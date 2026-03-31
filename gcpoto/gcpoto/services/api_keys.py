"""Service implementation for Google Cloud API Keys."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.api_keys import APIKey
from gcpoto.exceptions import (
    APIError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


class APIKeysService(GCPService[APIKey]):
    """Service for interacting with Google Cloud API Keys."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the API Keys service.

        Args:
            project_id: The GCP project ID to use for API calls.
            credentials_file: Optional path to a service account credentials
                file.
            **kwargs: Additional arguments to pass to the service constructor.
        """
        super().__init__(
            project_id=project_id,
            service_name="apikeys",
            version="v2",
            credentials_file=credentials_file,
            resource_model=APIKey,
            **kwargs,
        )

    # ------------------------------------------------------------------ #
    #  Key operations
    # ------------------------------------------------------------------ #

    def list_keys(self, location: str = "global") -> List[APIKey]:
        """List API keys in a given location.

        Args:
            location: The location of the keys (default ``"global"``).

        Returns:
            A list of APIKey instances.
        """
        logger.info(
            "Listing API keys in %s for project %s",
            location,
            self.project_id,
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        request = self.service.projects().locations().keys().list(
            parent=parent
        )

        keys = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("keys", []):
                keys.append(APIKey.from_api_response(item))
            request = (
                self.service.projects()
                .locations()
                .keys()
                .list_next(request, response)
            )

        logger.info("Found %s API keys", len(keys))
        return keys

    def get_key(self, location: str, key_id: str) -> APIKey:
        """Get a specific API key.

        Args:
            location: The location of the key.
            key_id: The ID of the API key.

        Returns:
            An APIKey instance.

        Raises:
            ResourceNotFoundError: If the key does not exist.
            APIError: If the API call fails.
        """
        logger.info("Getting API key %s in %s", key_id, location)

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/keys/{key_id}"
        )

        request = (
            self.service.projects().locations().keys().get(name=name)
        )
        response = self._execute(request, "APIKey", key_id)
        return APIKey.from_api_response(response)
    def create_key(
        self,
        location: str,
        display_name: Optional[str] = None,
        restrictions: Optional[Dict] = None,
    ) -> APIKey:
        """Create a new API key.

        Args:
            location: The location for the new key.
            display_name: Optional display name for the key.
            restrictions: Optional restrictions for the key.

        Returns:
            An APIKey instance for the newly created key.

        Raises:
            APIError: If the API call fails.
        """
        logger.info("Creating API key in %s", location)

        parent = f"projects/{self.project_id}/locations/{location}"
        body: Dict[str, Any] = {}

        if display_name:
            body["displayName"] = display_name
        if restrictions:
            body["restrictions"] = restrictions

        request = (
            self.service.projects()
            .locations()
            .keys()
            .create(parent=parent, body=body)
        )
        response = self._execute(request)
        logger.info("Created API key in %s", location)
        return APIKey.from_api_response(response)
    def update_key(
        self,
        location: str,
        key_id: str,
        display_name: Optional[str] = None,
        restrictions: Optional[Dict] = None,
    ) -> APIKey:
        """Update an existing API key.

        Args:
            location: The location of the key.
            key_id: The ID of the key to update.
            display_name: Optional new display name.
            restrictions: Optional new restrictions.

        Returns:
            An APIKey instance for the updated key.

        Raises:
            ResourceNotFoundError: If the key does not exist.
            APIError: If the API call fails.
        """
        logger.info("Updating API key %s in %s", key_id, location)

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/keys/{key_id}"
        )

        body: Dict[str, Any] = {}
        update_mask_fields = []

        if display_name is not None:
            body["displayName"] = display_name
            update_mask_fields.append("displayName")
        if restrictions is not None:
            body["restrictions"] = restrictions
            update_mask_fields.append("restrictions")

        update_mask = ",".join(update_mask_fields)

        request = (
            self.service.projects()
            .locations()
            .keys()
            .patch(name=name, updateMask=update_mask, body=body)
        )
        response = self._execute(request, "APIKey", key_id)
        logger.info("Updated API key %s", key_id)
        return APIKey.from_api_response(response)
    def delete_key(self, location: str, key_id: str) -> bool:
        """Delete an API key.

        Args:
            location: The location of the key.
            key_id: The ID of the key to delete.

        Returns:
            True if the deletion was successful.

        Raises:
            ResourceNotFoundError: If the key does not exist.
            APIError: If the API call fails.
        """
        logger.info("Deleting API key %s in %s", key_id, location)

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/keys/{key_id}"
        )

        request = self.service.projects().locations().keys().delete(
            name=name
        )
        self._execute(request)
        logger.info("Deleted API key %s", key_id)
        return True
    def undelete_key(self, location: str, key_id: str) -> APIKey:
        """Undelete a previously deleted API key.

        Args:
            location: The location of the key.
            key_id: The ID of the key to undelete.

        Returns:
            An APIKey instance for the restored key.

        Raises:
            ResourceNotFoundError: If the key does not exist.
            APIError: If the API call fails.
        """
        logger.info("Undeleting API key %s in %s", key_id, location)

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/keys/{key_id}"
        )

        request = (
            self.service.projects()
            .locations()
            .keys()
            .undelete(name=name)
        )
        response = self._execute(request, "APIKey", key_id)
        logger.info("Undeleted API key %s", key_id)
        return APIKey.from_api_response(response)
    def get_key_string(self, location: str, key_id: str) -> str:
        """Get the key string for an API key.

        Args:
            location: The location of the key.
            key_id: The ID of the key.

        Returns:
            The API key string.

        Raises:
            ResourceNotFoundError: If the key does not exist.
            APIError: If the API call fails.
        """
        logger.info("Getting key string for API key %s in %s", key_id, location)

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/keys/{key_id}"
        )

        request = (
            self.service.projects()
            .locations()
            .keys()
            .getKeyString(name=name)
        )
        response = self._execute(request, "APIKey", key_id)
        return response.get("keyString", "")