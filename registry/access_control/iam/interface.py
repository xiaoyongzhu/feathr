from abc import ABC, abstractmethod
from iam.models import AddOrganization


class IAM(ABC):
    @abstractmethod
    def add_organization(self, organization: AddOrganization):
        """Add a organization"""
        pass

    @abstractmethod
    def delete_organization(self, id: str):
        """Delete a organization"""
        pass