"""Service implementation for Google Cloud Bare Metal Solution."""

import logging
from typing import List, Optional, Dict, Any

from gcpoto.services.base import GCPService
from gcpoto.models.bare_metal import BareMetalInstance, BareMetalVolume
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class BareMetalService(GCPService[BareMetalInstance]):
    """Service for interacting with Google Cloud Bare Metal Solution."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the Bare Metal Solution service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="baremetalsolution",
            version="v2",
            credentials_file=credentials_file,
            resource_model=BareMetalInstance,
        )

    # --- Instance methods ---

    def list_instances(self, location: str) -> List[BareMetalInstance]:
        """List Bare Metal instances in the project.

        Args:
            location: The location to list instances in

        Returns:
            A list of BareMetalInstance instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug("Listing Bare Metal instances in %s", parent)

        request = (
            self.service.projects()
            .locations()
            .instances()
            .list(parent=parent)
        )
        response = request.execute()
        instances = [
            BareMetalInstance.from_api_response(item)
            for item in response.get("instances", [])
        ]
        logger.info(
            "Found %s Bare Metal instance(s) in %s", len(instances), parent
        )
        return instances

    def get_instance(
        self, location: str, instance_name: str
    ) -> BareMetalInstance:
        """Get a specific Bare Metal instance by name.

        Args:
            location: The location of the instance
            instance_name: The name of the instance

        Returns:
            A BareMetalInstance instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        logger.debug("Getting Bare Metal instance %s", name)

        request = (
            self.service.projects()
            .locations()
            .instances()
            .get(name=name)
        )
        response = request.execute()
        return BareMetalInstance.from_api_response(response)

    def update_instance(
        self,
        location: str,
        instance_name: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a Bare Metal instance.

        Args:
            location: The location of the instance
            instance_name: The name of the instance
            update_mask: The field mask specifying which fields to update
            update_fields: The fields to update

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        logger.info("Updating Bare Metal instance %s", name)

        request = (
            self.service.projects()
            .locations()
            .instances()
            .patch(name=name, updateMask=update_mask, body=update_fields)
        )
        response = request.execute()
        logger.info("Instance update initiated for %s", instance_name)
        return response

    def reset_instance(
        self, location: str, instance_name: str
    ) -> Dict[str, Any]:
        """Reset a Bare Metal instance.

        Args:
            location: The location of the instance
            instance_name: The name of the instance

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        logger.info("Resetting Bare Metal instance %s", name)

        request = (
            self.service.projects()
            .locations()
            .instances()
            .reset(name=name)
        )
        response = request.execute()
        logger.info("Instance reset initiated for %s", instance_name)
        return response

    def start_instance(
        self, location: str, instance_name: str
    ) -> Dict[str, Any]:
        """Start a Bare Metal instance.

        Args:
            location: The location of the instance
            instance_name: The name of the instance

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        logger.info("Starting Bare Metal instance %s", name)

        request = (
            self.service.projects()
            .locations()
            .instances()
            .start(name=name)
        )
        response = request.execute()
        logger.info("Instance start initiated for %s", instance_name)
        return response

    def stop_instance(
        self, location: str, instance_name: str
    ) -> Dict[str, Any]:
        """Stop a Bare Metal instance.

        Args:
            location: The location of the instance
            instance_name: The name of the instance

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        logger.info("Stopping Bare Metal instance %s", name)

        request = (
            self.service.projects()
            .locations()
            .instances()
            .stop(name=name)
        )
        response = request.execute()
        logger.info("Instance stop initiated for %s", instance_name)
        return response

    # --- Volume methods ---

    def list_volumes(self, location: str) -> List[BareMetalVolume]:
        """List Bare Metal volumes in the project.

        Args:
            location: The location to list volumes in

        Returns:
            A list of BareMetalVolume instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug("Listing Bare Metal volumes in %s", parent)

        request = (
            self.service.projects()
            .locations()
            .volumes()
            .list(parent=parent)
        )
        response = request.execute()
        volumes = [
            BareMetalVolume.from_api_response(item)
            for item in response.get("volumes", [])
        ]
        logger.info(
            "Found %s Bare Metal volume(s) in %s", len(volumes), parent
        )
        return volumes

    def get_volume(
        self, location: str, volume_name: str
    ) -> BareMetalVolume:
        """Get a specific Bare Metal volume by name.

        Args:
            location: The location of the volume
            volume_name: The name of the volume

        Returns:
            A BareMetalVolume instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/volumes/{volume_name}"
        )
        logger.debug("Getting Bare Metal volume %s", name)

        request = (
            self.service.projects()
            .locations()
            .volumes()
            .get(name=name)
        )
        response = request.execute()
        return BareMetalVolume.from_api_response(response)

    def update_volume(
        self,
        location: str,
        volume_name: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a Bare Metal volume.

        Args:
            location: The location of the volume
            volume_name: The name of the volume
            update_mask: The field mask specifying which fields to update
            update_fields: The fields to update

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/volumes/{volume_name}"
        )
        logger.info("Updating Bare Metal volume %s", name)

        request = (
            self.service.projects()
            .locations()
            .volumes()
            .patch(name=name, updateMask=update_mask, body=update_fields)
        )
        response = request.execute()
        logger.info("Volume update initiated for %s", volume_name)
        return response
