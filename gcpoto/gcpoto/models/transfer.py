"""Models for Google Cloud Storage Transfer Service resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.transfer import get_schema


class TransferJob(GCPResource):
    """Model for a Google Cloud Storage Transfer Job."""

    description: Optional[str] = Field(
        None, description="A description of the transfer job"
    )
    status: str = Field(
        "",
        description="The status of the transfer job (ENABLED, DISABLED, DELETED)",
    )
    schedule: Optional[Dict[str, Any]] = Field(
        None, description="The schedule for the transfer job"
    )
    transfer_spec: Dict[str, Any] = Field(
        default_factory=dict,
        description="The transfer specification",
    )
    notification_config: Optional[Dict[str, Any]] = Field(
        None, description="Notification configuration for the transfer job"
    )
    latest_operation_name: Optional[str] = Field(
        None, description="The name of the latest transfer operation"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("transfer_job")}

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
    ) -> "TransferJob":
        """Create a TransferJob from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new TransferJob instance
        """
        full_name = response.get("name", "")
        # Format: transferJobs/{jobId}
        job_name = full_name.split("/")[-1] if "/" in full_name else full_name

        if not project_id:
            project_id = response.get("projectId", "")

        instance = cls(
            id=full_name,
            name=job_name,
            type="storagetransfer.transferJob",
            project=project_id,
            labels=response.get("labels"),
            description=response.get("description"),
            status=response.get("status", ""),
            schedule=response.get("schedule"),
            transfer_spec=response.get("transferSpec", {}),
            notification_config=response.get("notificationConfig"),
            latest_operation_name=response.get("latestOperationName"),
            created=response.get("creationTime"),
            updated=response.get("lastModificationTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class TransferOperation(GCPResource):
    """Model for a Google Cloud Storage Transfer Operation."""

    transfer_job_name: str = Field(
        "", description="The name of the transfer job this operation belongs to"
    )
    status: str = Field(
        "", description="The status of the transfer operation"
    )
    start_time: Optional[datetime] = Field(
        None, description="The start time of the operation"
    )
    end_time: Optional[datetime] = Field(
        None, description="The end time of the operation"
    )
    counters: Optional[Dict[str, Any]] = Field(
        None, description="Transfer counters for the operation"
    )
    error_breakdowns: Optional[List[Dict[str, Any]]] = Field(
        None, description="Error breakdowns for the operation"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("transfer_operation")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "TransferOperation":
        """Create a TransferOperation from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new TransferOperation instance
        """
        full_name = response.get("name", "")
        op_name = full_name.split("/")[-1] if "/" in full_name else full_name

        metadata = response.get("metadata", {})

        if not project_id:
            project_id = metadata.get("projectId", "")

        return cls(
            id=full_name,
            name=op_name,
            type="storagetransfer.transferOperation",
            project=project_id,
            transfer_job_name=metadata.get("transferJobName", ""),
            status=metadata.get("status", ""),
            start_time=metadata.get("startTime"),
            end_time=metadata.get("endTime"),
            counters=metadata.get("counters"),
            error_breakdowns=metadata.get("errorBreakdowns"),
        )
