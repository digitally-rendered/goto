"""Service implementation for Google Cloud Data Fusion."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.data_fusion import DataFusionInstance
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class DataFusionService(GCPService[DataFusionInstance]):
    """Service for interacting with Google Cloud Data Fusion."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Data Fusion service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="datafusion",
            version="v1",
            credentials_file=credentials_file,
            resource_model=DataFusionInstance,
            **kwargs,
        )

    def list_instances(self, location: str) -> List[DataFusionInstance]:
        """List Data Fusion instances in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            A list of DataFusionInstance instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        request = (
            self.service.projects()
            .locations()
            .instances()
            .list(parent=parent)
        )

        instances = []
        while request is not None:
            response = request.execute()
            for item in response.get("instances", []):
                instances.append(
                    DataFusionInstance.from_api_response(
                        item, self.project_id
                    )
                )
            request = (
                self.service.projects()
                .locations()
                .instances()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s Data Fusion instances in %s",
            len(instances),
            location,
        )
        return instances

    def get_instance(
        self, location: str, instance_name: str
    ) -> DataFusionInstance:
        """Get a specific Data Fusion instance.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name of the instance

        Returns:
            A DataFusionInstance instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        try:
            request = (
                self.service.projects()
                .locations()
                .instances()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("instance", instance_name)
            raise

        logger.debug("Retrieved Data Fusion instance %s", instance_name)
        return DataFusionInstance.from_api_response(
            response, self.project_id
        )

    def create_instance(
        self,
        location: str,
        instance_name: str,
        type_field: str,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        private_instance: bool = False,
    ) -> DataFusionInstance:
        """Create a new Data Fusion instance.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name for the new instance
            type_field: The instance type (BASIC, ENTERPRISE, DEVELOPER)
            description: Optional description for the instance
            labels: Optional labels for the instance
            private_instance: Whether the instance should be private

        Returns:
            The created DataFusionInstance instance
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        body: Dict[str, Any] = {"type": type_field}

        if description is not None:
            body["description"] = description

        if labels is not None:
            body["labels"] = labels

        if private_instance:
            body["privateInstance"] = True

        try:
            request = (
                self.service.projects()
                .locations()
                .instances()
                .create(
                    parent=parent,
                    instanceId=instance_name,
                    body=body,
                )
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

        logger.debug(
            "Created Data Fusion instance %s in %s",
            instance_name,
            location,
        )
        return DataFusionInstance.from_api_response(
            response, self.project_id
        )

    def update_instance(
        self,
        location: str,
        instance_name: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> DataFusionInstance:
        """Update a Data Fusion instance.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name of the instance to update
            update_mask: Comma-separated list of fields to update
            update_fields: The fields to update

        Returns:
            The updated DataFusionInstance instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        try:
            request = (
                self.service.projects()
                .locations()
                .instances()
                .patch(
                    name=name,
                    updateMask=update_mask,
                    body=update_fields,
                )
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("instance", instance_name)
            raise

        logger.debug("Updated Data Fusion instance %s", instance_name)
        return DataFusionInstance.from_api_response(
            response, self.project_id
        )

    def delete_instance(
        self, location: str, instance_name: str
    ) -> bool:
        """Delete a Data Fusion instance.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name of the instance to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        try:
            self.service.projects().locations().instances().delete(
                name=name
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("instance", instance_name)
            raise

        logger.debug("Deleted Data Fusion instance %s", instance_name)
        return True

    def restart_instance(
        self, location: str, instance_name: str
    ) -> DataFusionInstance:
        """Restart a Data Fusion instance.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name of the instance to restart

        Returns:
            The restarted DataFusionInstance instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        try:
            request = (
                self.service.projects()
                .locations()
                .instances()
                .restart(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("instance", instance_name)
            raise

        logger.debug("Restarted Data Fusion instance %s", instance_name)
        return DataFusionInstance.from_api_response(
            response, self.project_id
        )
