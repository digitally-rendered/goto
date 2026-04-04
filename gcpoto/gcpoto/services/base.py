"""Base service class for GCP interactions."""

import logging
import random
import time
from typing import Dict, List, Any, Optional, Type, Generic, TypeVar

from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient import discovery
from googleapiclient.errors import HttpError

from gcpoto.exceptions import (
    APIError,
    AuthenticationError,
    PermissionDeniedError,
    QuotaExceededError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    ValidationError,
)
from gcpoto.models.base import GCPResource

logger = logging.getLogger(__name__)

# Type variable for generic resource types
T = TypeVar("T", bound=GCPResource)


class GCPService(Generic[T]):
    """Base service class for interacting with Google Cloud Platform resources."""

    # HTTP status codes that are safe to retry
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        project_id: str,
        service_name: str,
        version: str = "v1",
        credentials_file: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        resource_model: Type[T] = GCPResource,
        num_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize the GCP service.

        Args:
            project_id: The GCP project ID
            service_name: The name of the GCP service (e.g., 'compute', 'storage')
            version: The API version to use
            credentials_file: Path to service account credentials file
            scopes: Authentication scopes to use
            resource_model: The model class for this resource type
            num_retries: Maximum number of retry attempts for retryable errors
            retry_delay: Base delay in seconds for exponential backoff
        """
        self.project_id = project_id
        self.service_name = service_name
        self.version = version
        self.credentials_file = credentials_file
        self.scopes = scopes or [f"https://www.googleapis.com/auth/{service_name}"]
        self.resource_model = resource_model
        self.num_retries = num_retries
        self._max_retries = num_retries
        self.retry_delay = retry_delay
        self._retry_delay = retry_delay
        self.service = self._create_service()

    def _create_service(self):
        """Create and return an authenticated service client.

        Returns:
            An authenticated Google API client service
        """
        credentials = None
        if self.credentials_file:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file, scopes=self.scopes
            )

        return discovery.build(
            self.service_name, self.version, credentials=credentials
        )

    def _execute_with_retry(
        self,
        request: Any,
        resource_type: str = "",
        resource_id: str = "",
    ) -> Dict[str, Any]:
        """Execute an API request with retry logic and exponential backoff.

        Retries on transient errors (429, 500, 502, 503, 504) and connection
        errors.  Client errors (400, 401, 403, 404, 409) fail immediately and
        are mapped to the appropriate gcpoto exception.

        Args:
            request: A Google API client request object with an execute() method
            resource_type: Optional resource type for error context
            resource_id: Optional resource ID for error context

        Returns:
            The API response dictionary

        Raises:
            GCPotoError: A subclass corresponding to the HTTP status code
        """
        max_delay = 60.0
        for attempt in range(self.num_retries + 1):
            try:
                return request.execute()
            except HttpError as error:
                status = error.resp.status
                if (
                    status not in self.RETRYABLE_STATUS_CODES
                    or attempt == self.num_retries
                ):
                    self._handle_http_error(error, resource_type, resource_id)
                delay = min(
                    self.retry_delay * (2 ** attempt) + random.uniform(0, 1),
                    max_delay,
                )
                logger.warning(
                    "Retryable error %s on attempt %s/%s for %s %s, "
                    "retrying in %.1fs",
                    status,
                    attempt + 1,
                    self.num_retries,
                    resource_type,
                    resource_id,
                    delay,
                )
                time.sleep(delay)
            except (ConnectionError, OSError) as error:
                if attempt == self.num_retries:
                    raise APIError(0, str(error)) from error
                delay = min(
                    self.retry_delay * (2 ** attempt) + random.uniform(0, 1),
                    max_delay,
                )
                logger.warning(
                    "Connection error on attempt %s/%s: %s, retrying in %.1fs",
                    attempt + 1,
                    self.num_retries,
                    error,
                    delay,
                )
                time.sleep(delay)
        # Should not be reached, but satisfy type checkers
        raise APIError(0, "Unexpected retry loop exit")

    def _execute(
        self,
        request: Any,
        resource_type: str = "",
        resource_id: str = "",
    ) -> Dict[str, Any]:
        """Execute an API request with retry and error handling.

        All service methods should call this instead of request.execute()
        directly.  This is a convenience alias for ``_execute_with_retry``.

        Args:
            request: A Google API client request object with an execute() method
            resource_type: Optional resource type for error context
            resource_id: Optional resource ID for error context

        Returns:
            The API response dictionary

        Raises:
            GCPotoError: A subclass corresponding to the HTTP status code
        """
        return self._execute_with_retry(request, resource_type, resource_id)

    def _handle_http_error(
        self,
        error: HttpError,
        resource_type: str = "",
        resource_id: str = "",
    ) -> None:
        """Map an HttpError to the appropriate gcpoto exception and raise it.

        Args:
            error: The HttpError from googleapiclient
            resource_type: Optional resource type for error context
            resource_id: Optional resource ID for error context

        Raises:
            ValidationError: For 400 status
            AuthenticationError: For 401 status
            PermissionDeniedError: For 403 status
            ResourceNotFoundError: For 404 status
            ResourceAlreadyExistsError: For 409 status
            QuotaExceededError: For 429 status
            ServiceUnavailableError: For 503 status
            APIError: For all other status codes
        """
        status = error.resp.status
        message = str(error)

        if status == 400:
            raise ValidationError(message) from error
        elif status == 401:
            raise AuthenticationError(message) from error
        elif status == 403:
            raise PermissionDeniedError(status, message) from error
        elif status == 404:
            raise ResourceNotFoundError(
                resource_type=resource_type or "resource",
                resource_id=resource_id or "unknown",
                message=message,
            ) from error
        elif status == 409:
            raise ResourceAlreadyExistsError(message) from error
        elif status == 429:
            raise QuotaExceededError(status, message) from error
        elif status == 503:
            raise ServiceUnavailableError(status, message) from error
        else:
            raise APIError(status, message) from error

    def _wait_for_operation(
        self,
        operation: Dict[str, Any],
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        zone: Optional[str] = None,
        timeout: float = 300.0,
        poll_interval: float = 5.0,
    ) -> Dict[str, Any]:
        """Poll a long-running operation until it completes.

        Determines whether to use global, regional, or zonal operations based
        on the ``location`` and ``zone`` parameters.

        Args:
            operation: The operation dict returned by the initial API call
            project_id: GCP project ID (defaults to self.project_id)
            location: Region for regional operations (e.g. 'us-central1')
            zone: Zone for zonal operations (e.g. 'us-central1-a')
            timeout: Maximum time in seconds to wait for completion
            poll_interval: Time in seconds between polling requests

        Returns:
            The completed operation dict

        Raises:
            APIError: If the operation finishes with an error or times out
        """
        project_id = project_id or self.project_id
        op_name = operation.get("name", "")
        deadline = time.monotonic() + timeout

        logger.info("Waiting for operation %s (timeout=%ss)", op_name, timeout)

        while time.monotonic() < deadline:
            if operation.get("status") == "DONE" or operation.get("done"):
                if "error" in operation:
                    errors = operation["error"]
                    message = str(errors)
                    raise APIError(
                        0, "Operation %s failed: %s" % (op_name, message)
                    )
                return operation

            time.sleep(poll_interval)

            # Build the appropriate get request based on scope
            if zone:
                request = self.service.zoneOperations().get(
                    project=project_id, zone=zone, operation=op_name
                )
            elif location:
                request = self.service.regionOperations().get(
                    project=project_id, region=location, operation=op_name
                )
            else:
                request = self.service.globalOperations().get(
                    project=project_id, operation=op_name
                )

            operation = self._execute_with_retry(request)

        raise APIError(
            0, "Operation %s timed out after %ss" % (op_name, timeout)
        )

    def list_resources(self, **kwargs) -> List[T]:
        """List resources of this type in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of resource model instances
        """
        # This would be implemented by subclasses for specific resources
        raise NotImplementedError("Subclasses must implement this method")

    def get_resource(self, resource_id: str, **kwargs) -> T:
        """Get a specific resource by its ID.

        Args:
            resource_id: The ID of the resource to retrieve
            **kwargs: Additional parameters to pass to the get request

        Returns:
            A resource model instance
        """
        # This would be implemented by subclasses for specific resources
        raise NotImplementedError("Subclasses must implement this method")

    def create_resource(self, resource: T, **kwargs) -> T:
        """Create a new resource.

        Args:
            resource: The resource model to create
            **kwargs: Additional parameters to pass to the create request

        Returns:
            The created resource model instance
        """
        # This would be implemented by subclasses for specific resources
        raise NotImplementedError("Subclasses must implement this method")

    def update_resource(self, resource: T, **kwargs) -> T:
        """Update an existing resource.

        Args:
            resource: The resource model to update
            **kwargs: Additional parameters to pass to the update request

        Returns:
            The updated resource model instance
        """
        # This would be implemented by subclasses for specific resources
        raise NotImplementedError("Subclasses must implement this method")

    def delete_resource(self, resource_id: str, **kwargs) -> bool:
        """Delete a resource by its ID.

        Args:
            resource_id: The ID of the resource to delete
            **kwargs: Additional parameters to pass to the delete request

        Returns:
            True if the deletion was successful, False otherwise
        """
        # This would be implemented by subclasses for specific resources
        raise NotImplementedError("Subclasses must implement this method")

    def _process_tags(
        self, body: Dict[str, Any], tags: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Process tags for a resource API request.

        This adds tags to the request body. Different GCP services handle tags
        differently:
        - Some services use 'tags' field directly
        - Some use 'labels' field
        - Some support both with different semantics

        This base implementation merges tags into the existing labels field.
        Service-specific implementations can override this method.

        Args:
            body: The request body dictionary
            tags: Optional dictionary of tags to apply

        Returns:
            The updated request body dictionary
        """
        if not tags:
            return body

        # If there are no labels yet, initialize them
        if "labels" not in body or body["labels"] is None:
            body["labels"] = {}

        # Add tags to labels
        for key, value in tags.items():
            body["labels"][key] = value

        return body

    def _parse_response(self, response: Dict[str, Any]) -> T:
        """Parse an API response into a resource model.

        Args:
            response: The API response dictionary

        Returns:
            A resource model instance
        """
        return self.resource_model.from_api_response(response)
