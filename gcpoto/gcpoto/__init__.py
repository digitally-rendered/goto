"""GCPoto: A boto-like library and CLI for Google Cloud Platform."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from gcpoto.exceptions import (
    APIError,
    AuthenticationError,
    GCPotoError,
    PermissionDeniedError,
    QuotaExceededError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    ValidationError,
)

__all__ = [
    "APIError",
    "AuthenticationError",
    "GCPotoError",
    "PermissionDeniedError",
    "QuotaExceededError",
    "ResourceAlreadyExistsError",
    "ResourceNotFoundError",
    "ServiceUnavailableError",
    "ValidationError",
]
