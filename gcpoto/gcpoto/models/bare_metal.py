"""Models for Google Cloud Bare Metal Solution resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class BareMetalInstance(GCPResource):
    """Model for a Bare Metal Solution instance."""

    location: str = Field("", description="The location of the instance")
    machine_type: str = Field("", description="The machine type of the instance")
    state: str = Field("", description="The current state of the instance")
    os_image: Optional[str] = Field(
        None, description="The OS image currently installed"
    )
    network_template: Optional[str] = Field(
        None, description="The network template for the instance"
    )
    networks: Optional[List[Dict]] = Field(
        None, description="The networks associated with the instance"
    )
    luns: Optional[List[Dict]] = Field(
        None, description="The LUNs associated with the instance"
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
    def from_api_response(cls, response: Dict[str, Any]) -> "BareMetalInstance":
        """Create a BareMetalInstance from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new BareMetalInstance instance
        """
        labels = response.get("labels")

        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="baremetalsolution.instance",
            project=response.get("projectId", ""),
            location=response.get("location", ""),
            machine_type=response.get("machineType", ""),
            state=response.get("state", ""),
            os_image=response.get("osImage"),
            network_template=response.get("networkTemplate"),
            networks=response.get("networks"),
            luns=response.get("luns"),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if labels:
            instance._tags = labels
        return instance


class BareMetalVolume(GCPResource):
    """Model for a Bare Metal Solution volume."""

    location: str = Field("", description="The location of the volume")
    storage_type: str = Field("", description="The storage type of the volume")
    size_gib: int = Field(0, description="The size of the volume in GiB")
    state: str = Field("", description="The current state of the volume")
    snapshot_auto_delete_behavior: Optional[str] = Field(
        None, description="The snapshot auto-delete behavior"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "BareMetalVolume":
        """Create a BareMetalVolume from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new BareMetalVolume instance
        """
        labels = response.get("labels")

        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="baremetalsolution.volume",
            project=response.get("projectId", ""),
            location=response.get("location", ""),
            storage_type=response.get("storageType", ""),
            size_gib=response.get("sizeGib", 0),
            state=response.get("state", ""),
            snapshot_auto_delete_behavior=response.get(
                "snapshotAutoDeleteBehavior"
            ),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        return instance
