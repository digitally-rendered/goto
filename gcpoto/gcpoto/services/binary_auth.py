"""Service implementation for Google Cloud Binary Authorization."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.binary_auth import Policy, Attestor
from gcpoto.exceptions import (
    APIError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


class BinaryAuthService(GCPService[Policy]):
    """Service for interacting with Google Cloud Binary Authorization."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Binary Authorization service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="binaryauthorization",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Policy,
            **kwargs,
        )

    def get_policy(self) -> Policy:
        """Get the Binary Authorization policy for the project.

        Returns:
            A Policy instance

        Raises:
            ResourceNotFoundError: If the policy does not exist
            APIError: If the API call fails
        """
        logger.info("Getting Binary Authorization policy for project %s", self.project_id)

        request = self.service.projects().getPolicy(
            name=f"projects/{self.project_id}/policy"
        )
        response = self._execute(request, "Policy", self.project_id)
        return Policy.from_api_response(response)
    def update_policy(self, policy_body: Dict[str, Any]) -> Policy:
        """Update the Binary Authorization policy for the project.

        Args:
            policy_body: The policy body to update

        Returns:
            The updated Policy instance

        Raises:
            APIError: If the API call fails
        """
        logger.info(
            "Updating Binary Authorization policy for project %s",
            self.project_id,
        )

        request = self.service.projects().updatePolicy(
            name=f"projects/{self.project_id}/policy",
            body=policy_body,
        )
        response = self._execute(request)
        return Policy.from_api_response(response)
    def list_attestors(self) -> List[Attestor]:
        """List all attestors in the project.

        Returns:
            A list of Attestor instances
        """
        logger.info(
            "Listing Binary Authorization attestors for project %s",
            self.project_id,
        )

        request = self.service.projects().attestors().list(
            parent=f"projects/{self.project_id}"
        )

        attestors = []
        while request is not None:
            response = self._execute(request)
            for attestor_data in response.get("attestors", []):
                attestors.append(Attestor.from_api_response(attestor_data))
            request = self.service.projects().attestors().list_next(
                request, response
            )

        logger.info("Found %s attestors", len(attestors))
        return attestors

    def get_attestor(self, attestor_id: str) -> Attestor:
        """Get a specific attestor.

        Args:
            attestor_id: The attestor ID

        Returns:
            An Attestor instance

        Raises:
            ResourceNotFoundError: If the attestor does not exist
        """
        logger.info("Getting attestor %s", attestor_id)

        request = self.service.projects().attestors().get(
            name=f"projects/{self.project_id}/attestors/{attestor_id}"
        )
        response = self._execute(request, "Attestor", attestor_id)
        return Attestor.from_api_response(response)
    def create_attestor(
        self, attestor_id: str, attestor_body: Dict[str, Any]
    ) -> Attestor:
        """Create a new attestor.

        Args:
            attestor_id: The attestor ID to create
            attestor_body: The attestor body

        Returns:
            The created Attestor instance

        Raises:
            APIError: If the API call fails
        """
        logger.info("Creating attestor %s", attestor_id)

        request = self.service.projects().attestors().create(
            parent=f"projects/{self.project_id}",
            attestorId=attestor_id,
            body=attestor_body,
        )
        response = self._execute(request)
        logger.info("Created attestor %s", attestor_id)
        return Attestor.from_api_response(response)
    def update_attestor(
        self, attestor_id: str, attestor_body: Dict[str, Any]
    ) -> Attestor:
        """Update an existing attestor.

        Args:
            attestor_id: The attestor ID to update
            attestor_body: The updated attestor body

        Returns:
            The updated Attestor instance

        Raises:
            ResourceNotFoundError: If the attestor does not exist
            APIError: If the API call fails
        """
        logger.info("Updating attestor %s", attestor_id)

        request = self.service.projects().attestors().update(
            name=f"projects/{self.project_id}/attestors/{attestor_id}",
            body=attestor_body,
        )
        response = self._execute(request, "Attestor", attestor_id)
        logger.info("Updated attestor %s", attestor_id)
        return Attestor.from_api_response(response)
    def delete_attestor(self, attestor_id: str) -> bool:
        """Delete an attestor.

        Args:
            attestor_id: The attestor ID to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the attestor does not exist
            APIError: If the API call fails
        """
        logger.info("Deleting attestor %s", attestor_id)

        self.service.projects().attestors().delete(
            name=f"projects/{self.project_id}/attestors/{attestor_id}"
        ).execute()
        logger.info("Deleted attestor %s", attestor_id)
        return True