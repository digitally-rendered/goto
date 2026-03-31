"""Custom exception hierarchy for the gcpoto package."""


class GCPotoError(Exception):
    """Base exception for all gcpoto errors."""


class AuthenticationError(GCPotoError):
    """Raised when authentication or credential validation fails."""


class ResourceNotFoundError(GCPotoError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource_type: str, resource_id: str, message: str = ""):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(
            message or f"{resource_type} '{resource_id}' not found"
        )


class ResourceAlreadyExistsError(GCPotoError):
    """Raised when attempting to create a resource that already exists."""


class ValidationError(GCPotoError):
    """Raised when input validation fails."""


class APIError(GCPotoError):
    """Raised when a GCP API call fails."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error {status_code}: {message}")


class QuotaExceededError(APIError):
    """Raised when a quota or rate limit is exceeded."""


class PermissionDeniedError(APIError):
    """Raised when the caller lacks required IAM permissions."""


class ServiceUnavailableError(APIError):
    """Raised when a GCP service is temporarily unavailable."""
