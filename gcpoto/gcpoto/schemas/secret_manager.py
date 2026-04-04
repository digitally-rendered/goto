"""JSON Schema definitions for Google Cloud Secret Manager resources."""

from typing import Dict, Any

SECRET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Secret Manager Secret",
    "description": "Schema for Google Cloud Secret Manager Secrets",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the secret in the format projects/*/secrets/*",
        },
        "replication": {
            "type": "object",
            "description": "The replication policy for the secret",
            "properties": {
                "automatic": {
                    "type": "object",
                    "description": "Automatic replication policy",
                },
                "userManaged": {
                    "type": "object",
                    "description": "User-managed replication policy",
                    "properties": {
                        "replicas": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "The canonical IDs of the location to replicate data",
                                    },
                                    "customerManagedEncryption": {
                                        "type": "object",
                                        "description": "Customer-managed encryption for the secret",
                                    },
                                },
                            },
                        }
                    },
                },
            },
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the secret was created",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the secret",
            "additionalProperties": {"type": "string"},
        },
        "expireTime": {
            "type": "string",
            "format": "date-time",
            "description": "Optional expiration time for the secret",
        },
        "ttl": {
            "type": "string",
            "description": "Optional TTL duration for the secret (e.g. '86400s')",
        },
        "rotation": {
            "type": "object",
            "description": "Optional rotation policy for the secret",
            "properties": {
                "nextRotationTime": {
                    "type": "string",
                    "format": "date-time",
                    "description": "The next time the secret should be rotated",
                },
                "rotationPeriod": {
                    "type": "string",
                    "description": "The duration between rotations (e.g. '86400s')",
                },
            },
        },
        "topics": {
            "type": "array",
            "description": "Pub/Sub topics for secret event notifications",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The fully-qualified topic resource name",
                    }
                },
            },
        },
    },
    "additionalProperties": False,
}

SECRET_VERSION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Secret Manager SecretVersion",
    "description": "Schema for Google Cloud Secret Manager SecretVersions",
    "type": "object",
    "required": ["name", "state"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the version in the format projects/*/secrets/*/versions/*",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the version was created",
        },
        "destroyTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the version was destroyed (if applicable)",
        },
        "state": {
            "type": "string",
            "description": "The state of the secret version",
            "enum": ["ENABLED", "DISABLED", "DESTROYED"],
        },
        "replicationStatus": {
            "type": "object",
            "description": "The replication status of the secret version",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "secret") -> Dict[str, Any]:
    """Get the JSON schema for a specific Secret Manager resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("secret" or "version")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "version":
        return SECRET_VERSION_SCHEMA
    return SECRET_SCHEMA
