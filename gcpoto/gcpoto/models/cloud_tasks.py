"""Models for Google Cloud Tasks resources."""

from datetime import datetime
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource


class TaskQueue(GCPResource):
    """Model for a Google Cloud Tasks Queue."""

    location: str = Field("", description="The location of the queue")
    rate_limits: Optional[Dict[str, Any]] = Field(
        None, description="Rate limits for task dispatches from this queue"
    )
    retry_config: Optional[Dict[str, Any]] = Field(
        None, description="Retry configuration for tasks in this queue"
    )
    state: str = Field(
        "RUNNING",
        description="The state of the queue (RUNNING, PAUSED, or DISABLED)",
    )
    purge_time: Optional[datetime] = Field(
        None, description="The last time this queue was purged"
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
    ) -> "TaskQueue":
        """Create a TaskQueue from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new TaskQueue instance
        """
        full_name = response.get("name", "")
        queue_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID and location from the name if not provided
        # Format: projects/{project}/locations/{location}/queues/{queue}
        location = ""
        if full_name:
            parts = full_name.split("/")
            if len(parts) >= 4:
                if not project_id:
                    project_id = parts[1]
                location = parts[3]

        instance = cls(
            id=full_name,
            name=queue_name,
            type="cloudtasks.queue",
            project=project_id,
            location=location,
            rate_limits=response.get("rateLimits"),
            retry_config=response.get("retryConfig"),
            state=response.get("state", "RUNNING"),
            purge_time=response.get("purgeTime"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class Task(GCPResource):
    """Model for a Google Cloud Tasks Task."""

    queue_name: str = Field("", description="The name of the queue this task belongs to")
    location: str = Field("", description="The location of the task's queue")
    schedule_time: Optional[datetime] = Field(
        None, description="The time when the task is scheduled to be attempted"
    )
    create_time: Optional[datetime] = Field(
        None, description="The time that the task was created"
    )
    dispatch_deadline: Optional[str] = Field(
        None,
        description="The deadline for requests sent to the worker",
    )
    dispatch_count: int = Field(
        0, description="The number of attempts dispatched"
    )
    response_count: int = Field(
        0, description="The number of attempts which have received a response"
    )
    first_attempt: Optional[Dict[str, Any]] = Field(
        None, description="Information about the first attempt"
    )
    last_attempt: Optional[Dict[str, Any]] = Field(
        None, description="Information about the most recent attempt"
    )
    http_request: Optional[Dict[str, Any]] = Field(
        None, description="HTTP request for the task"
    )
    app_engine_http_request: Optional[Dict[str, Any]] = Field(
        None, description="App Engine HTTP request for the task"
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
    ) -> "Task":
        """Create a Task from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new Task instance
        """
        full_name = response.get("name", "")
        task_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID, location, and queue from the name
        # Format: projects/{project}/locations/{location}/queues/{queue}/tasks/{task}
        location = ""
        queue_name = ""
        if full_name:
            parts = full_name.split("/")
            if len(parts) >= 6:
                if not project_id:
                    project_id = parts[1]
                location = parts[3]
                queue_name = parts[5]

        instance = cls(
            id=full_name,
            name=task_name,
            type="cloudtasks.task",
            project=project_id,
            queue_name=queue_name,
            location=location,
            schedule_time=response.get("scheduleTime"),
            create_time=response.get("createTime"),
            dispatch_deadline=response.get("dispatchDeadline"),
            dispatch_count=response.get("dispatchCount", 0),
            response_count=response.get("responseCount", 0),
            first_attempt=response.get("firstAttempt"),
            last_attempt=response.get("lastAttempt"),
            http_request=response.get("httpRequest"),
            app_engine_http_request=response.get("appEngineHttpRequest"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
