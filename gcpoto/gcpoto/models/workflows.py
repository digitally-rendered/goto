"""Models for Google Cloud Workflows resources."""

from datetime import datetime
from typing import Dict, Optional, Any
from pydantic import Field

from gcpoto.models.base import GCPResource


class Workflow(GCPResource):
    """Model for a Google Cloud Workflow."""

    location: str = Field("", description="The location of the workflow")
    description: Optional[str] = Field(
        None, description="Description of the workflow"
    )
    state: str = Field(
        "ACTIVE", description="The state of the workflow (ACTIVE or unavailable)"
    )
    revision_id: Optional[str] = Field(
        None, description="The revision of the workflow"
    )
    source_contents: Optional[str] = Field(
        None, description="The workflow source code (YAML or JSON)"
    )
    service_account: Optional[str] = Field(
        None,
        description="The IAM service account associated with the workflow",
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
    ) -> "Workflow":
        """Create a Workflow from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new Workflow instance
        """
        full_name = response.get("name", "")
        workflow_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID and location from the name
        # Format: projects/{project}/locations/{location}/workflows/{workflow}
        location = ""
        if full_name:
            parts = full_name.split("/")
            if len(parts) >= 4:
                if not project_id:
                    project_id = parts[1]
                location = parts[3]

        instance = cls(
            id=full_name,
            name=workflow_name,
            type="workflows.workflow",
            project=project_id,
            location=location,
            description=response.get("description"),
            state=response.get("state", "ACTIVE"),
            revision_id=response.get("revisionId"),
            source_contents=response.get("sourceContents"),
            service_account=response.get("serviceAccount"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class WorkflowExecution(GCPResource):
    """Model for a Google Cloud Workflow Execution."""

    workflow_name: str = Field(
        "", description="The name of the workflow this execution belongs to"
    )
    location: str = Field(
        "", description="The location of the workflow"
    )
    state: str = Field(
        "ACTIVE",
        description="The state of the execution (ACTIVE, SUCCEEDED, FAILED, CANCELLED)",
    )
    argument: Optional[str] = Field(
        None, description="The argument passed to the workflow execution"
    )
    result: Optional[str] = Field(
        None, description="The result of the workflow execution"
    )
    error: Optional[Dict[str, Any]] = Field(
        None, description="Error information if the execution failed"
    )
    start_time: Optional[datetime] = Field(
        None, description="The time the execution started"
    )
    end_time: Optional[datetime] = Field(
        None, description="The time the execution ended"
    )
    call_log_level: Optional[str] = Field(
        None, description="The call logging level for the execution"
    )

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "WorkflowExecution":
        """Create a WorkflowExecution from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new WorkflowExecution instance
        """
        full_name = response.get("name", "")
        execution_name = full_name.split("/")[-1] if full_name else ""

        # Extract project ID, location, and workflow from the name
        # Format: projects/{project}/locations/{location}/workflows/{workflow}/executions/{execution}
        location = ""
        workflow_name = ""
        if full_name:
            parts = full_name.split("/")
            if len(parts) >= 6:
                if not project_id:
                    project_id = parts[1]
                location = parts[3]
                workflow_name = parts[5]

        instance = cls(
            id=full_name,
            name=execution_name,
            type="workflows.execution",
            project=project_id,
            workflow_name=workflow_name,
            location=location,
            state=response.get("state", "ACTIVE"),
            argument=response.get("argument"),
            result=response.get("result"),
            error=response.get("error"),
            start_time=response.get("startTime"),
            end_time=response.get("endTime"),
            call_log_level=response.get("callLogLevel"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        return instance
