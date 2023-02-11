"""

"""
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4
import hashlib
import jwt

from iam.interface import IAM
from iam.models import RegisterUser, AddOrganization

Base = declarative_base()

database_uri = 'mssql+pymssql://wxl:wxlAliyunDbAdmin@123.57.204.250/feathr'
secret_key = 'feathr123#@!'
default_password = 'feathr123#@!'
ALGORITHM = 'HS256'


# define errors
class ConflictError(Exception):
    """Entities already exist"""
    pass


class EntityNotFoundError(Exception):
    """Cannot find this Entity"""
    pass


class LoginError(Exception):
    """Exception Occurring During User Login"""
    pass


class AccessDeniedError(Exception):
    """Exception Occurring During User Cannot access"""
    pass


# define entities
class OrganizationEntity(Base):
    __tablename__ = 'organizations'

    id = Column('id', String, primary_key=True)
    name = Column('name', String, nullable=False)
    remark = Column('remark', String, nullable=True)
    status = Column('status', String, default='ACTIVE')
    create_time = Column('create_time', DateTime, default=datetime.utcnow)
    update_time = Column('update_time', DateTime, default=datetime.utcnow)


class UserEntity(Base):
    __tablename__ = "users"

    id = Column('id', String, primary_key=True)
    email = Column('email', String, nullable=False)
    password = Column('password', String, nullable=False)
    status = Column('status', String, default='ACTIVE')
    create_time = Column('create_time', DateTime, default=datetime.utcnow)
    update_time = Column('update_time', DateTime, default=datetime.utcnow)


class OrganizationUserRelation(Base):
    """User and organization relationship table"""
    __tablename__ = "organization_user"

    id = Column('id', String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    role = Column('role', String, nullable=False)
    create_time = Column('create_time', DateTime, default=datetime.utcnow)

    organization = relationship("OrganizationEntity", back_populates="users")
    user = relationship("UserEntity", back_populates="organizations")


OrganizationEntity.users = relationship("OrganizationUserRelation", back_populates="organization")
UserEntity.organizations = relationship("OrganizationUserRelation", back_populates="user")


class OrmIAM(IAM):
    def __init__(self):
        self.engine = create_engine(database_uri)
        self.Session = sessionmaker(bind=self.engine)

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

        # save administrator and relationship
        new_user = UserEntity(id=uuid4(), email=add_organization.email,
                              password=self.__digest_password(default_password))
        session.add(new_user)
        session.add(OrganizationUserRelation(id=uuid4(), organization_id=new_organization.id, user_id=new_user.id,
                                             role='ADMINISTRATOR'))

        session.commit()
        session.close()
        return new_organization.id

    def delete_organization(self, id: str):
        """Logical deletion"""
        session = self.Session()
        organization = session.query(OrganizationEntity).get(id)
        if organization is None:
            return 0
        organization.status = 'DELETED'
        session.commit()
        session.close()
        return 1

    def signup(self, register_user: RegisterUser):
        session = self.Session()
        # check if user already exist
        user = session.query(UserEntity).filter_by(email=register_user.email).first()
        if user is not None:
            raise ConflictError('email already exists!')

        new_user = UserEntity(id=uuid4(), email=register_user.email,
                              password=self.__digest_password(register_user.password))
        session.add(new_user)
        session.commit()
        user_id = new_user.id
        session.close()
        return user_id

    def login(self, email: str, password: str):
        session = self.Session()
        user = session.query(UserEntity).filter_by(email=email).first()
        if user is None:
            raise LoginError('Incorrect username or password.')

        if user.status != 'ACTIVE':
            raise LoginError('User is not available.')

        # Check password
        if user.password != self.__digest_password(password):
            raise LoginError('Incorrect username or password.')

        # Get organizations, retrieving the result by joining the organization table and the organization_user table
        # Now, a user only returns one organization
        result = session.query(OrganizationUserRelation, OrganizationEntity) \
            .join(OrganizationEntity).filter(OrganizationUserRelation.user_id == user.id).all()
        organizations = []
        for organizationUserRelation, organizationEntity in result:
            organizations.append({'organization_id': organizationUserRelation.organization_id,
                                  'organization_name': organizationEntity.name,
                                  'role': organizationUserRelation.role})
        response_data = {
            'token': jwt.encode({
                'sub': user.id,
                'iat': int(time.time()),
                'name': email
            }, secret_key, algorithm=ALGORITHM)
        }
        session.close()
        return response_data

    def invite_user(self, organization_id: str, email: str, role: str, operator_id: str):
        session = self.Session()

        # Check whether have access
        relation = session.query(OrganizationUserRelation) \
            .filter(OrganizationUserRelation.organization_id == organization_id,
                    OrganizationUserRelation.user_id == operator_id).first()
        if relation is None or relation.role != 'MANAGER':
            raise AccessDeniedError('Access Denied!')
        user = self.__get_existing_user(session, email)
        # Check if this user is already belonging to this organization
        organization_users = session.query(OrganizationUserRelation) \
            .filter_by(organization_id=organization_id, user_id=user.id).first()
        if organization_users is not None:
            return 0

        session.add(OrganizationUserRelation(id=uuid4(), organization_id=organization_id,
                                             user_id=user.id, role=role))
        session.commit()
        session.close()
        return 1

    def remove_organization_user(self, organization_id: str, user_id: str, operator_id: str):
        """Only Manager can operate records"""
        session = self.Session()

        # Check whether have access
        relation = session.query(OrganizationUserRelation) \
            .filter(OrganizationUserRelation.organization_id == organization_id,
                    OrganizationUserRelation.user_id == operator_id).first()
        if relation is None or relation.role != 'MANAGER':
            raise AccessDeniedError('Access Denied!')

        session.query(OrganizationUserRelation) \
            .filter(OrganizationUserRelation.organization_id == organization_id,
                    OrganizationUserRelation.user_id == user_id) \
            .delete(synchronize_session='fetch')
        session.commit()
        session.close()
        return

    def get_users(self, organization_id: str, keyword: str, page_size: int = 20, page_no: int = 1):
        """User search with support for keyword and pagination"""
        session = self.Session()
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
        session.close()
        return users

    def get_user_by_email(self, email: str):
        session = self.Session()
        user = session.query(UserEntity).filter_by(email=email).first()
        exist_user = {'id': user.id, 'email': user.email}
        session.close()
        return exist_user

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

    def __check_organization_not_exists(self, organization_id: str):
        session = self.Session()
        organization = session.query(OrganizationEntity).filter_by(id=organization_id).first()
        session.close()
        if organization is None:
            raise EntityNotFoundError('Organization(' + organization_id + ') not found!')

    def __digest_password(self, password: str):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
