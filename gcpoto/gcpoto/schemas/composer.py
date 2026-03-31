"""JSON Schema definitions for Google Cloud Composer resources."""

from typing import Dict, Any

COMPOSER_ENVIRONMENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Composer Environment",
    "description": "Schema for Google Cloud Composer Environments",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the environment",
        },
        "state": {
            "type": "string",
            "description": "The state of the environment",
            "enum": [
                "STATE_UNSPECIFIED",
                "CREATING",
                "RUNNING",
                "UPDATING",
                "DELETING",
                "ERROR",
            ],
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation timestamp",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update timestamp",
        },
        "config": {
            "type": "object",
            "description": "Configuration parameters for the environment",
            "properties": {
                "softwareConfig": {
                    "type": "object",
                    "description": "Software configuration",
                    "properties": {
                        "imageVersion": {
                            "type": "string",
                            "description": "Composer image version",
                        },
                        "airflowConfigOverrides": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                        },
                        "pypiPackages": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                        },
                        "envVariables": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                        },
                    },
                },
                "nodeConfig": {
                    "type": "object",
                    "description": "Node configuration",
                },
                "privateEnvironmentConfig": {
                    "type": "object",
                    "description": "Private environment configuration",
                },
                "webServerConfig": {
                    "type": "object",
                    "description": "Web server configuration",
                },
                "databaseConfig": {
                    "type": "object",
                    "description": "Cloud SQL database configuration",
                },
                "gkeCluster": {
                    "type": "string",
                    "description": "The GKE cluster used by the environment",
                },
                "dagGcsPrefix": {
                    "type": "string",
                    "description": "The GCS prefix for DAGs",
                },
                "airflowUri": {
                    "type": "string",
                    "description": "The Airflow web UI URI",
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels for the environment",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "environment") -> Dict[str, Any]:
    """Get the JSON schema for a specific Composer resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("environment")

    Returns:
        The JSON schema for the specified resource type
    """
    return COMPOSER_ENVIRONMENT_SCHEMA
