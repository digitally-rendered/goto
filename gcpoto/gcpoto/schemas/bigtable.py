"""JSON Schema definitions for Google Cloud Bigtable resources."""

from typing import Dict, Any

# JSON Schema for Bigtable Instances
BIGTABLE_INSTANCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Bigtable Instance",
    "description": "Schema for Google Cloud Bigtable Instances",
    "type": "object",
    "required": ["name", "displayName"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The unique name of the instance",
        },
        "displayName": {
            "type": "string",
            "description": "The descriptive name for the instance",
        },
        "type": {
            "type": "string",
            "description": "The type of the instance",
            "enum": ["PRODUCTION", "DEVELOPMENT"],
        },
        "state": {
            "type": "string",
            "description": "The current state of the instance",
            "enum": ["STATE_NOT_KNOWN", "READY", "CREATING"],
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the instance",
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

# JSON Schema for Bigtable Clusters
BIGTABLE_CLUSTER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Bigtable Cluster",
    "description": "Schema for Google Cloud Bigtable Clusters",
    "type": "object",
    "required": ["name", "location"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The unique name of the cluster",
        },
        "location": {
            "type": "string",
            "description": "The location of the cluster",
        },
        "serveNodes": {
            "type": "integer",
            "description": "The number of nodes allocated to the cluster",
        },
        "defaultStorageType": {
            "type": "string",
            "description": "The type of storage used by the cluster",
            "enum": ["SSD", "HDD"],
        },
        "state": {
            "type": "string",
            "description": "The current state of the cluster",
            "enum": ["STATE_NOT_KNOWN", "READY", "CREATING", "RESIZING", "DISABLED"],
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the cluster",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the cluster",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Bigtable Tables
BIGTABLE_TABLE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Bigtable Table",
    "description": "Schema for Google Cloud Bigtable Tables",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The unique name of the table",
        },
        "columnFamilies": {
            "type": "object",
            "description": "The column families configured for the table",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "gcRule": {
                        "type": "object",
                        "description": "Garbage collection rule for the column family",
                    },
                },
            },
        },
        "granularity": {
            "type": "string",
            "description": "The granularity of timestamps stored in the table",
            "enum": ["MILLIS", "TIMESTAMP_GRANULARITY_UNSPECIFIED"],
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "instance") -> Dict[str, Any]:
    """Get the JSON schema for a specific Bigtable resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("instance", "cluster", or "table")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "cluster":
        return BIGTABLE_CLUSTER_SCHEMA
    elif resource_type.lower() == "table":
        return BIGTABLE_TABLE_SCHEMA
    else:  # Default to instance
        return BIGTABLE_INSTANCE_SCHEMA
