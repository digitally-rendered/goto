"""JSON Schema definitions for Security Command Center resources."""

from typing import Dict, Any


FINDING_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Security Command Center Finding",
    "description": "Schema for Security Command Center Findings",
    "type": "object",
    "required": ["name", "category"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The relative resource name of the finding",
        },
        "category": {
            "type": "string",
            "description": "The category of the finding",
        },
        "state": {
            "type": "string",
            "description": "The state of the finding",
            "enum": ["ACTIVE", "INACTIVE"],
        },
        "severity": {
            "type": "string",
            "description": "The severity of the finding",
            "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        },
        "sourceProperties": {
            "type": "object",
            "description": "Source-specific properties",
            "additionalProperties": True,
        },
        "securityMarks": {
            "type": "object",
            "description": "Security marks on the finding",
            "properties": {
                "marks": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
        },
        "eventTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the finding was first detected",
        },
        "resourceName": {
            "type": "string",
            "description": "The full resource name of the affected resource",
        },
        "externalUri": {
            "type": "string",
            "description": "URI to an external page about the finding",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the finding",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the finding",
        },
    },
    "additionalProperties": False,
}

SOURCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Security Command Center Source",
    "description": "Schema for Security Command Center Sources",
    "type": "object",
    "required": ["name", "displayName"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The relative resource name of the source",
        },
        "displayName": {
            "type": "string",
            "description": "The display name of the source",
        },
        "description": {
            "type": "string",
            "description": "A description of the source",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "finding") -> Dict[str, Any]:
    """Get the JSON schema for a specific Security Command Center resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("finding" or "source")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "source":
        return SOURCE_SCHEMA
    else:
        return FINDING_SCHEMA
