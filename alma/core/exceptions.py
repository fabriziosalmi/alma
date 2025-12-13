class AlmaError(Exception):
    """Base class for ALMA exceptions."""
    pass

class MissingResourceError(AlmaError):
    """Raised when a required resource (like a template) is missing."""
    def __init__(self, resource_type: str, resource_name: str, message: str = None):
        self.resource_type = resource_type
        self.resource_name = resource_name
        super().__init__(message or f"Missing {resource_type}: {resource_name}")

class AuthenticationError(AlmaError):
    """Raised when authentication fails."""
    pass
