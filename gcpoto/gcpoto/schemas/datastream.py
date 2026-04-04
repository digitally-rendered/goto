"""JSON Schema definitions for Google Cloud Datastream resources."""

from typing import Dict, Any

CONNECTION_PROFILE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Datastream Connection Profile",
    "description": "Schema for Google Cloud Datastream Connection Profiles",
    "type": "object",
    "required": ["name", "displayName"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the connection profile",
        },
        "displayName": {
            "type": "string",
            "description": "Display name of the connection profile",
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
        "oracleProfile": {
            "type": "object",
            "description": "Oracle connection profile configuration",
        },
        "mysqlProfile": {
            "type": "object",
            "description": "MySQL connection profile configuration",
        },
        "postgresqlProfile": {
            "type": "object",
            "description": "PostgreSQL connection profile configuration",
        },
        "gcsProfile": {
            "type": "object",
            "description": "GCS connection profile configuration",
        },
        "bigqueryProfile": {
            "type": "object",
            "description": "BigQuery connection profile configuration",
        },
        "labels": {
            "type": "object",
            "description": "Labels for the connection profile",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

STREAM_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Datastream Stream",
    "description": "Schema for Google Cloud Datastream Streams",
    "type": "object",
    "required": ["name", "displayName", "sourceConfig", "destinationConfig"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the stream",
        },
        "displayName": {
            "type": "string",
            "description": "Display name of the stream",
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
        "state": {
            "type": "string",
            "description": "The state of the stream",
            "enum": [
                "STATE_UNSPECIFIED",
                "NOT_STARTED",
                "RUNNING",
                "PAUSED",
                "MAINTENANCE",
                "FAILED",
                "FAILED_PERMANENTLY",
                "STARTING",
                "DRAINING",
            ],
        },
        "sourceConfig": {
            "type": "object",
            "description": "Source connection configuration",
        },
        "destinationConfig": {
            "type": "object",
            "description": "Destination connection configuration",
        },
        "backfillAll": {
            "type": "object",
            "description": "Backfill all objects configuration",
        },
        "backfillNone": {
            "type": "object",
            "description": "No backfill configuration",
        },
        "labels": {
            "type": "object",
            "description": "Labels for the stream",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "connection_profile") -> Dict[str, Any]:
    """Get the JSON schema for a specific Datastream resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("connection_profile" or "stream")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "connection_profile": CONNECTION_PROFILE_SCHEMA,
        "stream": STREAM_SCHEMA,
    }
    return schemas.get(resource_type.lower(), CONNECTION_PROFILE_SCHEMA)
