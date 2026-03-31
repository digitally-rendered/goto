"""Models for Google Cloud Scheduler resources."""

from datetime import datetime
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.scheduler import get_schema


class SchedulerJob(GCPResource):
    """Model for a Google Cloud Scheduler Job."""

    location: str = Field("", description="The location (region) of the job")
    description: Optional[str] = Field(
        None, description="A human-readable description of the job"
    )
    schedule: str = Field("", description="Cron expression for the job schedule")
    time_zone: str = Field(
        "", description="The time zone for the cron schedule (e.g. America/New_York)"
    )
    state: str = Field(
        "ENABLED",
        description="The state of the job (ENABLED, PAUSED, DISABLED, UPDATE_FAILED)",
    )
    retry_config: Optional[Dict[str, Any]] = Field(
        None, description="Settings for retrying failed job attempts"
    )
    attempt_deadline: Optional[str] = Field(
        None,
        description="The deadline for job attempts (duration in seconds, e.g. '180s')",
    )
    http_target: Optional[Dict[str, Any]] = Field(
        None, description="HTTP target configuration for the job"
    )
    pubsub_target: Optional[Dict[str, Any]] = Field(
        None, description="Pub/Sub target configuration for the job"
    )
    app_engine_http_target: Optional[Dict[str, Any]] = Field(
        None, description="App Engine HTTP target configuration for the job"
    )
    last_attempt_time: Optional[datetime] = Field(
        None, description="The time the last job attempt started"
    )
    schedule_time: Optional[datetime] = Field(
        None, description="The next time the job is scheduled to run"
    )
    status: Optional[Dict[str, Any]] = Field(
        None, description="The status of the last execution attempt"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema()}

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
    ) -> "SchedulerJob":
        """Create a SchedulerJob from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new SchedulerJob instance
        """
        # The API returns the full name in the format:
        # projects/{project}/locations/{location}/jobs/{job}
        full_name = response.get("name", "")
        job_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID and location from the name if not provided
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
            type="scheduler.job",
            project=project_id,
            location=location,
            description=response.get("description"),
            schedule=response.get("schedule", ""),
            time_zone=response.get("timeZone", ""),
            state=response.get("state", "ENABLED"),
            retry_config=response.get("retryConfig"),
            attempt_deadline=response.get("attemptDeadline"),
            http_target=response.get("httpTarget"),
            pubsub_target=response.get("pubsubTarget"),
            app_engine_http_target=response.get("appEngineHttpTarget"),
            last_attempt_time=response.get("lastAttemptTime"),
            schedule_time=response.get("scheduleTime"),
            status=response.get("status"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
