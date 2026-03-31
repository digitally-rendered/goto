"""Service implementation for Google Cloud reCAPTCHA Enterprise."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.recaptcha import RecaptchaKey, Assessment
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
)

logger = logging.getLogger(__name__)


class RecaptchaService(GCPService[RecaptchaKey]):
    """Service for interacting with Google Cloud reCAPTCHA Enterprise."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the reCAPTCHA Enterprise service.

        Args:
            project_id: The GCP project ID to use for API calls.
            credentials_file: Optional path to a service account credentials
                file.
            **kwargs: Additional arguments to pass to the service constructor.
        """
        super().__init__(
            project_id=project_id,
            service_name="recaptchaenterprise",
            version="v1",
            credentials_file=credentials_file,
            resource_model=RecaptchaKey,
            **kwargs,
        )

    # ------------------------------------------------------------------ #
    #  Key operations
    # ------------------------------------------------------------------ #

    def list_keys(self) -> List[RecaptchaKey]:
        """List reCAPTCHA keys for the project.

        Returns:
            A list of RecaptchaKey instances.
        """
        logger.info(
            "Listing reCAPTCHA keys for project %s", self.project_id
        )

        parent = f"projects/{self.project_id}"
        request = self.service.projects().keys().list(parent=parent)

        keys = []
        while request is not None:
            response = request.execute()
            for item in response.get("keys", []):
                keys.append(RecaptchaKey.from_api_response(item))
            request = (
                self.service.projects()
                .keys()
                .list_next(request, response)
            )

        logger.info("Found %s reCAPTCHA keys", len(keys))
        return keys

    def get_key(self, key_id: str) -> RecaptchaKey:
        """Get a specific reCAPTCHA key.

        Args:
            key_id: The ID of the reCAPTCHA key.

        Returns:
            A RecaptchaKey instance.

        Raises:
            ResourceNotFoundError: If the key does not exist.
            APIError: If the API call fails.
        """
        logger.info("Getting reCAPTCHA key %s", key_id)

        name = f"projects/{self.project_id}/keys/{key_id}"

        try:
            request = self.service.projects().keys().get(name=name)
            response = request.execute()
            return RecaptchaKey.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("RecaptchaKey", key_id)
            raise APIError(e.resp.status, str(e))

    def create_key(
        self,
        display_name: str,
        web_settings: Optional[Dict] = None,
        android_settings: Optional[Dict] = None,
        ios_settings: Optional[Dict] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> RecaptchaKey:
        """Create a new reCAPTCHA key.

        Args:
            display_name: The display name for the key.
            web_settings: Optional web platform settings.
            android_settings: Optional Android platform settings.
            ios_settings: Optional iOS platform settings.
            labels: Optional labels to apply to the key.

        Returns:
            A RecaptchaKey instance for the newly created key.

        Raises:
            APIError: If the API call fails.
        """
        logger.info("Creating reCAPTCHA key %s", display_name)

        parent = f"projects/{self.project_id}"
        body: Dict[str, Any] = {
            "displayName": display_name,
        }

        if web_settings:
            body["webSettings"] = web_settings
        if android_settings:
            body["androidSettings"] = android_settings
        if ios_settings:
            body["iosSettings"] = ios_settings
        if labels:
            body["labels"] = labels

        try:
            request = self.service.projects().keys().create(
                parent=parent, body=body
            )
            response = request.execute()
            logger.info("Created reCAPTCHA key %s", display_name)
            return RecaptchaKey.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"RecaptchaKey '{display_name}' already exists"
                )
            raise APIError(e.resp.status, str(e))

    def update_key(
        self,
        key_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> RecaptchaKey:
        """Update an existing reCAPTCHA key.

        Args:
            key_id: The ID of the key to update.
            update_mask: Comma-separated list of fields to update
                (e.g. ``"displayName,webSettings"``).
            update_fields: A dictionary of fields and values to update.

        Returns:
            A RecaptchaKey instance for the updated key.

        Raises:
            ResourceNotFoundError: If the key does not exist.
            APIError: If the API call fails.
        """
        logger.info("Updating reCAPTCHA key %s", key_id)

        name = f"projects/{self.project_id}/keys/{key_id}"

        try:
            request = self.service.projects().keys().patch(
                name=name, updateMask=update_mask, body=update_fields
            )
            response = request.execute()
            logger.info("Updated reCAPTCHA key %s", key_id)
            return RecaptchaKey.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("RecaptchaKey", key_id)
            raise APIError(e.resp.status, str(e))

    def delete_key(self, key_id: str) -> bool:
        """Delete a reCAPTCHA key.

        Args:
            key_id: The ID of the key to delete.

        Returns:
            True if the deletion was successful.

        Raises:
            ResourceNotFoundError: If the key does not exist.
            APIError: If the API call fails.
        """
        logger.info("Deleting reCAPTCHA key %s", key_id)

        name = f"projects/{self.project_id}/keys/{key_id}"

        try:
            self.service.projects().keys().delete(name=name).execute()
            logger.info("Deleted reCAPTCHA key %s", key_id)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("RecaptchaKey", key_id)
            raise APIError(e.resp.status, str(e))

    # ------------------------------------------------------------------ #
    #  Assessment operations
    # ------------------------------------------------------------------ #

    def create_assessment(self, event: Dict[str, Any]) -> Assessment:
        """Create a new assessment for a reCAPTCHA token.

        Args:
            event: The event to assess, including the token and site key.

        Returns:
            An Assessment instance with risk analysis results.

        Raises:
            APIError: If the API call fails.
        """
        logger.info("Creating reCAPTCHA assessment for project %s", self.project_id)

        parent = f"projects/{self.project_id}"
        body: Dict[str, Any] = {
            "event": event,
        }

        try:
            request = self.service.projects().assessments().create(
                parent=parent, body=body
            )
            response = request.execute()
            logger.info("Created reCAPTCHA assessment")
            return Assessment.from_api_response(response)
        except HttpError as e:
            raise APIError(e.resp.status, str(e))
