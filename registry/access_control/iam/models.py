from datetime import datetime
from pydantic import BaseModel, constr


class AddOrganization(BaseModel):
    name: str
    email: str
    remark: str
    email: str


class RegisterUser(BaseModel):
    email: constr(min_length=5)
    password: constr(min_length=5)
    captcha: constr(min_length=4)


class UserLogin(BaseModel):
    email: constr(min_length=5)
    password: constr(min_length=5)


class Organization:
    def __init__(self,
                 id: str,
                 name: str,
                 status: str,
                 create_time: datetime,
                 update_time: datetime):
        self.id = id
        self.name = name
        self.status = status
        self.create_time: create_time
        self.update_time: update_time


class User:
    def __init__(self,
                 id: str,
                 email: str,
                 password: str,
                 phone: str,
                 type: str,
                 status: str,
                 create_time: datetime,
                 update_time: datetime):
        self.id = id
        self.email = email
        self.password = password
        self.phone = phone
        self.type = type
        self.status = status
        self.create_time = create_time
        self.update_time = update_time


class OrganizationUser:
    def __init__(self,
                 id: str,
                 organization_id: str,
                 user_id: str):
        self.id = id
        self.organization_id = organization_id
        self.user_id = user_id
