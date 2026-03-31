"""Service implementation for Google Cloud Memorystore (Redis)."""

import logging
from typing import List, Optional, Dict, Any

from gcpoto.services.base import GCPService
from gcpoto.models.memorystore import RedisInstance
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class MemorystoreService(GCPService[RedisInstance]):
    """Service for interacting with Google Cloud Memorystore (Redis)."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the Memorystore service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="redis",
            version="v1",
            credentials_file=credentials_file,
            resource_model=RedisInstance,
        )

    def _instance_path(self, location: str, instance_id: str) -> str:
        """Format the fully qualified instance resource path.

        Args:
            location: The GCP location (region)
            instance_id: The instance ID

        Returns:
            The fully qualified resource path
        """
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_id}"
        )

    def _location_path(self, location: str) -> str:
        """Format the fully qualified location path.

        Args:
            location: The GCP location (region), use '-' for all locations

        Returns:
            The fully qualified location path
        """
        return f"projects/{self.project_id}/locations/{location}"

    def list_instances(self, location: str = "-") -> List[RedisInstance]:
        """List Redis instances in the project.

        Args:
            location: The GCP location to list instances from.
                Use '-' to list across all locations.

        Returns:
            A list of RedisInstance instances
        """
        parent = self._location_path(location)
        logger.info(
            "Listing Redis instances in %s", parent
        )
        request = self.service.projects().locations().instances().list(
            parent=parent
        )
        response = request.execute()
        instances = [
            RedisInstance.from_api_response(item)
            for item in response.get("instances", [])
        ]
        logger.info("Found %s Redis instance(s)", len(instances))
        return instances

    def get_instance(
        self, location: str, instance_id: str
    ) -> RedisInstance:
        """Get a specific Redis instance.

        Args:
            location: The GCP location of the instance
            instance_id: The ID of the instance to retrieve

        Returns:
            A RedisInstance instance

        Raises:
            ResourceNotFoundError: If the instance is not found
        """
        name = self._instance_path(location, instance_id)
        logger.info("Getting Redis instance %s", name)
        try:
            request = self.service.projects().locations().instances().get(
                name=name
            )
            response = request.execute()
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    "RedisInstance", instance_id
                ) from e
            raise APIError(500, str(e)) from e
        return RedisInstance.from_api_response(response)

    def create_instance(
        self,
        location: str,
        instance_id: str,
        tier: str,
        memory_size_gb: int,
        redis_version: Optional[str] = None,
        display_name: Optional[str] = None,
        authorized_network: Optional[str] = None,
        redis_configs: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new Redis instance.

        Args:
            location: The GCP location for the instance
            instance_id: The ID for the new instance
            tier: The service tier (BASIC or STANDARD_HA)
            memory_size_gb: Redis memory size in GiB
            redis_version: The version of Redis (e.g. REDIS_7_0)
            display_name: An optional display name for the instance
            authorized_network: The full resource name of the VPC network
            redis_configs: Redis configuration parameters
            labels: Labels to apply to the instance

        Returns:
            The long-running operation response dictionary
        """
        parent = self._location_path(location)
        body: Dict[str, Any] = {
            "tier": tier,
            "memorySizeGb": memory_size_gb,
        }

        if redis_version is not None:
            body["redisVersion"] = redis_version
        if display_name is not None:
            body["displayName"] = display_name
        if authorized_network is not None:
            body["authorizedNetwork"] = authorized_network
        if redis_configs is not None:
            body["redisConfigs"] = redis_configs
        if labels is not None:
            body["labels"] = labels

        logger.info(
            "Creating Redis instance %s in %s with tier %s and %s GB",
            instance_id,
            parent,
            tier,
            memory_size_gb,
        )
        request = self.service.projects().locations().instances().create(
            parent=parent, instanceId=instance_id, body=body
        )
        response = request.execute()
        logger.info("Create operation started for instance %s", instance_id)
        return response

    def update_instance(
        self,
        location: str,
        instance_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an existing Redis instance.

        Args:
            location: The GCP location of the instance
            instance_id: The ID of the instance to update
            update_mask: Comma-separated list of fields to update
                (e.g. 'displayName,memorySizeGb')
            update_fields: Dictionary of fields and their new values

        Returns:
            The long-running operation response dictionary
        """
        name = self._instance_path(location, instance_id)
        logger.info(
            "Updating Redis instance %s with mask %s",
            name,
            update_mask,
        )
        request = self.service.projects().locations().instances().patch(
            name=name, updateMask=update_mask, body=update_fields
        )
        response = request.execute()
        logger.info("Update operation started for instance %s", instance_id)
        return response

    def delete_instance(
        self, location: str, instance_id: str
    ) -> Dict[str, Any]:
        """Delete a Redis instance.

        Args:
            location: The GCP location of the instance
            instance_id: The ID of the instance to delete

        Returns:
            The long-running operation response dictionary
        """
        name = self._instance_path(location, instance_id)
        logger.info("Deleting Redis instance %s", name)
        request = self.service.projects().locations().instances().delete(
            name=name
        )
        response = request.execute()
        logger.info("Delete operation started for instance %s", instance_id)
        return response

    def upgrade_instance(
        self, location: str, instance_id: str, redis_version: str
    ) -> Dict[str, Any]:
        """Upgrade a Redis instance to a specified version.

        Args:
            location: The GCP location of the instance
            instance_id: The ID of the instance to upgrade
            redis_version: The target Redis version (e.g. REDIS_7_0)

        Returns:
            The long-running operation response dictionary
        """
        name = self._instance_path(location, instance_id)
        body = {"redisVersion": redis_version}
        logger.info(
            "Upgrading Redis instance %s to version %s",
            name,
            redis_version,
        )
        request = self.service.projects().locations().instances().upgrade(
            name=name, body=body
        )
        response = request.execute()
        logger.info(
            "Upgrade operation started for instance %s", instance_id
        )
        return response

    def failover_instance(
        self,
        location: str,
        instance_id: str,
        data_protection_mode: str = "LIMITED_DATA_LOSS",
    ) -> Dict[str, Any]:
        """Initiate a failover of a STANDARD_HA Redis instance.

        Args:
            location: The GCP location of the instance
            instance_id: The ID of the instance to failover
            data_protection_mode: The data protection mode for the failover.
                Either 'LIMITED_DATA_LOSS' or 'FORCE_DATA_LOSS'.

        Returns:
            The long-running operation response dictionary
        """
        name = self._instance_path(location, instance_id)
        body = {
            "dataProtectionMode": data_protection_mode,
        }
        logger.info(
            "Initiating failover for Redis instance %s with mode %s",
            name,
            data_protection_mode,
        )
        request = self.service.projects().locations().instances().failover(
            name=name, body=body
        )
        response = request.execute()
        logger.info(
            "Failover operation started for instance %s", instance_id
        )
        return response

    def get_instance_auth_string(
        self, location: str, instance_id: str
    ) -> str:
        """Get the AUTH string for a Redis instance.

        Args:
            location: The GCP location of the instance
            instance_id: The ID of the instance

        Returns:
            The AUTH string for the instance
        """
        name = self._instance_path(location, instance_id)
        logger.info("Getting AUTH string for Redis instance %s", name)
        request = (
            self.service.projects()
            .locations()
            .instances()
            .getAuthString(name=name)
        )
        response = request.execute()
        return response.get("authString", "")
