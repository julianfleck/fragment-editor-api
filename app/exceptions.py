class APIRequestError(Exception):
    """Custom exception for API request errors"""

    def __init__(self, message: str, status: int = 500, details: str = None):
        self.message = message
        self.status = status
        self.details = details
        super().__init__(self.message)


class ValidationError(Exception):
    """Custom exception for validation errors"""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""

    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        self.status = 401
        super().__init__(self.message)
