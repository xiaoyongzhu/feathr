"""define errors"""


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
