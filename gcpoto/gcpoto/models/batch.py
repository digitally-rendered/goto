"""Models for Google Cloud Batch resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource


class BatchJob(GCPResource):
    """Model for a Google Cloud Batch Job."""

    location: str = Field("", description="The location of the job")
    status: Dict[str, Any] = Field(
        default_factory=dict, description="Current status of the job"
    )
    task_groups: List[Dict[str, Any]] = Field(
        default_factory=list, description="Task groups for the job"
    )
    allocation_policy: Optional[Dict[str, Any]] = Field(
        None, description="Compute resource allocation policy"
    )
    scheduling_policy: Optional[Dict[str, Any]] = Field(
        None, description="Scheduling policy for task execution"
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
    ) -> "BatchJob":
        """Create a BatchJob from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new BatchJob instance
        """
        full_name = response.get("name", "")
        job_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID and location from the name
        # Format: projects/{project}/locations/{location}/jobs/{job}
        location = ""
        if full_name:
            parts = full_name.split("/")
            if len(parts) >= 4:
                if not project_id:
                    project_id = parts[1]
                location = parts[3]

        instance = cls(
            id=full_name,
            name=job_name,
            type="batch.job",
            project=project_id,
            location=location,
            status=response.get("status", {}),
            task_groups=response.get("taskGroups", []),
            allocation_policy=response.get("allocationPolicy"),
            scheduling_policy=response.get("schedulingPolicy"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class BatchTask(GCPResource):
    """Model for a Google Cloud Batch Task."""

    job_name: str = Field(
        "", description="The name of the job this task belongs to"
    )
    task_group: str = Field(
        "", description="The task group this task belongs to"
    )
    status: Dict[str, Any] = Field(
        default_factory=dict, description="Current status of the task"
    )

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "BatchTask":
        """Create a BatchTask from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new BatchTask instance
        """
        full_name = response.get("name", "")
        task_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID, location, job, and task group from the name
        # Format: projects/{project}/locations/{location}/jobs/{job}/taskGroups/{group}/tasks/{task}
        location = ""
        job_name = ""
        task_group = ""
        if full_name:
            parts = full_name.split("/")
            if len(parts) >= 8:
                if not project_id:
                    project_id = parts[1]
                location = parts[3]
                job_name = parts[5]
                task_group = parts[7]

        instance = cls(
            id=full_name,
            name=task_name,
            type="batch.task",
            project=project_id,
            job_name=job_name,
            task_group=task_group,
            status=response.get("status", {}),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        return instance
