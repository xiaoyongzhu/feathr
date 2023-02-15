import json
import os
import string
import time
import datetime
import random
from email.mime.text import MIMEText

from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4
import hashlib
import jwt
import smtplib

from iam.interface import IAM
from iam.models import RegisterUser, AddOrganization

from iam.exceptions import LoginError, ConflictError, EntityNotFoundError, AccessDeniedError
from iam.models import UserRole, UserStatus

from iam.models import CaptchaType
from rbac import config

from iam.models import CaptchaStatus
from iam import okta

from iam.models import SsoUserPlatform
from iam.okta import OkataUserInfo

Base = declarative_base()

secret_key = 'feathr123#@!'
default_password = 'feathr123#@!'
ALGORITHM = 'HS256'

"""The ORM implementation of IAM function"""


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


def parse_conn_str(s: str) -> dict:
    """
    TODO: Not a sound and safe implementation, but useful enough in this case
    as the connection string is provided by users themselves.
    """
    parts = dict([p.strip().split("=", 1)
                  for p in s.split(";") if len(p.strip()) > 0])
    server = parts["Server"].split(":")[1].split(",")[0]
    return {
        "host": server,
        "database": parts["Initial Catalog"],
        "user": parts["User ID"],
        "password": parts["Password"],
        # "charset": "utf-8",   ## For unknown reason this causes connection failure
    }


class OrmIAM(IAM):
    def __init__(self):
        conn_str = os.environ["RBAC_CONNECTION_STR"]
        if "Server=" not in conn_str:
            raise RuntimeError("`RBAC_CONNECTION_STR` is not in ADO connection string format")
        params = parse_conn_str(conn_str)
        self.engine = create_engine(
            f'mssql+pymssql://{params["user"]}:{params["password"]}@{params["host"]}/{params["database"]}')
        self.Session = sessionmaker(bind=self.engine)

        # init email server
        smtp_obj = smtplib.SMTP()
        # 连接到服务器
        smtp_obj.connect(config.EMAIL_SENDER_HOST, config.EMAIL_SENDER_PORT)
        # 登录到服务器
        smtp_obj.login(config.EMAIL_SENDER_ADDRESS, config.EMAIL_SENDER_PASSWORD)
        self.smtp_obj = smtp_obj
        self.smtp_sender = config.EMAIL_SENDER_ADDRESS

    def create_tables(self):
        Base.metadata.create_all(self.engine)

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
        new_organization = OrganizationEntity(id=uuid4(), name=add_organization.name, remark=add_organization.remark)
        session.add(new_organization)
        new_organization_id = new_organization.id

        # save administrator and relationship
        new_user = UserEntity(id=uuid4(), email=add_organization.email,
                              password=self.__digest_password(default_password))
        session.add(new_user)
        session.add(OrganizationUserRelation(id=uuid4(), organization_id=new_organization.id, user_id=new_user.id,
                                             role=UserRole.ADMIN.value))

        session.commit()
        session.close()
        return new_organization_id

    def delete_organization(self, organization_id: str, operator_id: str):
        """Logical deletion"""
        session = self.Session()
        self.__check_organization_access(session, organization_id, operator_id)

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

        new_captcha = CaptchaEntity(id=uuid4(), receiver=email, type=type.value,
                                    code=code, status=CaptchaStatus.SEND.value)

        # Send email
        self.smtp_obj.sendmail(
            self.smtp_sender, email,
            MIMEText(f'Type: {type.value}, Verification Code: {code}', 'plain', 'utf-8').as_string())

        session.add(new_captcha)
        session.commit()
        session.close()

    def signup(self, register_user: RegisterUser):
        session = self.Session()
        # check if user already exist
        self.__check_email_exists(session, register_user.email)

        # Check if the captcha is right
        self.__verify_code(session, register_user.email, CaptchaType.REGISTER, register_user.captcha)

        new_user = UserEntity(id=uuid4(), email=register_user.email,
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
            user = UserEntity(id=uuid4(), email=okta_user_info_json['email'])
            session.add(user)
            okta_user = SsoUserEntity(id=uuid4(), user_id=user.id, sso_user_id=okta_user_info_json['sub'],
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
        self.__check_organization_access(session, organization_id, operator_id)
        # Check if this user is already belonging to this organization
        organization_users = session.query(OrganizationUserRelation) \
            .filter_by(organization_id=organization_id, user_id=user.id).first()
        if organization_users is not None:
            return 0

        session.add(OrganizationUserRelation(id=uuid4(), organization_id=organization_id,
                                             user_id=user.id, role=role.value))
        session.commit()
        session.close()
        return 1

    def remove_organization_user(self, organization_id: str, user_id: str, operator_id: str):
        """Only Manager can operate records"""
        session = self.Session()

        # Check whether have access
        self.__check_organization_access(session, organization_id, operator_id)

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

        self.__check_organization_access(session, organization_id, operator_id)

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
            }, secret_key, algorithm=ALGORITHM)
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

    def __check_organization_access(self, session, organization_id: str, operator_id: str):
        """Check if the user has the authority to operate on this organization,
        and if the user or organization does not exist, it will also return Access Denied """

        relation = session.query(OrganizationUserRelation) \
            .filter(OrganizationUserRelation.organization_id == organization_id,
                    OrganizationUserRelation.user_id == operator_id).first()
        if relation is None or relation.role != UserRole.ADMIN.value:
            raise AccessDeniedError('Access Denied!')

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
