"""JSON Schema definitions for Google Cloud Trace resources."""

from typing import Dict, Any

# JSON Schema for Cloud Trace
TRACE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Trace",
    "description": "Schema for Google Cloud Trace traces",
    "type": "object",
    "required": ["traceId"],
    "properties": {
        "traceId": {
            "type": "string",
            "description": "The unique trace identifier",
        },
        "spans": {
            "type": "array",
            "description": "The collection of spans in this trace",
            "items": {"type": "object"},
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Trace Span
TRACE_SPAN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Trace Span",
    "description": "Schema for Google Cloud Trace spans",
    "type": "object",
    "required": ["spanId", "displayName"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the span",
        },
        "spanId": {
            "type": "string",
            "description": "The unique span identifier within a trace",
        },
        "parentSpanId": {
            "type": "string",
            "description": "The span ID of the parent span",
        },
        "displayName": {
            "type": ["string", "object"],
            "description": "A description of the span's operation",
        },
        "startTime": {
            "type": "string",
            "format": "date-time",
            "description": "The start time of the span",
        },
        "endTime": {
            "type": "string",
            "format": "date-time",
            "description": "The end time of the span",
        },
        "status": {
            "type": "object",
            "description": "The status of the span",
            "properties": {
                "code": {
                    "type": "integer",
                    "description": "The status code",
                },
                "message": {
                    "type": "string",
                    "description": "A developer-facing error message",
                },
            },
        },
        "attributes": {
            "type": "object",
            "description": "A set of attributes on the span",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "trace") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud Trace resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("trace" or "span")

    Returns:
        The JSON schema for the specified resource type
    """
    resource_type_lower = resource_type.lower()
    if resource_type_lower == "span":
        return TRACE_SPAN_SCHEMA
    else:
        return TRACE_SCHEMA
