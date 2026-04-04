"""JSON Schema definitions for Google Cloud Document AI resources."""

from typing import Dict, Any


PROCESSOR_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Document AI Processor",
    "description": "Schema for Google Cloud Document AI processors",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string", "description": "Full resource name of the processor"},
        "displayName": {"type": "string", "description": "Display name of the processor"},
        "type": {"type": "string", "description": "The processor type"},
        "state": {
            "type": "string",
            "description": "The state of the processor",
            "enum": ["STATE_UNSPECIFIED", "ENABLED", "DISABLED", "ENABLING", "DISABLING", "CREATING", "FAILED", "DELETING"],
        },
        "defaultProcessorVersion": {
            "type": "string",
            "description": "The default processor version resource name",
        },
        "createTime": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
        "updateTime": {"type": "string", "format": "date-time", "description": "Last update timestamp"},
        "labels": {
            "type": "object",
            "description": "Labels associated with the processor",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

PROCESSOR_VERSION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Document AI Processor Version",
    "description": "Schema for Google Cloud Document AI processor versions",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string", "description": "Full resource name of the processor version"},
        "displayName": {"type": "string", "description": "Display name of the processor version"},
        "state": {
            "type": "string",
            "description": "The state of the processor version",
            "enum": ["STATE_UNSPECIFIED", "DEPLOYED", "DEPLOYING", "UNDEPLOYED", "UNDEPLOYING", "CREATING", "DELETING", "FAILED"],
        },
        "createTime": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
        "updateTime": {"type": "string", "format": "date-time", "description": "Last update timestamp"},
    },
    "additionalProperties": False,
}

PROCESS_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Document AI Process Result",
    "description": "Schema for Google Cloud Document AI process results",
    "type": "object",
    "required": [],
    "properties": {
        "document": {
            "type": "object",
            "description": "The document result from processing",
        },
        "humanReviewStatus": {
            "type": "object",
            "description": "The status of human review on the processed document",
            "properties": {
                "state": {"type": "string"},
                "stateMessage": {"type": "string"},
                "humanReviewOperation": {"type": "string"},
            },
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "processor") -> Dict[str, Any]:
    """Get the JSON schema for a specific Document AI resource type.

    Args:
        resource_type: The type of resource ("processor", "processor_version", "process_result")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "processor": PROCESSOR_SCHEMA,
        "processor_version": PROCESSOR_VERSION_SCHEMA,
        "process_result": PROCESS_RESULT_SCHEMA,
    }
    return schemas.get(resource_type.lower(), PROCESSOR_SCHEMA)
