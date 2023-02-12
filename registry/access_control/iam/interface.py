from abc import ABC, abstractmethod
from iam.models import AddOrganization, RegisterUser

from iam.models import UserRole

"""The interface definition of IAM mainly includes interfaces related to organizations,
interfaces related to users, and interfaces related to operations between users and organizations"""


class IAM(ABC):
    @abstractmethod
    def add_organization(self, organization: AddOrganization):
        """Add a organization"""
        pass

    @abstractmethod
    def delete_organization(self, organization_id: str, operator_id: str):
        """Delete a organization"""
        pass

    @abstractmethod
    def signup(self, register_user: RegisterUser):
        """User signup"""
        pass

    @abstractmethod
    def login(self, email: str, password: str):
        """User login"""
        pass

    @abstractmethod
    def invite_user(self, organization_id: str, email: str, role: UserRole, operator_id: str):
        """Invite user"""
        pass

    @abstractmethod
    def remove_organization_user(self, organization_id: str, user_id: str, operator_id: str):
        """Remove User"""
        pass

    @abstractmethod
    def get_users(self, organization_id: str, keyword: str, operator_id: str, page_size: int, page_no: int):
        """Search users from organization"""
        pass

    @abstractmethod
    def get_user_by_email(self, email: str):
        """Search user through email"""
        pass
