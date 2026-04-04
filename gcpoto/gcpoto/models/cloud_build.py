"""Models for Google Cloud Build resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource


class Build(GCPResource):
    """Model for a Google Cloud Build."""

    status: str = Field("", description="The status of the build")
    source: Optional[Dict[str, Any]] = Field(
        None, description="The source code to build"
    )
    steps: List[Dict[str, Any]] = Field(
        default_factory=list, description="The build steps"
    )
    results: Optional[Dict[str, Any]] = Field(
        None, description="Results of the build"
    )
    create_time: Optional[datetime] = Field(
        None, description="The time the build was created"
    )
    start_time: Optional[datetime] = Field(
        None, description="The time the build was started"
    )
    finish_time: Optional[datetime] = Field(
        None, description="The time the build finished"
    )
    timeout: Optional[str] = Field(
        None, description="Amount of time the build should be allowed to run"
    )
    images: Optional[List[str]] = Field(
        None, description="List of images expected to be built"
    )
    artifacts: Optional[Dict[str, Any]] = Field(
        None, description="Artifacts produced by the build"
    )
    logs_bucket: Optional[str] = Field(
        None, description="Cloud Storage bucket for build logs"
    )
    source_provenance: Optional[Dict[str, Any]] = Field(
        None, description="Provenance of the source"
    )
    options: Optional[Dict[str, Any]] = Field(
        None, description="Special options for this build"
    )
    substitutions: Optional[Dict[str, str]] = Field(
        None, description="Substitution variables for the build"
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
    ) -> "Build":
        """Create a Build from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from response if not provided)

        Returns:
            A new Build instance
        """
        build_id = response.get("id", "")
        build_name = response.get("name", build_id)

        if not project_id:
            project_id = response.get("projectId", "")

        instance = cls(
            id=build_id,
            name=build_name,
            type="cloudbuild.build",
            project=project_id,
            status=response.get("status", ""),
            source=response.get("source"),
            steps=response.get("steps", []),
            results=response.get("results"),
            create_time=response.get("createTime"),
            start_time=response.get("startTime"),
            finish_time=response.get("finishTime"),
            timeout=response.get("timeout"),
            images=response.get("images"),
            artifacts=response.get("artifacts"),
            logs_bucket=response.get("logsBucket"),
            source_provenance=response.get("sourceProvenance"),
            options=response.get("options"),
            substitutions=response.get("substitutions"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("finishTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class BuildTrigger(GCPResource):
    """Model for a Google Cloud Build Trigger."""

    description: Optional[str] = Field(
        None, description="Human-readable description of the trigger"
    )
    disabled: bool = Field(
        False, description="Whether the trigger is disabled"
    )
    substitutions: Optional[Dict[str, str]] = Field(
        None, description="Substitution variables for the trigger"
    )
    filename: Optional[str] = Field(
        None, description="Path to the build configuration file"
    )
    trigger_template: Optional[Dict[str, Any]] = Field(
        None, description="Template describing the types of source changes"
    )
    github: Optional[Dict[str, Any]] = Field(
        None, description="GitHub-specific trigger configuration"
    )
    pubsub_config: Optional[Dict[str, Any]] = Field(
        None, description="Pub/Sub configuration for the trigger"
    )
    webhook_config: Optional[Dict[str, Any]] = Field(
        None, description="Webhook configuration for the trigger"
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
    ) -> "BuildTrigger":
        """Create a BuildTrigger from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from response if not provided)

        Returns:
            A new BuildTrigger instance
        """
        trigger_id = response.get("id", "")
        trigger_name = response.get("name", "")

        if not project_id:
            project_id = response.get("projectId", "")

        instance = cls(
            id=trigger_id,
            name=trigger_name,
            type="cloudbuild.trigger",
            project=project_id,
            description=response.get("description"),
            disabled=response.get("disabled", False),
            substitutions=response.get("substitutions"),
            filename=response.get("filename"),
            trigger_template=response.get("triggerTemplate"),
            github=response.get("github"),
            pubsub_config=response.get("pubsubConfig"),
            webhook_config=response.get("webhookConfig"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
