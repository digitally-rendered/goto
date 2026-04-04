"""JSON Schema definitions for Google Cloud Run resources."""

from typing import Dict, Any

CLOUD_RUN_SERVICE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Run Service",
    "description": "Schema for Google Cloud Run Services",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified name of the service in the format projects/*/locations/*/services/*",
        },
        "description": {
            "type": "string",
            "description": "User-provided description of the service",
        },
        "uri": {
            "type": "string",
            "description": "The main URI in which this service is serving traffic",
        },
        "ingress": {
            "type": "string",
            "description": "Ingress settings for the service",
            "enum": [
                "INGRESS_TRAFFIC_ALL",
                "INGRESS_TRAFFIC_INTERNAL_ONLY",
                "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER",
            ],
        },
        "launchStage": {
            "type": "string",
            "description": "The launch stage of the service",
            "enum": ["UNIMPLEMENTED", "PRELAUNCH", "EARLY_ACCESS", "ALPHA", "BETA", "GA", "DEPRECATED"],
        },
        "template": {
            "type": "object",
            "description": "The template used to create revisions for this service",
            "properties": {
                "revision": {
                    "type": "string",
                    "description": "The unique name for the revision",
                },
                "labels": {
                    "type": "object",
                    "description": "Labels applied to the revision template",
                    "additionalProperties": {"type": "string"},
                },
                "scaling": {
                    "type": "object",
                    "description": "Scaling settings for the revision",
                    "properties": {
                        "minInstanceCount": {"type": "integer"},
                        "maxInstanceCount": {"type": "integer"},
                    },
                },
                "containers": {
                    "type": "array",
                    "description": "Containers for the revision",
                    "items": {
                        "type": "object",
                        "properties": {
                            "image": {
                                "type": "string",
                                "description": "Container image URI",
                            },
                            "ports": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "containerPort": {"type": "integer"},
                                    },
                                },
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
                            },
                            "resources": {
                                "type": "object",
                                "properties": {
                                    "limits": {
                                        "type": "object",
                                        "additionalProperties": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
                "serviceAccount": {
                    "type": "string",
                    "description": "Email address of the IAM service account",
                },
            },
        },
        "traffic": {
            "type": "array",
            "description": "Specifies how to distribute traffic over revisions",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "revision": {"type": "string"},
                    "percent": {"type": "integer"},
                    "tag": {"type": "string"},
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the service",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the service was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the service was last updated",
        },
        "conditions": {
            "type": "array",
            "description": "The conditions of the service",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "state": {"type": "string"},
                    "message": {"type": "string"},
                    "lastTransitionTime": {
                        "type": "string",
                        "format": "date-time",
                    },
                },
            },
        },
        "latestReadyRevision": {
            "type": "string",
            "description": "Name of the latest revision that is serving traffic",
        },
        "latestCreatedRevision": {
            "type": "string",
            "description": "Name of the last created revision",
        },
    },
    "additionalProperties": False,
}

CLOUD_RUN_REVISION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Run Revision",
    "description": "Schema for Google Cloud Run Revisions",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified name of the revision in the format projects/*/locations/*/services/*/revisions/*",
        },
        "generation": {
            "type": "integer",
            "description": "A number that monotonically increases every time the user modifies the desired state",
        },
        "containers": {
            "type": "array",
            "description": "Containers for the revision",
            "items": {
                "type": "object",
                "properties": {
                    "image": {"type": "string"},
                    "ports": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "containerPort": {"type": "integer"},
                            },
                        },
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
                    },
                    "resources": {
                        "type": "object",
                        "properties": {
                            "limits": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
        "scaling": {
            "type": "object",
            "description": "Scaling settings for the revision",
            "properties": {
                "minInstanceCount": {"type": "integer"},
                "maxInstanceCount": {"type": "integer"},
            },
        },
        "serviceAccount": {
            "type": "string",
            "description": "Email address of the IAM service account",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the revision",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the revision was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the revision was last updated",
        },
        "conditions": {
            "type": "array",
            "description": "The conditions of the revision",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "state": {"type": "string"},
                    "message": {"type": "string"},
                    "lastTransitionTime": {
                        "type": "string",
                        "format": "date-time",
                    },
                },
            },
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "service") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud Run resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("service" or "revision")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "revision":
        return CLOUD_RUN_REVISION_SCHEMA
    return CLOUD_RUN_SERVICE_SCHEMA
