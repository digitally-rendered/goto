"""Service implementation for Google Cloud Filestore."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.filestore import FilestoreInstance
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class FilestoreService(GCPService[FilestoreInstance]):
    """Service for interacting with Google Cloud Filestore."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Filestore service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="file",
            version="v1",
            credentials_file=credentials_file,
            resource_model=FilestoreInstance,
            **kwargs,
        )

    def list_instances(
        self, location: str = "-"
    ) -> List[FilestoreInstance]:
        """List Filestore instances in a location.

        Args:
            location: The GCP location (e.g. 'us-east1'). Use '-' for all locations.

        Returns:
            A list of FilestoreInstance instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug("Listing Filestore instances in %s", parent)

        instances = []
        request = (
            self.service.projects()
            .locations()
            .instances()
            .list(parent=parent)
        )

        while request is not None:
            response = request.execute()
            for item in response.get("instances", []):
                instances.append(
                    FilestoreInstance.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .instances()
                .list_next(request, response)
            )

        return instances

    def get_instance(
        self, location: str, instance_id: str
    ) -> FilestoreInstance:
        """Get a specific Filestore instance.

        Args:
            location: The GCP location (e.g. 'us-east1')
            instance_id: The instance ID

        Returns:
            A FilestoreInstance instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_id}"
        )
        logger.debug("Getting Filestore instance %s", name)

        request = (
            self.service.projects()
            .locations()
            .instances()
            .get(name=name)
        )
        response = request.execute()

        return FilestoreInstance.from_api_response(response, self.project_id)

    def create_instance(
        self,
        location: str,
        instance_id: str,
        tier: str,
        file_shares: List[Dict[str, Any]],
        networks: List[Dict[str, Any]],
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new Filestore instance.

        Args:
            location: The GCP location (e.g. 'us-east1')
            instance_id: The instance ID to create
            tier: The service tier (BASIC_HDD, BASIC_SSD, HIGH_SCALE_SSD, ENTERPRISE)
            file_shares: List of file share configurations
            networks: List of network configurations
            description: Optional description for the instance
            labels: Optional labels to apply

        Returns:
            The long-running operation response
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug(
            "Creating Filestore instance %s in %s", instance_id, parent
        )

        body: Dict[str, Any] = {
            "tier": tier,
            "fileShares": file_shares,
            "networks": networks,
        }

        if description is not None:
            body["description"] = description

        if labels is not None:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .instances()
            .create(parent=parent, instanceId=instance_id, body=body)
        )
        response = request.execute()

        return response

    def update_instance(
        self,
        location: str,
        instance_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an existing Filestore instance.

        Args:
            location: The GCP location
            instance_id: The instance ID to update
            update_mask: Comma-separated list of fields to update
            update_fields: Dictionary of fields to update

        Returns:
            The long-running operation response
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_id}"
        )
        logger.debug("Updating Filestore instance %s", name)

        request = (
            self.service.projects()
            .locations()
            .instances()
            .patch(name=name, updateMask=update_mask, body=update_fields)
        )
        response = request.execute()

        return response

    def delete_instance(
        self, location: str, instance_id: str
    ) -> Dict[str, Any]:
        """Delete a Filestore instance.

        Args:
            location: The GCP location
            instance_id: The instance ID to delete

        Returns:
            The long-running operation response
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_id}"
        )
        logger.debug("Deleting Filestore instance %s", name)

        request = (
            self.service.projects()
            .locations()
            .instances()
            .delete(name=name)
        )
        response = request.execute()

        return response

    def list_snapshots(
        self, location: str, instance_id: str
    ) -> List[Dict[str, Any]]:
        """List snapshots for a Filestore instance.

        Args:
            location: The GCP location
            instance_id: The instance ID

        Returns:
            A list of snapshot dictionaries
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_id}"
        )
        logger.debug("Listing snapshots for Filestore instance %s", parent)

        snapshots = []
        request = (
            self.service.projects()
            .locations()
            .instances()
            .snapshots()
            .list(parent=parent)
        )

        while request is not None:
            response = request.execute()
            for item in response.get("snapshots", []):
                snapshots.append(item)
            request = (
                self.service.projects()
                .locations()
                .instances()
                .snapshots()
                .list_next(request, response)
            )

        return snapshots

    def create_snapshot(
        self,
        location: str,
        instance_id: str,
        snapshot_id: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a snapshot for a Filestore instance.

        Args:
            location: The GCP location
            instance_id: The instance ID
            snapshot_id: The snapshot ID to create
            description: Optional description for the snapshot

        Returns:
            The long-running operation response
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_id}"
        )
        logger.debug(
            "Creating snapshot %s for Filestore instance %s",
            snapshot_id,
            parent,
        )

        body: Dict[str, Any] = {}
        if description is not None:
            body["description"] = description

        request = (
            self.service.projects()
            .locations()
            .instances()
            .snapshots()
            .create(parent=parent, snapshotId=snapshot_id, body=body)
        )
        response = request.execute()

        return response

    def delete_snapshot(
        self, location: str, instance_id: str, snapshot_id: str
    ) -> Dict[str, Any]:
        """Delete a snapshot for a Filestore instance.

        Args:
            location: The GCP location
            instance_id: The instance ID
            snapshot_id: The snapshot ID to delete

        Returns:
            The long-running operation response
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_id}/snapshots/{snapshot_id}"
        )
        logger.debug("Deleting Filestore snapshot %s", name)

        request = (
            self.service.projects()
            .locations()
            .instances()
            .snapshots()
            .delete(name=name)
        )
        response = request.execute()

        return response
