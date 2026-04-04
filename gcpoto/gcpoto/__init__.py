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
from gcpoto.session import Session


def client(service_name, project_id=None, credentials_file=None, **kwargs):
    """Convenience function to create a service client.

    Creates a new :class:`Session` and returns a client for the requested
    service.  This is the simplest way to get started::

        storage = gcpoto.client("storage", project_id="my-project")

    Args:
        service_name: The name of the GCP service (e.g. ``"storage"``).
        project_id: The GCP project ID.
        credentials_file: Optional path to a service account credentials file.
        **kwargs: Additional keyword arguments forwarded to :class:`Session`.

    Returns:
        An instance of the requested service class.
    """
    session = Session(
        project_id=project_id,
        credentials_file=credentials_file,
        **kwargs,
    )
    return session.client(service_name)


__all__ = [
    "APIError",
    "AuthenticationError",
    "GCPotoError",
    "PermissionDeniedError",
    "QuotaExceededError",
    "ResourceAlreadyExistsError",
    "ResourceNotFoundError",
    "ServiceUnavailableError",
    "Session",
    "ValidationError",
    "client",
]
