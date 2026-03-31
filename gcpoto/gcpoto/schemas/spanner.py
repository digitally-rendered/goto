"""JSON Schema definitions for Google Cloud Spanner resources."""

from typing import Dict, Any


# JSON Schema for Spanner Instances
SPANNER_INSTANCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Spanner Instance",
    "description": "Schema for Google Cloud Spanner Instances",
    "type": "object",
    "required": ["name", "config", "displayName"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The unique name of the instance (projects/{project}/instances/{instance})",
        },
        "config": {
            "type": "string",
            "description": "The instance configuration (e.g. projects/{project}/instanceConfigs/regional-us-central1)",
        },
        "displayName": {
            "type": "string",
            "description": "The descriptive name for the instance",
        },
        "nodeCount": {
            "type": "integer",
            "description": "The number of nodes allocated to the instance",
            "minimum": 1,
        },
        "processingUnits": {
            "type": "integer",
            "description": "The number of processing units allocated (100 per node)",
            "minimum": 100,
        },
        "state": {
            "type": "string",
            "description": "The current state of the instance",
            "enum": ["STATE_UNSPECIFIED", "CREATING", "READY"],
        },
        "labels": {
            "type": "object",
            "description": "Labels for the instance",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the instance",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the instance",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Spanner Databases
SPANNER_DATABASE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Spanner Database",
    "description": "Schema for Google Cloud Spanner Databases",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The database name (projects/{project}/instances/{instance}/databases/{database})",
        },
        "state": {
            "type": "string",
            "description": "The current state of the database",
            "enum": [
                "STATE_UNSPECIFIED",
                "CREATING",
                "READY",
                "READY_OPTIMIZING",
            ],
        },
        "versionRetentionPeriod": {
            "type": "string",
            "description": "The retention period for versions of the database",
        },
        "earliestVersionTime": {
            "type": "string",
            "format": "date-time",
            "description": "The earliest available version time for the database",
        },
        "encryptionConfig": {
            "type": "object",
            "description": "Encryption configuration for the database",
            "properties": {
                "kmsKeyName": {
                    "type": "string",
                    "description": "The Cloud KMS key to use for encryption",
                },
            },
        },
        "databaseDialect": {
            "type": "string",
            "description": "The SQL dialect of the database",
            "enum": [
                "DATABASE_DIALECT_UNSPECIFIED",
                "GOOGLE_STANDARD_SQL",
                "POSTGRESQL",
            ],
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the database",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the database",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "instance") -> Dict[str, Any]:
    """Get the JSON schema for a specific Spanner resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("instance" or "database")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "instance": SPANNER_INSTANCE_SCHEMA,
        "database": SPANNER_DATABASE_SCHEMA,
    }
    return schemas.get(resource_type.lower(), SPANNER_INSTANCE_SCHEMA)
