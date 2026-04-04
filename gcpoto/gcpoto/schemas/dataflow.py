"""JSON Schema definitions for Google Cloud Dataflow resources."""

from typing import Dict, Any

# JSON Schema for Dataflow Jobs
DATAFLOW_JOB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Dataflow Job",
    "description": "Schema for Google Cloud Dataflow Jobs",
    "type": "object",
    "required": ["name"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique ID of the job",
        },
        "name": {
            "type": "string",
            "description": "The user-assigned name of the job",
        },
        "projectId": {
            "type": "string",
            "description": "The ID of the Cloud Platform project",
        },
        "location": {
            "type": "string",
            "description": "The regional endpoint for the job",
        },
        "type": {
            "type": "string",
            "description": "The type of Dataflow job",
            "enum": [
                "JOB_TYPE_UNKNOWN",
                "JOB_TYPE_BATCH",
                "JOB_TYPE_STREAMING",
            ],
        },
        "currentState": {
            "type": "string",
            "description": "The current state of the job",
            "enum": [
                "JOB_STATE_UNKNOWN",
                "JOB_STATE_STOPPED",
                "JOB_STATE_RUNNING",
                "JOB_STATE_DONE",
                "JOB_STATE_FAILED",
                "JOB_STATE_CANCELLED",
                "JOB_STATE_UPDATED",
                "JOB_STATE_DRAINING",
                "JOB_STATE_DRAINED",
                "JOB_STATE_PENDING",
                "JOB_STATE_CANCELLING",
                "JOB_STATE_QUEUED",
            ],
        },
        "requestedState": {
            "type": "string",
            "description": "The requested state of the job",
            "enum": [
                "JOB_STATE_UNKNOWN",
                "JOB_STATE_RUNNING",
                "JOB_STATE_DONE",
                "JOB_STATE_CANCELLED",
                "JOB_STATE_DRAINED",
            ],
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The timestamp when the job was created",
        },
        "startTime": {
            "type": "string",
            "format": "date-time",
            "description": "The timestamp when the job was started",
        },
        "currentStateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The timestamp of the current state",
        },
        "pipelineDescription": {
            "type": "object",
            "description": "Preliminary field describing the pipeline",
            "properties": {
                "originalPipelineTransform": {
                    "type": "array",
                    "description": "Transforms in the pipeline",
                    "items": {"type": "object"},
                },
                "executionPipelineStage": {
                    "type": "array",
                    "description": "Execution stages of the pipeline",
                    "items": {"type": "object"},
                },
            },
        },
        "stageStates": {
            "type": "array",
            "description": "Information about stages of the pipeline",
            "items": {
                "type": "object",
                "properties": {
                    "executionStageName": {
                        "type": "string",
                        "description": "The name of the stage",
                    },
                    "executionStageState": {
                        "type": "string",
                        "description": "The state of the stage",
                    },
                    "currentStateTime": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Timestamp of the current state",
                    },
                },
            },
        },
        "environment": {
            "type": "object",
            "description": "The environment configuration for the job",
            "properties": {
                "tempStoragePrefix": {
                    "type": "string",
                    "description": "Temp storage prefix for the job",
                },
                "workerPools": {
                    "type": "array",
                    "description": "Worker pools for the job",
                    "items": {"type": "object"},
                },
                "serviceAccountEmail": {
                    "type": "string",
                    "description": "Service account email",
                },
            },
        },
        "sdkPipelineOptions": {
            "type": "object",
            "description": "SDK pipeline options for the job",
        },
        "tempFiles": {
            "type": "array",
            "description": "Temporary files used by the job",
            "items": {"type": "string"},
        },
        "labels": {
            "type": "object",
            "description": "User-defined labels for the job",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Dataflow Templates
DATAFLOW_TEMPLATE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Dataflow Template",
    "description": "Schema for Google Cloud Dataflow Templates",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The template name",
        },
        "location": {
            "type": "string",
            "description": "The regional endpoint for the template",
        },
        "metadata": {
            "type": "object",
            "description": "Metadata about the template",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the template",
                },
                "description": {
                    "type": "string",
                    "description": "A description of the template",
                },
                "parameters": {
                    "type": "array",
                    "description": "The parameters for the template",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "label": {"type": "string"},
                            "helpText": {"type": "string"},
                            "isOptional": {"type": "boolean"},
                        },
                    },
                },
            },
        },
        "runtimeParameters": {
            "type": "object",
            "description": "Runtime parameters for the template",
            "additionalProperties": {"type": "string"},
        },
        "labels": {
            "type": "object",
            "description": "User-defined labels",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "job") -> Dict[str, Any]:
    """Get the JSON schema for a specific Dataflow resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("job" or "template")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "template":
        return DATAFLOW_TEMPLATE_SCHEMA
    else:  # Default to job
        return DATAFLOW_JOB_SCHEMA
