from enum import Enum

from pydantic import BaseModel, constr

"""Definition of IAM page request model, response model and public enumeration"""


# define enums
class UserRole(Enum):
    ADMIN = 'ADMIN'
    USER = 'USER'


class UserStatus(Enum):
    ACTIVE = 'ACTIVE'


class CaptchaType(Enum):
    REGISTER = 'REGISTER'
    UPDATE_PASSWORD = 'UPDATE_PASSWORD'


class CaptchaStatus(Enum):
    SEND = 'SEND'
    VERIFIED = 'VERIFIED'


class AddOrganization(BaseModel):
    name: str
    email: str
    remark: str


class RegisterUser(BaseModel):
    email: constr(min_length=5)
    password: constr(min_length=5)
    captcha: constr(min_length=4)


class OrganizationUserEdit(BaseModel):
    role: UserRole


class UserLogin(BaseModel):
    email: constr(min_length=5)
    password: constr(min_length=5)


class OktaLogin(BaseModel):
    code: constr(min_length=5)
    redirect_uri: constr(min_length=5)


class UserResetPassword(BaseModel):
    email: constr(min_length=5)
    new_password: constr(min_length=5)
    captcha: constr(min_length=4)


class SsoUserPlatform(Enum):
    OKTA = 'OKTA'
