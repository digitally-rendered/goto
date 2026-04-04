"""JSON Schema definitions for Google Cloud Workflows resources."""

from typing import Dict, Any

# JSON Schema for Workflows
WORKFLOW_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Workflow",
    "description": "Schema for Google Cloud Workflows",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified workflow name",
        },
        "description": {
            "type": "string",
            "description": "Description of the workflow",
        },
        "state": {
            "type": "string",
            "description": "The state of the workflow",
            "enum": ["STATE_UNSPECIFIED", "ACTIVE"],
        },
        "revisionId": {
            "type": "string",
            "description": "The revision of the workflow",
        },
        "sourceContents": {
            "type": "string",
            "description": "The workflow source code (YAML or JSON)",
        },
        "serviceAccount": {
            "type": "string",
            "description": "The IAM service account associated with the workflow",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the workflow",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the workflow was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last time the workflow was updated",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Workflow Executions
WORKFLOW_EXECUTION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Workflow Execution",
    "description": "Schema for Google Cloud Workflow Executions",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified execution name",
        },
        "state": {
            "type": "string",
            "description": "The state of the execution",
            "enum": [
                "STATE_UNSPECIFIED",
                "ACTIVE",
                "SUCCEEDED",
                "FAILED",
                "CANCELLED",
            ],
        },
        "argument": {
            "type": "string",
            "description": "The argument passed to the workflow execution",
        },
        "result": {
            "type": "string",
            "description": "The result of the workflow execution",
        },
        "error": {
            "type": "object",
            "description": "Error information if the execution failed",
            "properties": {
                "payload": {
                    "type": "string",
                    "description": "Error payload",
                },
                "context": {
                    "type": "string",
                    "description": "Error context",
                },
                "stackTrace": {
                    "type": "object",
                    "description": "Stack trace information",
                },
            },
        },
        "startTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the execution started",
        },
        "endTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the execution ended",
        },
        "callLogLevel": {
            "type": "string",
            "description": "The call logging level",
            "enum": [
                "CALL_LOG_LEVEL_UNSPECIFIED",
                "LOG_ALL_CALLS",
                "LOG_ERRORS_ONLY",
                "LOG_NONE",
            ],
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "workflow") -> Dict[str, Any]:
    """Get the JSON schema for a specific Workflows resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("workflow" or "execution")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "execution":
        return WORKFLOW_EXECUTION_SCHEMA
    else:  # Default to workflow
        return WORKFLOW_SCHEMA
