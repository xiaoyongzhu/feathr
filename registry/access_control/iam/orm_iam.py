import json
import os
import string
import time
import datetime
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from itertools import groupby

from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, StaticPool, distinct
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4
import hashlib
import jwt
import smtplib

from iam.interface import IAM
from iam.models import RegisterUser, AddOrganization, OrganizationUserEdit, UserRole, UserStatus, CaptchaType, \
    CaptchaStatus, SsoUserPlatform, EditProjectUsers

from iam.exceptions import LoginError, ConflictError, EntityNotFoundError, AccessDeniedError
from iam import okta

from iam.config import FEATHR_SANDBOX, DEFAULT_PASSWORD, SECRET_KEY, ALGORITHM

Base = declarative_base()

"""The ORM implementation of IAM function
Management of organization and user-related, login, registration, reset password
implemented using ORM, requiring configuration of ORM driver and email sender.
"""


# define entities
class OrganizationEntity(Base):
    __tablename__ = 'organizations'

    id = Column('id', String, primary_key=True)
    name = Column('name', String, nullable=False)
    remark = Column('remark', String, nullable=True)
    status = Column('status', String, default='ACTIVE')
    create_time = Column('create_time', DateTime, default=datetime.datetime.utcnow)
    update_time = Column('update_time', DateTime, default=datetime.datetime.utcnow)


class UserEntity(Base):
    __tablename__ = "users"

    id = Column('id', String, primary_key=True)
    email = Column('email', String, nullable=False)
    password = Column('password', String)
    status = Column('status', String, default='ACTIVE')
    create_time = Column('create_time', DateTime, default=datetime.datetime.utcnow)
    update_time = Column('update_time', DateTime, default=datetime.datetime.utcnow)


class SsoUserEntity(Base):
    __tablename__ = "sso_users"

    id = Column('id', String, primary_key=True)
    sso_user_id = Column('sso_user_id', String, nullable=False)
    sso_email = Column('sso_email', String, nullable=False)
    user_id = Column('user_id', String, nullable=False)
    platform = Column('platform', String, nullable=False)
    access_token = Column('access_token', String, nullable=False)
    source_str = Column('source_str', String, nullable=False)
    create_time = Column('create_time', DateTime, default=datetime.datetime.utcnow)
    update_time = Column('update_time', DateTime, default=datetime.datetime.utcnow)


class CaptchaEntity(Base):
    __tablename__ = "captcha"

    id = Column('id', String, primary_key=True)
    receiver = Column('receiver', String, nullable=False)
    type = Column('type', String, nullable=False)
    code = Column('code', String, nullable=False)
    status = Column('status', String, nullable=False)
    create_time = Column('create_time', DateTime, default=datetime.datetime.utcnow)


class OrganizationUserRelation(Base):
    """User and organization relationship table"""
    __tablename__ = "organization_user"

    id = Column('id', String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    role = Column('role', String, nullable=False)
    create_time = Column('create_time', DateTime, default=datetime.datetime.utcnow)

    organization = relationship("OrganizationEntity", back_populates="users")
    user = relationship("UserEntity", back_populates="organizations")


OrganizationEntity.users = relationship("OrganizationUserRelation", back_populates="organization")
UserEntity.organizations = relationship("OrganizationUserRelation", back_populates="user")


class ProjectUserRelation(Base):
    """User and Project relationship table"""
    __tablename__ = "project_user"

    id = Column('id', String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    project_id = Column('project_id', String(50), nullable=False)
    role = Column('role', String(50), nullable=False)
    create_time = Column('create_time', DateTime, default=datetime.datetime.utcnow)


class OrmIAM(IAM):
    def __init__(self):
        if os.environ.get(FEATHR_SANDBOX):
            self.engine = create_engine('sqlite:////tmp/feathr_iam.sqlite?check_same_thread=False',
                                        connect_args={'check_same_thread': False},
                                        poolclass=StaticPool)
        else:
            conn_str = os.environ['RBAC_CONNECTION_STR']
            if "Server=" not in conn_str:
                raise RuntimeError("`RBAC_CONNECTION_STR` is not in ADO connection string format")
            params = self.__parse_conn_str(conn_str)
            self.engine = create_engine(
                f'mssql+pymssql://{params["user"]}:{params["password"]}@{params["host"]}/{params["database"]}')
        self.Session = sessionmaker(bind=self.engine)
        self.smtp_sender = os.environ['EMAIL_SENDER_ADDRESS']

        # If SandBox, need init test data
        if os.environ.get(FEATHR_SANDBOX):
            self.__create_tables()
            self.__init_sandbox_data()

    def add_organization(self, add_organization: AddOrganization):
        """After adding the organization successfully, an administrator will be generated."""
        session = self.Session()
        # check if organization already exist
        organization = session.query(OrganizationEntity).filter_by(name=add_organization.name).first()
        if organization is not None:
            raise ConflictError("Organization(" + organization.name + ") already exists!")

        # check if email already exist
        self.__check_email_exists(session, add_organization.email)

        # save organization
        new_organization = OrganizationEntity(id=self.__get_uuid(), name=add_organization.name,
                                              remark=add_organization.remark)
        session.add(new_organization)
        new_organization_id = new_organization.id

        # save administrator and relationship
        new_user = UserEntity(id=self.__get_uuid(), email=add_organization.email,
                              password=self.__digest_password(DEFAULT_PASSWORD))
        session.add(new_user)
        session.add(
            OrganizationUserRelation(id=self.__get_uuid(), organization_id=new_organization.id, user_id=new_user.id,
                                     role=UserRole.ADMIN.value))

        session.commit()
        session.close()
        return new_organization_id

    def delete_organization(self, organization_id: str, operator_id: str):
        """Logical deletion"""
        session = self.Session()
        self.__check_organization_manager_access(session, organization_id, operator_id)

        organization = session.query(OrganizationEntity).get(organization_id)
        organization.status = 'DELETED'
        session.commit()
        session.close()
        return 1

    def send_captcha(self, email: str, type: CaptchaType):
        session = self.Session()

        # If it is registration, then an email that has not been registered
        if type == CaptchaType.REGISTER:
            # check if user already exist
            self.__check_email_exists(session, email)

        # It is necessary to wait until the verification code expires
        latest_entity = session.query(CaptchaEntity) \
            .filter(CaptchaEntity.receiver == email,
                    CaptchaEntity.type == type.value,
                    CaptchaEntity.status == CaptchaStatus.SEND.value) \
            .order_by(CaptchaEntity.create_time.desc()).first()
        if latest_entity is not None:
            if (datetime.datetime.utcnow() - latest_entity.create_time) < datetime.timedelta(minutes=1):
                raise AccessDeniedError("Need previous verification code expires")
        code = self.__generate_code()

        new_captcha = CaptchaEntity(id=self.__get_uuid(), receiver=email, type=type.value,
                                    code=code, status=CaptchaStatus.SEND.value)

        smtp_obj = self.get_email_sender()
        msg = MIMEMultipart()
        msg['From'] = self.smtp_sender
        msg['To'] = email
        msg['Subject'] = type.value
        body = f'Type: {type.value}, Verification Code: {code}'
        # Add content
        msg.attach(MIMEText(body, 'plain'))
        smtp_obj.sendmail(self.smtp_sender, [email], msg.as_string())
        smtp_obj.close()

        session.add(new_captcha)
        session.commit()
        session.close()

    def signup(self, register_user: RegisterUser):
        session = self.Session()
        # check if user already exist
        self.__check_email_exists(session, register_user.email)

        # Check if the captcha is right
        self.__verify_code(session, register_user.email, CaptchaType.REGISTER, register_user.captcha)

        new_user = UserEntity(id=self.__get_uuid(), email=register_user.email,
                              password=self.__digest_password(register_user.password))
        session.add(new_user)
        session.commit()
        user_id = new_user.id
        session.close()
        return user_id

    def okta_login(self, code: str, redirect_uri: str):
        """If already have a Feathr user, return successful login. If not, generate a new user"""
        session = self.Session()
        access_token = okta.get_token_by_code(code, redirect_uri)
        okta_user_info_json = okta.get_user_info(access_token)
        okta_user = session.query(SsoUserEntity) \
            .filter(SsoUserEntity.sso_user_id == okta_user_info_json['sub'],
                    SsoUserEntity.platform == SsoUserPlatform.OKTA.value) \
            .order_by(SsoUserEntity.create_time.desc()).first()
        if okta_user is None:
            # Save Feathr user
            self.__check_email_exists(session, okta_user_info_json['email'])
            user = UserEntity(id=self.__get_uuid(), email=okta_user_info_json['email'])
            session.add(user)
            okta_user = SsoUserEntity(id=self.__get_uuid(), user_id=user.id, sso_user_id=okta_user_info_json['sub'],
                                      platform=SsoUserPlatform.OKTA.value, sso_email=okta_user_info_json['email'],
                                      access_token=access_token, source_str=json.dumps(okta_user_info_json))
            session.add(okta_user)
        else:
            okta_user.access_token = access_token
            okta_user.sso_email = okta_user_info_json['email']
            okta_user.update_time = datetime.datetime.utcnow()

        # Search user and return
        select_user = session.query(UserEntity).get(okta_user.user_id)
        response_data = self.__login_result(session, select_user)
        session.commit()
        session.close()
        return response_data

    def login(self, email: str, password: str):
        session = self.Session()
        user = session.query(UserEntity).filter_by(email=email).first()
        if user is None:
            raise LoginError('Incorrect username or password.')

        if user.status != UserStatus.ACTIVE.value:
            raise LoginError('User is not available.')

        # Check password
        if user.password != self.__digest_password(password):
            raise LoginError('Incorrect username or password.')

        response_data = self.__login_result(session, user)
        session.close()
        return response_data

    def reset_password(self, email: str, new_password: str, captcha: str):
        session = self.Session()
        self.__verify_code(session, email, CaptchaType.UPDATE_PASSWORD, captcha)
        user = self.__get_existing_user(session, email)
        user.password = self.__digest_password(new_password)
        session.commit()
        session.close()

    def invite_user(self, organization_id: str, email: str, role: UserRole, operator_id: str):
        session = self.Session()

        user = self.__get_existing_user(session, email)

        # Check whether have access
        self.__check_organization_manager_access(session, organization_id, operator_id)
        # Check if this user is already belonging to this organization
        organization_users = session.query(OrganizationUserRelation) \
            .filter_by(organization_id=organization_id, user_id=user.id).first()
        if organization_users is not None:
            return False

        session.add(OrganizationUserRelation(id=self.__get_uuid(), organization_id=organization_id,
                                             user_id=user.id, role=role.value))
        session.commit()
        session.close()
        return True

    def edit_organization_user(self, organization_id: str, user_id: str, edit_user: OrganizationUserEdit,
                               operator_id: str):
        session = self.Session()

        # Check whether have access
        self.__check_organization_manager_access(session, organization_id, operator_id)

        organization_user_relation = session.query(OrganizationUserRelation) \
            .filter(OrganizationUserRelation.organization_id == organization_id,
                    OrganizationUserRelation.user_id == user_id).first()
        if organization_user_relation is None:
            raise EntityNotFoundError('Cannot find this user from organization')
        organization_user_relation.role = edit_user.role.value
        session.commit()
        session.close()
        return

    def remove_organization_user(self, organization_id: str, user_id: str, operator_id: str):
        """Only Manager can operate records"""
        session = self.Session()

        # Check whether have access
        self.__check_organization_manager_access(session, organization_id, operator_id)

        session.query(OrganizationUserRelation) \
            .filter(OrganizationUserRelation.organization_id == organization_id,
                    OrganizationUserRelation.user_id == user_id) \
            .delete(synchronize_session='fetch')
        session.commit()
        session.close()
        return

    def get_users(self, organization_id: str, keyword: str, operator_id: str, page_size: int, page_no: int):
        """User search with support for keyword and pagination"""
        session = self.Session()

        self.__check_organization_manager_access(session, organization_id, operator_id)

        users = []
        filters = [OrganizationUserRelation.organization_id == organization_id]
        if keyword is not None and keyword != '':
            filters.append(UserEntity.email.like('%' + keyword + '%'))
        offset = (page_no - 1) * page_size
        result = session.query(OrganizationUserRelation, UserEntity) \
            .join(UserEntity) \
            .filter(*filters).order_by(UserEntity.create_time.desc()).offset(offset).limit(page_size).all()
        for organizationUserRelation, userEntity in result:
            users.append({'id': userEntity.id,
                          'email': userEntity.email,
                          'role': organizationUserRelation.role,
                          'create_time': userEntity.create_time,
                          'update_time': userEntity.update_time})
        total = session.query(OrganizationUserRelation, UserEntity) \
            .join(UserEntity).filter(*filters).count()
        session.close()
        # return {'data': users, 'total': total}
        return users

    def get_user_by_email(self, email: str):
        session = self.Session()
        user = session.query(UserEntity).filter_by(email=email).first()
        exist_user = {'id': user.id, 'email': user.email}
        session.close()
        return exist_user

    def get_email_sender(self):
        # init email server
        smtp_obj = smtplib.SMTP(os.environ['EMAIL_SENDER_HOST'], os.environ['EMAIL_SENDER_PORT'])
        smtp_obj.starttls()
        # Login to email server
        smtp_obj.login(os.environ['EMAIL_SENDER_ADDRESS'], os.environ['EMAIL_SENDER_PASSWORD'])
        return smtp_obj

    def supply_projects_users(self, organization_id: str, projects: list[dict]):
        """Supply projects managers and users"""
        if projects is None or len(projects) == 0:
            return
        session = self.Session()
        project_ids = list(map(lambda obj: obj['entity_id'], projects))
        relations = session.query(ProjectUserRelation) \
            .filter(ProjectUserRelation.organization_id == organization_id,
                    ProjectUserRelation.project_id.in_(project_ids)).all()
        relation_group = groupby(relations, key=lambda x: x['project_id'])
        for project in projects:
            relations = relation_group[project['entity_id']]
            project['manages'] = []
            project['users'] = []
            for relation in relations:
                if relation.role == UserRole.ADMIN:
                    project['manages'].append({'id': relation.user_id, 'name': ''})
                elif relation.role == UserRole.USER:
                    project['users'].append({'id': relation.user_id, 'name': ''})

    def edit_project_users(self, organization_id: str, project_id: str,
                           edit_project_user: EditProjectUsers, user_id: str):
        """Edit project users, will check authority first
        will remove all relations and init new relations"""
        session = self.Session()

        self.__check_organization_user_access(session, organization_id, user_id)
        self.__check_project_manager(session, project_id, user_id)

        session.query(ProjectUserRelation) \
            .filter(ProjectUserRelation.organization_id == organization_id,
                    ProjectUserRelation.project_id == project_id) \
            .delete(synchronize_session='fetch')

        for manager in edit_project_user.managers:
            session.add(ProjectUserRelation(id=self.__get_uuid(), organization_id=organization_id,
                                            user_id=manager, project_id=project_id,
                                            role=UserRole.ADMIN.value))

        for user in edit_project_user.users:
            session.add(ProjectUserRelation(id=self.__get_uuid(), organization_id=organization_id,
                                            user_id=user, project_id=project_id,
                                            role=UserRole.USER.value))

        session.commit()
        session.close()
        return True

    def get_user_projects(self, organization_id: str, user_id: str):
        session = self.Session()
        user_role = self.__get_user_role(session, organization_id, user_id)
        if user_role == UserRole.ADMIN.value:
            project_ids = session.query(distinct(ProjectUserRelation.project_id)) \
                .filter_by(organization_id=organization_id).all()
        else:
            """Get all project ids which user has authority"""
            project_ids = session.query(distinct(ProjectUserRelation.project_id)) \
                .filter_by(organization_id=organization_id,
                           user_id=user_id).all()
        return project_ids

    def add_project_user(self, organization_id: str, user_id: str, project_id: str, role: UserRole):
        """Add user to the project"""
        session = self.Session()
        # Check if user exists
        self.__check_organization_user_access(session, organization_id, user_id)

        # If the relation already exists, will return directly
        exist_relation = session.query(ProjectUserRelation) \
            .filter_by(organization_id=organization_id,
                       user_id=user_id,
                       project_id=project_id).first()
        if exist_relation is not None:
            return

        session.add(ProjectUserRelation(id=self.__get_uuid(),
                                        organization_id=organization_id,
                                        user_id=user_id,
                                        project_id=project_id,
                                        role=role))

        session.commit()
        session.close()

    def __login_result(self, session, user: UserEntity):
        """Get organizations, retrieving the result by joining the organization table and the organization_user table
        Now, a user only returns one organization"""
        result = session.query(OrganizationUserRelation, OrganizationEntity) \
            .join(OrganizationEntity).filter(OrganizationUserRelation.user_id == user.id).all()
        organizations = []
        for organizationUserRelation, organizationEntity in result:
            organizations.append({'organization_id': organizationUserRelation.organization_id,
                                  'organization_name': organizationEntity.name,
                                  'role': organizationUserRelation.role})
        return {
            'organizations': organizations,
            'name': user.email,
            'token': jwt.encode({
                'sub': user.id,
                'iat': int(time.time()),
                'name': user.email
            }, SECRET_KEY, algorithm=ALGORITHM)
        }

    def __verify_code(self, session, receiver: str, type: CaptchaType, captcha: str):
        """Check whether the captcha is correct"""
        latest_captcha = session.query(CaptchaEntity) \
            .filter(CaptchaEntity.receiver == receiver,
                    CaptchaEntity.type == type.value,
                    CaptchaEntity.status == CaptchaStatus.SEND.value) \
            .order_by(CaptchaEntity.create_time.desc()).first()
        if latest_captcha is None or latest_captcha.code != captcha:
            raise AccessDeniedError('Incorrect Captcha!')
        else:
            latest_captcha.status = CaptchaStatus.VERIFIED.value

    def __check_organization_manager_access(self, session, organization_id: str, operator_id: str):
        """Check if the user has the authority to manager on this organization,
        and if the user or organization does not exist, it will also return Access Denied """

        relation = session.query(OrganizationUserRelation) \
            .filter(OrganizationUserRelation.organization_id == organization_id,
                    OrganizationUserRelation.user_id == operator_id).first()
        if relation is None or relation.role != UserRole.ADMIN.value:
            raise AccessDeniedError('Access Denied!')

    def check_organization_user_access(self, organization_id: str, operator_id: str):
        session = self.Session()
        self.check_organization_user_access(organization_id, operator_id)
        session.commit()
        session.close()

    def __check_organization_user_access(self, session, organization_id: str, operator_id: str):
        """Check if the user has the authority to operate on this organization,
        and if the user or organization does not exist, it will also return Access Denied """

        relation = session.query(OrganizationUserRelation) \
            .filter(OrganizationUserRelation.organization_id == organization_id,
                    OrganizationUserRelation.user_id == operator_id).first()
        if relation is None:
            raise AccessDeniedError('Access Denied!')

    def __check_project_manager(self, session, organization_id: str, project_id: str, user_id: str):
        """Organization Manager should not call this function,
        will check if user has this project and is a project manager"""
        relation = session.query(ProjectUserRelation) \
            .filter_by(organization_id=organization_id,
                       project_id=project_id,
                       user_id=user_id).first()
        if relation is None or relation.role == UserRole.USER:
            raise AccessDeniedError('Access Denied!')

    def __get_user_role(self, session, organization_id: str, user_Id: str):
        relation = session.query(OrganizationUserRelation) \
            .filter(OrganizationUserRelation.organization_id == organization_id,
                    OrganizationUserRelation.user_id == user_Id).first()
        if relation is None:
            return UserRole.USER.value
        else:
            return relation.role

    def __check_email_exists(self, session, email: str):
        """ if email already exists, will raise a error """
        user = session.query(UserEntity).filter_by(email=email).first()
        if user is not None:
            raise ConflictError('User(' + email + ') already exists!')

    def __get_existing_user(self, session, email: str):
        user = session.query(UserEntity).filter_by(email=email).first()
        if user is None:
            raise EntityNotFoundError('User(' + email + ') not found!')
        return user

    def __digest_password(self, password: str):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def __generate_code(self, ):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return code

    def __create_tables(self):
        Base.metadata.create_all(self.engine)

    def __init_sandbox_data(self):
        """Init test data"""
        session = self.Session()
        organization = session.query(OrganizationEntity).filter_by(name='Feathr').first()
        if organization is None:
            self.add_organization(AddOrganization(name='Feathr', email='feathr@163.com', remark='Sandbox test data'))
        session.commit()
        session.close()

    def __get_uuid(self):
        return str(uuid4())

    def __parse_conn_str(self, s: str) -> dict:
        """
        TODO: Not a sound and safe implementation, but useful enough in this case
        as the connection string is provided by users themselves.
        example: Server=Port:IP;Initial Catalog=****;User ID=***;Password=***
        """
        parts = dict([p.strip().split("=", 1)
                      for p in s.split(";") if len(p.strip()) > 0])
        server = parts["Server"].split(":")[1].split(",")[0]
        return {
            "host": server,
            "database": parts["Initial Catalog"],
            "user": parts["User ID"],
            "password": parts["Password"],
        }
