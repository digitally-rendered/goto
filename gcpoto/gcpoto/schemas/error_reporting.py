"""JSON Schema definitions for Google Cloud Error Reporting resources."""

from typing import Dict, Any

# JSON Schema for Cloud Error Reporting Error Group
ERROR_GROUP_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Error Reporting Error Group",
    "description": "Schema for Google Cloud Error Reporting error groups",
    "type": "object",
    "required": ["groupId"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the error group",
        },
        "groupId": {
            "type": "string",
            "description": "The unique group identifier",
        },
        "trackingIssues": {
            "type": "array",
            "description": "Associated tracking issues",
            "items": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the tracking issue",
                    },
                },
            },
        },
        "resolutionStatus": {
            "type": "string",
            "description": "The resolution status of the group",
            "enum": ["OPEN", "ACKNOWLEDGED", "RESOLVED", "MUTED"],
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Error Reporting Error Event
ERROR_EVENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Error Reporting Error Event",
    "description": "Schema for Google Cloud Error Reporting error events",
    "type": "object",
    "required": ["serviceContext", "message"],
    "properties": {
        "eventTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the event occurred",
        },
        "serviceContext": {
            "type": "object",
            "description": "The service context in which the error occurred",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "The service name",
                },
                "version": {
                    "type": "string",
                    "description": "The service version",
                },
                "resourceType": {
                    "type": "string",
                    "description": "The resource type",
                },
            },
        },
        "message": {
            "type": "string",
            "description": "The error message including stack trace",
        },
        "context": {
            "type": "object",
            "description": "Additional context about the error",
            "properties": {
                "httpRequest": {
                    "type": "object",
                    "description": "The HTTP request associated with the error",
                },
                "user": {
                    "type": "string",
                    "description": "The user affected by the error",
                },
                "reportLocation": {
                    "type": "object",
                    "description": "The source code location of the error",
                    "properties": {
                        "filePath": {
                            "type": "string",
                            "description": "The source file name",
                        },
                        "lineNumber": {
                            "type": "integer",
                            "description": "The line number",
                        },
                        "functionName": {
                            "type": "string",
                            "description": "The function name",
                        },
                    },
                },
            },
        },
        "group": {
            "type": "object",
            "description": "The error group this event belongs to",
            "properties": {
                "groupId": {
                    "type": "string",
                    "description": "The group identifier",
                },
            },
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "error_group") -> Dict[str, Any]:
    """Get the JSON schema for a specific Error Reporting resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("error_group" or "error_event")

    Returns:
        The JSON schema for the specified resource type
    """
    resource_type_lower = resource_type.lower()
    if resource_type_lower == "error_event":
        return ERROR_EVENT_SCHEMA
    else:
        return ERROR_GROUP_SCHEMA
