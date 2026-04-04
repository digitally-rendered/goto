"""Models for Google Cloud Memorystore (Redis) resources."""

from typing import Dict, Optional, Any

from pydantic import Field

from gcpoto.models.base import GCPResource


class RedisInstance(GCPResource):
    """Model for a Google Cloud Memorystore Redis instance."""

    location: str = Field("", description="The GCP location of the instance")
    display_name: Optional[str] = Field(
        None, description="An arbitrary user-provided name for the instance"
    )
    tier: str = Field(
        "", description="The service tier (BASIC or STANDARD_HA)"
    )
    memory_size_gb: int = Field(
        0, description="Redis memory size in GiB"
    )
    host: Optional[str] = Field(
        None, description="Hostname or IP address of the Redis endpoint"
    )
    port: Optional[int] = Field(
        None, description="The port number of the Redis endpoint"
    )
    current_location_id: Optional[str] = Field(
        None, description="The current zone where the Redis primary node is located"
    )
    redis_version: Optional[str] = Field(
        None, description="The version of Redis software"
    )
    state: str = Field(
        "", description="The current state of the instance"
    )
    status_message: Optional[str] = Field(
        None, description="Additional information about the current status"
    )
    redis_configs: Optional[Dict[str, str]] = Field(
        None, description="Redis configuration parameters"
    )
    authorized_network: Optional[str] = Field(
        None,
        description="The full name of the authorized network for the instance",
    )
    connect_mode: Optional[str] = Field(
        None, description="The network connect mode (DIRECT_PEERING or PRIVATE_SERVICE_ACCESS)"
    )
    auth_enabled: bool = Field(
        False, description="Whether AUTH is enabled for the instance"
    )
    transit_encryption_mode: Optional[str] = Field(
        None, description="The TLS mode of the Redis instance"
    )
    maintenance_policy: Optional[Dict] = Field(
        None, description="The maintenance policy for the instance"
    )
    maintenance_schedule: Optional[Dict] = Field(
        None, description="The upcoming maintenance schedule"
    )
    _tags: Optional[Dict[str, str]] = None

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "RedisInstance":
        """Create a RedisInstance from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new RedisInstance instance
        """
        # Extract instance ID from the fully qualified name
        # Format: projects/{project}/locations/{location}/instances/{instance}
        name = response.get("name", "")
        instance_id = name.rsplit("/", 1)[-1] if "/" in name else name

        # Extract location from the name
        parts = name.split("/")
        location = parts[3] if len(parts) >= 4 else ""

        # Extract project from the name
        project = parts[1] if len(parts) >= 2 else ""

        labels = response.get("labels")

        instance = cls(
            id=instance_id,
            name=name,
            type="redis.instance",
            project=project,
            location=location,
            display_name=response.get("displayName"),
            tier=response.get("tier", ""),
            memory_size_gb=response.get("memorySizeGb", 0),
            host=response.get("host"),
            port=response.get("port"),
            current_location_id=response.get("currentLocationId"),
            redis_version=response.get("redisVersion"),
            state=response.get("state", ""),
            status_message=response.get("statusMessage"),
            redis_configs=response.get("redisConfigs"),
            authorized_network=response.get("authorizedNetwork"),
            connect_mode=response.get("connectMode"),
            auth_enabled=response.get("authEnabled", False),
            transit_encryption_mode=response.get("transitEncryptionMode"),
            maintenance_policy=response.get("maintenancePolicy"),
            maintenance_schedule=response.get("maintenanceSchedule"),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if labels:
            instance._tags = labels
        return instance
