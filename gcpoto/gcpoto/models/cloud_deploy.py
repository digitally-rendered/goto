"""Models for Google Cloud Deploy resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource


class DeliveryPipeline(GCPResource):
    """Model for a Google Cloud Deploy Delivery Pipeline."""

    location: str = Field("", description="The location of the pipeline")
    description: Optional[str] = Field(
        None, description="Description of the delivery pipeline"
    )
    serial_pipeline: Optional[Dict[str, Any]] = Field(
        None, description="SerialPipeline defines a sequential set of stages"
    )
    condition: Optional[Dict[str, Any]] = Field(
        None, description="Output only pipeline condition information"
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
    ) -> "DeliveryPipeline":
        """Create a DeliveryPipeline from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new DeliveryPipeline instance
        """
        full_name = response.get("name", "")
        pipeline_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID and location from the name
        # Format: projects/{project}/locations/{location}/deliveryPipelines/{pipeline}
        location = ""
        if full_name:
            parts = full_name.split("/")
            if len(parts) >= 4:
                if not project_id:
                    project_id = parts[1]
                location = parts[3]

        instance = cls(
            id=full_name,
            name=pipeline_name,
            type="clouddeploy.deliveryPipeline",
            project=project_id,
            location=location,
            description=response.get("description"),
            serial_pipeline=response.get("serialPipeline"),
            condition=response.get("condition"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class Release(GCPResource):
    """Model for a Google Cloud Deploy Release."""

    pipeline_name: str = Field(
        "", description="The name of the delivery pipeline"
    )
    location: str = Field("", description="The location of the release")
    description: Optional[str] = Field(
        None, description="Description of the release"
    )
    skaffold_config_uri: Optional[str] = Field(
        None, description="Cloud Storage URI of the skaffold configuration"
    )
    skaffold_config_path: Optional[str] = Field(
        None, description="Filepath of the skaffold configuration"
    )
    render_state: Optional[str] = Field(
        None, description="Current state of the render operation"
    )
    delivery_pipeline_snapshot: Optional[Dict[str, Any]] = Field(
        None, description="Snapshot of the delivery pipeline at release time"
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
    ) -> "Release":
        """Create a Release from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new Release instance
        """
        full_name = response.get("name", "")
        release_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID, location, and pipeline from the name
        # Format: projects/{project}/locations/{location}/deliveryPipelines/{pipeline}/releases/{release}
        location = ""
        pipeline_name = ""
        if full_name:
            parts = full_name.split("/")
            if len(parts) >= 6:
                if not project_id:
                    project_id = parts[1]
                location = parts[3]
                pipeline_name = parts[5]

        instance = cls(
            id=full_name,
            name=release_name,
            type="clouddeploy.release",
            project=project_id,
            pipeline_name=pipeline_name,
            location=location,
            description=response.get("description"),
            skaffold_config_uri=response.get("skaffoldConfigUri"),
            skaffold_config_path=response.get("skaffoldConfigPath"),
            render_state=response.get("renderState"),
            delivery_pipeline_snapshot=response.get("deliveryPipelineSnapshot"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class Rollout(GCPResource):
    """Model for a Google Cloud Deploy Rollout."""

    release_name: str = Field(
        "", description="The name of the release this rollout belongs to"
    )
    pipeline_name: str = Field(
        "", description="The name of the delivery pipeline"
    )
    location: str = Field("", description="The location of the rollout")
    target_id: str = Field("", description="The target to which this rollout deploys")
    state: str = Field("", description="Current state of the rollout")
    deploy_start_time: Optional[datetime] = Field(
        None, description="Time at which the rollout deploy started"
    )
    deploy_end_time: Optional[datetime] = Field(
        None, description="Time at which the rollout deploy finished"
    )

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "Rollout":
        """Create a Rollout from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new Rollout instance
        """
        full_name = response.get("name", "")
        rollout_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID, location, pipeline, and release from the name
        # Format: projects/{project}/locations/{location}/deliveryPipelines/{pipeline}/releases/{release}/rollouts/{rollout}
        location = ""
        pipeline_name = ""
        release_name = ""
        if full_name:
            parts = full_name.split("/")
            if len(parts) >= 8:
                if not project_id:
                    project_id = parts[1]
                location = parts[3]
                pipeline_name = parts[5]
                release_name = parts[7]

        instance = cls(
            id=full_name,
            name=rollout_name,
            type="clouddeploy.rollout",
            project=project_id,
            release_name=release_name,
            pipeline_name=pipeline_name,
            location=location,
            target_id=response.get("targetId", ""),
            state=response.get("state", ""),
            deploy_start_time=response.get("deployStartTime"),
            deploy_end_time=response.get("deployEndTime"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        return instance
