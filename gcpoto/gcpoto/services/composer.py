"""Service implementation for Google Cloud Composer."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.composer import ComposerEnvironment
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class ComposerService(GCPService[ComposerEnvironment]):
    """Service for interacting with Google Cloud Composer."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Composer service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="composer",
            version="v1",
            credentials_file=credentials_file,
            resource_model=ComposerEnvironment,
            **kwargs,
        )

    def list_environments(
        self, location: str
    ) -> List[ComposerEnvironment]:
        """List Composer environments in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            A list of ComposerEnvironment instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        request = (
            self.service.projects()
            .locations()
            .environments()
            .list(parent=parent)
        )

        environments = []
        while request is not None:
            response = request.execute()
            for item in response.get("environments", []):
                environments.append(
                    ComposerEnvironment.from_api_response(
                        item, self.project_id
                    )
                )
            request = (
                self.service.projects()
                .locations()
                .environments()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s environments in %s", len(environments), location
        )
        return environments

    def get_environment(
        self, location: str, environment_name: str
    ) -> ComposerEnvironment:
        """Get a specific Composer environment.

        Args:
            location: The GCP location (e.g. 'us-central1')
            environment_name: The name of the environment

        Returns:
            A ComposerEnvironment instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/environments/{environment_name}"
        )
        try:
            request = (
                self.service.projects()
                .locations()
                .environments()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "environment", environment_name
                )
            raise

        logger.debug("Retrieved environment %s", environment_name)
        return ComposerEnvironment.from_api_response(
            response, self.project_id
        )

    def create_environment(
        self,
        location: str,
        environment_name: str,
        config: Dict[str, Any],
        labels: Optional[Dict[str, str]] = None,
    ) -> ComposerEnvironment:
        """Create a new Composer environment.

        Args:
            location: The GCP location (e.g. 'us-central1')
            environment_name: The name for the new environment
            config: The environment configuration
            labels: Optional labels for the environment

        Returns:
            The created ComposerEnvironment instance
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        body: Dict[str, Any] = {
            "name": (
                f"projects/{self.project_id}/locations/{location}"
                f"/environments/{environment_name}"
            ),
            "config": config,
        }

        if labels is not None:
            body["labels"] = labels

        try:
            request = (
                self.service.projects()
                .locations()
                .environments()
                .create(parent=parent, body=body)
            )
            response = request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

        logger.debug(
            "Created environment %s in %s", environment_name, location
        )
        return ComposerEnvironment.from_api_response(
            response, self.project_id
        )

    def update_environment(
        self,
        location: str,
        environment_name: str,
        update_mask: str,
        environment_config: Dict[str, Any],
    ) -> ComposerEnvironment:
        """Update a Composer environment.

        Args:
            location: The GCP location (e.g. 'us-central1')
            environment_name: The name of the environment to update
            update_mask: Comma-separated list of fields to update
            environment_config: The updated configuration fields

        Returns:
            The updated ComposerEnvironment instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/environments/{environment_name}"
        )
        try:
            request = (
                self.service.projects()
                .locations()
                .environments()
                .patch(
                    name=name,
                    updateMask=update_mask,
                    body=environment_config,
                )
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "environment", environment_name
                )
            raise

        logger.debug("Updated environment %s", environment_name)
        return ComposerEnvironment.from_api_response(
            response, self.project_id
        )

    def delete_environment(
        self, location: str, environment_name: str
    ) -> bool:
        """Delete a Composer environment.

        Args:
            location: The GCP location (e.g. 'us-central1')
            environment_name: The name of the environment to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/environments/{environment_name}"
        )
        try:
            self.service.projects().locations().environments().delete(
                name=name
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "environment", environment_name
                )
            raise

        logger.debug("Deleted environment %s", environment_name)
        return True
