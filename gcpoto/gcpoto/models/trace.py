"""Models for Google Cloud Trace resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class Trace(GCPResource):
    """Model for a Google Cloud Trace."""

    trace_id: str = Field("", description="The unique trace identifier")
    spans: List[Dict[str, Any]] = Field(
        default_factory=list, description="The collection of spans in this trace"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Trace":
        """Create a Trace from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Trace instance
        """
        trace_id = response.get("traceId", "")

        # Extract project from spans if available
        project_id = ""
        spans = response.get("spans", [])
        if spans:
            span_name = spans[0].get("name", "")
            if "/" in span_name:
                parts = span_name.split("/")
                if len(parts) >= 2:
                    project_id = parts[1]

        return cls(
            id=trace_id,
            name=trace_id,
            type="cloudtrace.trace",
            project=project_id,
            trace_id=trace_id,
            spans=spans,
        )


class TraceSpan(GCPResource):
    """Model for a Google Cloud Trace span."""

    trace_id: str = Field("", description="The trace ID this span belongs to")
    span_id: str = Field("", description="The unique span identifier")
    parent_span_id: Optional[str] = Field(
        None, description="The parent span ID"
    )
    display_name: str = Field("", description="A description of the span")
    start_time: Optional[datetime] = Field(
        None, description="The start time of the span"
    )
    end_time: Optional[datetime] = Field(
        None, description="The end time of the span"
    )
    status: Optional[Dict[str, Any]] = Field(
        None, description="The status of the span"
    )
    attributes: Optional[Dict[str, Any]] = Field(
        None, description="A set of attributes on the span"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "TraceSpan":
        """Create a TraceSpan from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new TraceSpan instance
        """
        full_name = response.get("name", "")
        span_id = response.get("spanId", "")

        # Extract project and trace_id from name:
        # projects/{project}/traces/{trace_id}/spans/{span_id}
        project_id = ""
        trace_id = ""
        if "/" in full_name:
            parts = full_name.split("/")
            if len(parts) >= 4:
                project_id = parts[1]
                trace_id = parts[3]

        # Handle displayName which may be a TruncatedString
        display_name_val = response.get("displayName", "")
        if isinstance(display_name_val, dict):
            display_name_val = display_name_val.get("value", "")

        return cls(
            id=span_id or full_name,
            name=full_name,
            type="cloudtrace.span",
            project=project_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=response.get("parentSpanId"),
            display_name=display_name_val,
            start_time=response.get("startTime"),
            end_time=response.get("endTime"),
            status=response.get("status"),
            attributes=response.get("attributes"),
        )
