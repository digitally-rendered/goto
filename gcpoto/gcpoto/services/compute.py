"""Service implementation for Google Compute Engine."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.base import GCPResource
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
)

logger = logging.getLogger(__name__)


class ComputeInstance(GCPResource):
    """Model for a Google Compute Engine instance."""

    machine_type: str
    status: str
    zone: str

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "ComputeInstance":
        """Create an instance from API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ComputeInstance instance
        """
        return cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="compute.instance",
            project=response.get("projectId", ""),
            machine_type=response.get("machineType", "").split("/")[-1],
            status=response.get("status", ""),
            zone=response.get("zone", "").split("/")[-1],
            labels=response.get("labels", {}),
            created=response.get("creationTimestamp"),
            updated=response.get("lastStartTimestamp"),
        )


class ComputeService(GCPService[ComputeInstance]):
    """Service for interacting with Google Compute Engine."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the compute service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="compute",
            version="v1",
            credentials_file=credentials_file,
            resource_model=ComputeInstance,
        )

    def list_resources(self, zone: str, **kwargs) -> List[ComputeInstance]:
        """List compute instances in the specified zone.

        Args:
            zone: The zone to list instances from
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of ComputeInstance instances
        """
        try:
            request = self.service.instances().list(
                project=self.project_id, zone=zone, **kwargs
            )
            response = request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

        instances = []
        for item in response.get("items", []):
            instances.append(self._parse_response(item))

        return instances

    def get_resource(self, resource_id: str, zone: str, **kwargs) -> ComputeInstance:
        """Get a specific instance by name.

        Args:
            resource_id: The name of the instance to retrieve
            zone: The zone the instance is in
            **kwargs: Additional parameters to pass to the get request

        Returns:
            A ComputeInstance instance
        """
        try:
            request = self.service.instances().get(
                project=self.project_id, zone=zone, instance=resource_id, **kwargs
            )
            response = request.execute()
            return self._parse_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ComputeInstance", resource_id)
            raise APIError(e.resp.status, str(e))

    def create_resource(
        self, resource: ComputeInstance, zone: str, **kwargs
    ) -> ComputeInstance:
        """Create a new compute instance.

        Args:
            resource: The instance model to create
            zone: The zone to create the instance in
            **kwargs: Additional parameters to pass to the create request

        Returns:
            The created ComputeInstance instance
        """
        # This would be a more complex implementation in practice
        # Simplified for example purposes
        body = {
            "name": resource.name,
            "machineType": f"zones/{zone}/machineTypes/{resource.machine_type}",
            "labels": resource.labels or {},
        }

        try:
            request = self.service.instances().insert(
                project=self.project_id, zone=zone, body=body, **kwargs
            )
            response = request.execute()
            return self._parse_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"ComputeInstance '{resource.name}' already exists"
                )
            raise APIError(e.resp.status, str(e))

    def delete_resource(self, resource_id: str, zone: str, **kwargs) -> bool:
        """Delete an instance by name.

        Args:
            resource_id: The name of the instance to delete
            zone: The zone the instance is in
            **kwargs: Additional parameters to pass to the delete request

        Returns:
            True if the deletion was successful
        """
        try:
            request = self.service.instances().delete(
                project=self.project_id, zone=zone, instance=resource_id, **kwargs
            )
            request.execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ComputeInstance", resource_id)
            raise APIError(e.resp.status, str(e))
