"""JSON Schema definitions for Google Cloud Vertex AI resources."""

from typing import Dict, Any


VERTEX_DATASET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Vertex AI Dataset",
    "description": "Schema for Google Cloud Vertex AI Datasets",
    "type": "object",
    "required": ["displayName"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the dataset",
        },
        "displayName": {
            "type": "string",
            "description": "The user-defined name of the dataset",
        },
        "metadataSchemaUri": {
            "type": "string",
            "description": "Points to a YAML file stored on Google Cloud Storage describing additional information about the dataset",
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata about the dataset",
        },
        "dataItemCount": {
            "type": "integer",
            "description": "The number of data items in the dataset",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the dataset",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp when the dataset was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp when the dataset was last updated",
        },
    },
    "additionalProperties": False,
}


VERTEX_MODEL_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Vertex AI Model",
    "description": "Schema for Google Cloud Vertex AI Models",
    "type": "object",
    "required": ["displayName"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the model",
        },
        "displayName": {
            "type": "string",
            "description": "The user-defined name of the model",
        },
        "description": {
            "type": "string",
            "description": "The description of the model",
        },
        "versionId": {
            "type": "string",
            "description": "The version ID of the model",
        },
        "artifactUri": {
            "type": "string",
            "description": "The path to the directory containing the model artifacts",
        },
        "containerSpec": {
            "type": "object",
            "description": "The specification of the container for serving predictions",
            "properties": {
                "imageUri": {
                    "type": "string",
                    "description": "The URI of the container image",
                },
                "command": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The command to run in the container",
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The arguments to the command",
                },
                "env": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "string"},
                        },
                    },
                    "description": "Environment variables for the container",
                },
                "ports": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "containerPort": {"type": "integer"},
                        },
                    },
                    "description": "Ports to expose from the container",
                },
                "predictRoute": {
                    "type": "string",
                    "description": "HTTP path for prediction requests",
                },
                "healthRoute": {
                    "type": "string",
                    "description": "HTTP path for health checks",
                },
            },
        },
        "deployedModels": {
            "type": "array",
            "description": "The pointers to deployed models created from this model",
            "items": {
                "type": "object",
                "properties": {
                    "endpoint": {"type": "string"},
                    "deployedModelId": {"type": "string"},
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the model",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp when the model was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp when the model was last updated",
        },
    },
    "additionalProperties": False,
}


VERTEX_ENDPOINT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Vertex AI Endpoint",
    "description": "Schema for Google Cloud Vertex AI Endpoints",
    "type": "object",
    "required": ["displayName"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the endpoint",
        },
        "displayName": {
            "type": "string",
            "description": "The user-defined name of the endpoint",
        },
        "description": {
            "type": "string",
            "description": "The description of the endpoint",
        },
        "deployedModels": {
            "type": "array",
            "description": "The models deployed on this endpoint",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "model": {"type": "string"},
                    "displayName": {"type": "string"},
                    "dedicatedResources": {
                        "type": "object",
                        "properties": {
                            "machineSpec": {
                                "type": "object",
                                "properties": {
                                    "machineType": {"type": "string"},
                                },
                            },
                            "minReplicaCount": {"type": "integer"},
                            "maxReplicaCount": {"type": "integer"},
                        },
                    },
                },
            },
        },
        "trafficSplit": {
            "type": "object",
            "description": "Traffic split configuration across deployed models",
            "additionalProperties": {"type": "integer"},
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the endpoint",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp when the endpoint was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp when the endpoint was last updated",
        },
    },
    "additionalProperties": False,
}


TRAINING_PIPELINE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Vertex AI Training Pipeline",
    "description": "Schema for Google Cloud Vertex AI Training Pipelines",
    "type": "object",
    "required": ["displayName", "trainingTaskDefinition", "trainingTaskInputs"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the training pipeline",
        },
        "displayName": {
            "type": "string",
            "description": "The user-defined name of the training pipeline",
        },
        "state": {
            "type": "string",
            "description": "The state of the pipeline",
            "enum": [
                "PIPELINE_STATE_UNSPECIFIED",
                "PIPELINE_STATE_QUEUED",
                "PIPELINE_STATE_PENDING",
                "PIPELINE_STATE_RUNNING",
                "PIPELINE_STATE_SUCCEEDED",
                "PIPELINE_STATE_FAILED",
                "PIPELINE_STATE_CANCELLING",
                "PIPELINE_STATE_CANCELLED",
                "PIPELINE_STATE_PAUSED",
            ],
        },
        "trainingTaskDefinition": {
            "type": "string",
            "description": "The training task definition resource name",
        },
        "trainingTaskInputs": {
            "type": "object",
            "description": "The training task inputs",
        },
        "modelToUpload": {
            "type": "object",
            "description": "The model to upload after training",
            "properties": {
                "displayName": {"type": "string"},
                "containerSpec": {"type": "object"},
            },
        },
        "startTime": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp when the training pipeline started",
        },
        "endTime": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp when the training pipeline ended",
        },
        "error": {
            "type": "object",
            "description": "Error information if the pipeline failed",
            "properties": {
                "code": {"type": "integer"},
                "message": {"type": "string"},
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the training pipeline",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp when the pipeline was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "Timestamp when the pipeline was last updated",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "dataset") -> Dict[str, Any]:
    """Get the JSON schema for a specific Vertex AI resource type.

    Args:
        resource_type: The type of resource
            ("dataset", "model", "endpoint", or "training_pipeline")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "dataset": VERTEX_DATASET_SCHEMA,
        "model": VERTEX_MODEL_SCHEMA,
        "endpoint": VERTEX_ENDPOINT_SCHEMA,
        "training_pipeline": TRAINING_PIPELINE_SCHEMA,
    }
    return schemas.get(resource_type.lower(), VERTEX_DATASET_SCHEMA)
