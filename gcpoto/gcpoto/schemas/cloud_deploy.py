"""JSON Schema definitions for Google Cloud Deploy resources."""

from typing import Dict, Any

# JSON Schema for Cloud Deploy Delivery Pipelines
DELIVERY_PIPELINE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Deploy Delivery Pipeline",
    "description": "Schema for Google Cloud Deploy Delivery Pipelines",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified delivery pipeline name",
        },
        "description": {
            "type": "string",
            "description": "Description of the delivery pipeline",
        },
        "serialPipeline": {
            "type": "object",
            "description": "SerialPipeline defines a sequential set of stages",
            "properties": {
                "stages": {
                    "type": "array",
                    "description": "Each stage specifies configuration for a Target",
                    "items": {
                        "type": "object",
                        "properties": {
                            "targetId": {
                                "type": "string",
                                "description": "The target_id to which this stage points",
                            },
                            "profiles": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Skaffold profiles to use",
                            },
                        },
                    },
                },
            },
        },
        "condition": {
            "type": "object",
            "description": "Output only pipeline condition information",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the pipeline",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the pipeline was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last time the pipeline was updated",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Deploy Releases
RELEASE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Deploy Release",
    "description": "Schema for Google Cloud Deploy Releases",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified release name",
        },
        "description": {
            "type": "string",
            "description": "Description of the release",
        },
        "skaffoldConfigUri": {
            "type": "string",
            "description": "Cloud Storage URI of the skaffold configuration",
        },
        "skaffoldConfigPath": {
            "type": "string",
            "description": "Filepath of the skaffold configuration",
        },
        "renderState": {
            "type": "string",
            "description": "Current state of the render operation",
            "enum": [
                "RENDER_STATE_UNSPECIFIED",
                "SUCCEEDED",
                "FAILED",
                "IN_PROGRESS",
            ],
        },
        "deliveryPipelineSnapshot": {
            "type": "object",
            "description": "Snapshot of the delivery pipeline at release time",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the release",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the release was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last time the release was updated",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Deploy Rollouts
ROLLOUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Deploy Rollout",
    "description": "Schema for Google Cloud Deploy Rollouts",
    "type": "object",
    "required": ["name", "targetId"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified rollout name",
        },
        "targetId": {
            "type": "string",
            "description": "The target to which this rollout deploys",
        },
        "state": {
            "type": "string",
            "description": "Current state of the rollout",
            "enum": [
                "STATE_UNSPECIFIED",
                "SUCCEEDED",
                "FAILED",
                "IN_PROGRESS",
                "PENDING_APPROVAL",
                "APPROVAL_REJECTED",
                "PENDING",
                "PENDING_RELEASE",
            ],
        },
        "deployStartTime": {
            "type": "string",
            "format": "date-time",
            "description": "Time at which the rollout deploy started",
        },
        "deployEndTime": {
            "type": "string",
            "format": "date-time",
            "description": "Time at which the rollout deploy finished",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the rollout",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the rollout was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last time the rollout was updated",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "pipeline") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud Deploy resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("pipeline", "release", or "rollout")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "release":
        return RELEASE_SCHEMA
    elif resource_type.lower() == "rollout":
        return ROLLOUT_SCHEMA
    else:  # Default to pipeline
        return DELIVERY_PIPELINE_SCHEMA
