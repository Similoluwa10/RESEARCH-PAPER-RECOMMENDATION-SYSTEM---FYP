"""
Custom Exceptions

Application-specific exception classes.
"""

from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found exception."""
    
    def __init__(self, resource: str, id: Any):
        super().__init__(
            message=f"{resource} with id '{id}' not found",
            status_code=404,
        )


class UnauthorizedException(AppException):
    """Unauthorized access exception."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message=message, status_code=401)


class ValidationException(AppException):
    """Validation error exception."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            details=details,
        )


class DuplicateException(AppException):
    """Duplicate resource exception."""
    
    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} with {field} '{value}' already exists",
            status_code=409,
        )
