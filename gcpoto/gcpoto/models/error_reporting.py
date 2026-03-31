"""Models for Google Cloud Error Reporting resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class ErrorGroup(GCPResource):
    """Model for a Google Cloud Error Reporting error group."""

    group_id: str = Field("", description="The unique group identifier")
    tracking_issues: Optional[List[Dict[str, Any]]] = Field(
        None, description="Associated tracking issues (e.g., bug tracker links)"
    )
    resolution_status: Optional[str] = Field(
        None,
        description="The resolution status of the group (OPEN, ACKNOWLEDGED, RESOLVED, MUTED)",
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "ErrorGroup":
        """Create an ErrorGroup from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ErrorGroup instance
        """
        full_name = response.get("name", "")
        group_id = response.get("groupId", "")

        # Extract project from name:
        # projects/{project}/groups/{group_id}
        project_id = ""
        if "/" in full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        return cls(
            id=group_id or full_name,
            name=full_name,
            type="clouderrorreporting.errorGroup",
            project=project_id,
            group_id=group_id,
            tracking_issues=response.get("trackingIssues"),
            resolution_status=response.get("resolutionStatus"),
        )


class ErrorEvent(GCPResource):
    """Model for a Google Cloud Error Reporting error event."""

    group_id: str = Field("", description="The group this event belongs to")
    service_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="The service context in which the error occurred",
    )
    message: str = Field("", description="The error message")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for the error"
    )
    event_time: Optional[datetime] = Field(
        None, description="The time the error event occurred"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "ErrorEvent":
        """Create an ErrorEvent from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ErrorEvent instance
        """
        # Extract group_id from the event
        group_id = ""
        if response.get("group"):
            group_id = response["group"].get("groupId", "")

        # Extract service context
        service_context = response.get("serviceContext", {})

        # Extract project from serviceContext or context
        project_id = service_context.get("resourceContainer", "")
        if not project_id and response.get("context"):
            report_location = response["context"].get("reportLocation", {})
            project_id = report_location.get("filePath", "").split("/")[0] if report_location else ""

        # Use eventTime as event identifier
        event_time = response.get("eventTime")
        event_id = response.get("eventId", event_time or "")

        return cls(
            id=str(event_id),
            name=str(event_id),
            type="clouderrorreporting.errorEvent",
            project=project_id,
            group_id=group_id,
            service_context=service_context,
            message=response.get("message", ""),
            context=response.get("context"),
            event_time=event_time,
        )
