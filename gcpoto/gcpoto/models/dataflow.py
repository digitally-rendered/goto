"""Models for Google Cloud Dataflow resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource


class DataflowJob(GCPResource):
    """Model for a Google Cloud Dataflow Job."""

    location: str = Field("", description="The location of the job")
    job_type: str = Field(
        "",
        description="The type of job (JOB_TYPE_BATCH or JOB_TYPE_STREAMING)",
    )
    current_state: str = Field(
        "", description="The current state of the job"
    )
    create_time: Optional[datetime] = Field(
        None, description="The time the job was created"
    )
    start_time: Optional[datetime] = Field(
        None, description="The time the job was started"
    )
    requested_state: Optional[str] = Field(
        None, description="The requested state of the job"
    )
    pipeline_description: Optional[Dict[str, Any]] = Field(
        None, description="Description of the pipeline"
    )
    stage_states: Optional[List[Dict[str, Any]]] = Field(
        None, description="Information about the stages of the pipeline"
    )
    environment: Optional[Dict[str, Any]] = Field(
        None, description="The environment configuration for the job"
    )
    sdk_pipeline_options: Optional[Dict[str, Any]] = Field(
        None, description="SDK pipeline options for the job"
    )
    temp_files: Optional[List[str]] = Field(
        None, description="Temporary files used by the job"
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
    ) -> "DataflowJob":
        """Create a DataflowJob from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from response if not provided)

        Returns:
            A new DataflowJob instance
        """
        job_id = response.get("id", "")
        job_name = response.get("name", "")

        if not project_id:
            project_id = response.get("projectId", "")

        location = response.get("location", "")

        instance = cls(
            id=job_id,
            name=job_name,
            type="dataflow.job",
            project=project_id,
            location=location,
            job_type=response.get("type", ""),
            current_state=response.get("currentState", ""),
            create_time=response.get("createTime"),
            start_time=response.get("startTime"),
            requested_state=response.get("requestedState"),
            pipeline_description=response.get("pipelineDescription"),
            stage_states=response.get("stageStates"),
            environment=response.get("environment"),
            sdk_pipeline_options=response.get("sdkPipelineOptions"),
            temp_files=response.get("tempFiles"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("currentStateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class DataflowTemplate(GCPResource):
    """Model for a Google Cloud Dataflow Template."""

    location: str = Field("", description="The location of the template")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Metadata about the template"
    )
    runtime_parameters: Optional[Dict[str, Any]] = Field(
        None, description="Runtime parameters for the template"
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
    ) -> "DataflowTemplate":
        """Create a DataflowTemplate from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new DataflowTemplate instance
        """
        # Template launch responses contain a nested job
        job = response.get("job", {})
        template_name = job.get("name", response.get("name", ""))
        job_id = job.get("id", response.get("id", ""))

        if not project_id:
            project_id = job.get("projectId", response.get("projectId", ""))

        location = job.get("location", response.get("location", ""))

        instance = cls(
            id=job_id,
            name=template_name,
            type="dataflow.template",
            project=project_id,
            location=location,
            metadata=response.get("metadata"),
            runtime_parameters=response.get("runtimeParameters"),
            labels=job.get("labels", response.get("labels")),
            created=job.get("createTime", response.get("createTime")),
            updated=job.get("currentStateTime", response.get("updateTime")),
        )

        labels = job.get("labels", response.get("labels"))
        if labels:
            instance._tags = labels

        return instance
