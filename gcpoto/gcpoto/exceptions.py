"""Custom exception hierarchy for the gcpoto package."""


class GCPotoError(Exception):
    """Base exception for all gcpoto errors."""


class APIError(GCPotoError):
    """Raised when a GCP API call fails."""

    def __init__(self, status_code: int = 0, message: str = ""):
        self.status_code = status_code
        self.message = message
        super().__init__(message or f"API error {status_code}: {message}")


class AuthenticationError(APIError):
    """Raised when authentication or credential validation fails (401)."""

    def __init__(self, message: str = ""):
        super().__init__(status_code=401, message=message)


class ResourceNotFoundError(APIError):
    """Raised when a requested resource does not exist (404)."""

    def __init__(self, resource_type: str = "", resource_id: str = "", message: str = ""):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(
            status_code=404,
            message=message or f"{resource_type} '{resource_id}' not found",
        )


class ResourceAlreadyExistsError(APIError):
    """Raised when attempting to create a resource that already exists (409)."""

    def __init__(self, message: str = ""):
        super().__init__(status_code=409, message=message)


class ValidationError(APIError):
    """Raised when input validation fails (400)."""

    def __init__(self, message: str = ""):
        super().__init__(status_code=400, message=message)


class QuotaExceededError(APIError):
    """Raised when a quota or rate limit is exceeded (429)."""


class PermissionDeniedError(APIError):
    """Raised when the caller lacks required IAM permissions (403)."""


class ServiceUnavailableError(APIError):
    """Raised when a GCP service is temporarily unavailable (503)."""
