"""JSON Schema definitions for Google Cloud Eventarc resources."""

from typing import Dict, Any

# JSON Schema for Eventarc Triggers
EVENTARC_TRIGGER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Eventarc Trigger",
    "description": "Schema for Google Cloud Eventarc Triggers",
    "type": "object",
    "required": ["name", "eventFilters", "destination"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified trigger name",
        },
        "eventFilters": {
            "type": "array",
            "description": "Event filters for matching events",
            "items": {
                "type": "object",
                "properties": {
                    "attribute": {
                        "type": "string",
                        "description": "The name of a CloudEvents attribute",
                    },
                    "value": {
                        "type": "string",
                        "description": "The value for the attribute",
                    },
                    "operator": {
                        "type": "string",
                        "description": "The operator used for matching",
                    },
                },
                "required": ["attribute", "value"],
            },
        },
        "destination": {
            "type": "object",
            "description": "Destination for matched events",
            "properties": {
                "cloudRun": {
                    "type": "object",
                    "description": "Cloud Run destination",
                    "properties": {
                        "service": {
                            "type": "string",
                            "description": "The Cloud Run service name",
                        },
                        "path": {
                            "type": "string",
                            "description": "The relative path on the Cloud Run service",
                        },
                        "region": {
                            "type": "string",
                            "description": "The region of the Cloud Run service",
                        },
                    },
                },
                "cloudFunction": {
                    "type": "string",
                    "description": "The Cloud Function resource name",
                },
                "gke": {
                    "type": "object",
                    "description": "GKE destination",
                    "properties": {
                        "cluster": {
                            "type": "string",
                            "description": "The GKE cluster name",
                        },
                        "location": {
                            "type": "string",
                            "description": "The cluster location",
                        },
                        "namespace": {
                            "type": "string",
                            "description": "The Kubernetes namespace",
                        },
                        "service": {
                            "type": "string",
                            "description": "The Kubernetes service name",
                        },
                        "path": {
                            "type": "string",
                            "description": "The relative path",
                        },
                    },
                },
                "workflow": {
                    "type": "string",
                    "description": "The Workflows resource name",
                },
            },
        },
        "transport": {
            "type": "object",
            "description": "Transport configuration",
            "properties": {
                "pubsub": {
                    "type": "object",
                    "description": "Pub/Sub transport configuration",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The Pub/Sub topic name",
                        },
                        "subscription": {
                            "type": "string",
                            "description": "The Pub/Sub subscription name",
                        },
                    },
                },
            },
        },
        "serviceAccount": {
            "type": "string",
            "description": "The IAM service account email",
        },
        "channel": {
            "type": "string",
            "description": "The channel associated with the trigger",
        },
        "conditions": {
            "type": "object",
            "description": "Conditions for the trigger",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the trigger",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the trigger was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last time the trigger was updated",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "trigger") -> Dict[str, Any]:
    """Get the JSON schema for a specific Eventarc resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("trigger")

    Returns:
        The JSON schema for the specified resource type
    """
    return EVENTARC_TRIGGER_SCHEMA
