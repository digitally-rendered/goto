"""Models for Google Cloud Dataplex resources."""

from typing import Dict, Optional, Any
from pydantic import Field

from gcpoto.models.base import GCPResource


class Lake(GCPResource):
    """Model for a Google Cloud Dataplex Lake."""

    location: str = Field("", description="The location of the lake")
    description: Optional[str] = Field(
        None, description="Description of the lake"
    )
    state: str = Field("", description="The state of the lake")
    metastore: Optional[Dict[str, Any]] = Field(
        None, description="Metastore configuration"
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
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "Lake":
        """Create a Lake from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new Lake instance
        """
        name = response.get("name", "")
        # name: projects/{p}/locations/{l}/lakes/{id}
        parts = name.split("/")
        lake_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        instance = cls(
            id=lake_id,
            name=name,
            type="dataplex.lake",
            project=project_id,
            location=location,
            description=response.get("description"),
            state=response.get("state", ""),
            metastore=response.get("metastore"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class Zone(GCPResource):
    """Model for a Google Cloud Dataplex Zone."""

    lake_name: str = Field("", description="The parent lake name")
    location: str = Field("", description="The location of the zone")
    type_field: str = Field(
        "", description="Zone type (RAW or CURATED)"
    )
    description: Optional[str] = Field(
        None, description="Description of the zone"
    )
    state: str = Field("", description="The state of the zone")
    discovery_spec: Optional[Dict[str, Any]] = Field(
        None, description="Discovery specification"
    )
    resource_spec: Optional[Dict[str, Any]] = Field(
        None, description="Resource specification"
    )

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "Zone":
        """Create a Zone from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new Zone instance
        """
        name = response.get("name", "")
        # name: projects/{p}/locations/{l}/lakes/{lake}/zones/{id}
        parts = name.split("/")
        zone_id = parts[-1] if len(parts) >= 8 else ""
        lake_name = parts[5] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        return cls(
            id=zone_id,
            name=name,
            type="dataplex.zone",
            project=project_id,
            lake_name=lake_name,
            location=location,
            type_field=response.get("type", ""),
            description=response.get("description"),
            state=response.get("state", ""),
            discovery_spec=response.get("discoverySpec"),
            resource_spec=response.get("resourceSpec"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )


class Asset(GCPResource):
    """Model for a Google Cloud Dataplex Asset."""

    zone_name: str = Field("", description="The parent zone name")
    lake_name: str = Field("", description="The parent lake name")
    location: str = Field("", description="The location of the asset")
    resource_spec: Dict[str, Any] = Field(
        default_factory=dict, description="Resource specification"
    )
    discovery_spec: Optional[Dict[str, Any]] = Field(
        None, description="Discovery specification"
    )
    state: str = Field("", description="The state of the asset")

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "Asset":
        """Create an Asset from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new Asset instance
        """
        name = response.get("name", "")
        # name: projects/{p}/locations/{l}/lakes/{lake}/zones/{zone}/assets/{id}
        parts = name.split("/")
        asset_id = parts[-1] if len(parts) >= 10 else ""
        zone_name = parts[7] if len(parts) >= 8 else ""
        lake_name = parts[5] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id:
            project_id = parts[1] if len(parts) >= 2 else ""

        return cls(
            id=asset_id,
            name=name,
            type="dataplex.asset",
            project=project_id,
            zone_name=zone_name,
            lake_name=lake_name,
            location=location,
            resource_spec=response.get("resourceSpec", {}),
            discovery_spec=response.get("discoverySpec"),
            state=response.get("state", ""),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
