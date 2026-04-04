"""Models for Google Cloud Run resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource


class CloudRunService(GCPResource):
    """Model for a Google Cloud Run Service."""

    location: str = Field("", description="The location/region of the service")
    description: Optional[str] = Field(
        None, description="User-provided description of the service"
    )
    uri: Optional[str] = Field(
        None, description="The main URI in which this service is serving traffic"
    )
    ingress: Optional[str] = Field(
        None,
        description="Ingress settings for the service (e.g. INGRESS_TRAFFIC_ALL)",
    )
    launch_stage: Optional[str] = Field(
        None, description="The launch stage (e.g. GA, BETA, ALPHA)"
    )
    template: Optional[Dict[str, Any]] = Field(
        None, description="The template used to create revisions for this service"
    )
    traffic: Optional[List[Dict[str, Any]]] = Field(
        None, description="Specifies how to distribute traffic over revisions"
    )
    conditions: Optional[List[Dict[str, Any]]] = Field(
        None, description="The conditions of the service"
    )
    latest_ready_revision: Optional[str] = Field(
        None, description="Name of the latest revision that is serving traffic"
    )
    latest_created_revision: Optional[str] = Field(
        None, description="Name of the last created revision"
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
    ) -> "CloudRunService":
        """Create a CloudRunService from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new CloudRunService instance
        """
        full_name = response.get("name", "")
        # name format: projects/{project}/locations/{location}/services/{service}
        parts = full_name.split("/") if full_name else []

        service_name = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id and len(parts) >= 2:
            project_id = parts[1]

        instance = cls(
            id=full_name,
            name=service_name,
            type="run.service",
            project=project_id,
            location=location,
            labels=response.get("labels"),
            description=response.get("description"),
            uri=response.get("uri"),
            ingress=response.get("ingress"),
            launch_stage=response.get("launchStage"),
            template=response.get("template"),
            traffic=response.get("traffic"),
            conditions=response.get("conditions"),
            latest_ready_revision=response.get("latestReadyRevision"),
            latest_created_revision=response.get("latestCreatedRevision"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class CloudRunRevision(GCPResource):
    """Model for a Google Cloud Run Revision."""

    service_name: str = Field(
        "", description="The name of the parent Cloud Run service"
    )
    location: str = Field("", description="The location/region of the revision")
    generation: Optional[int] = Field(
        None, description="A number that monotonically increases every time the user modifies the desired state"
    )
    containers: Optional[List[Dict[str, Any]]] = Field(
        None, description="Holds the single container that defines the unit of execution"
    )
    scaling: Optional[Dict[str, Any]] = Field(
        None, description="Scaling settings for the revision"
    )
    service_account: Optional[str] = Field(
        None, description="Email address of the IAM service account"
    )
    conditions: Optional[List[Dict[str, Any]]] = Field(
        None, description="The conditions of the revision"
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
    ) -> "CloudRunRevision":
        """Create a CloudRunRevision from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new CloudRunRevision instance
        """
        full_name = response.get("name", "")
        # name format: projects/{project}/locations/{location}/services/{service}/revisions/{revision}
        parts = full_name.split("/") if full_name else []

        revision_name = parts[-1] if len(parts) >= 8 else ""
        service_name = parts[5] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id and len(parts) >= 2:
            project_id = parts[1]

        instance = cls(
            id=full_name,
            name=revision_name,
            type="run.revision",
            project=project_id,
            service_name=service_name,
            location=location,
            labels=response.get("labels"),
            generation=response.get("generation"),
            containers=response.get("containers"),
            scaling=response.get("scaling"),
            service_account=response.get("serviceAccount"),
            conditions=response.get("conditions"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
