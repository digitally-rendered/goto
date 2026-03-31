"""JSON Schema definitions for Google Cloud AlloyDB resources."""

from typing import Dict, Any


# JSON Schema for AlloyDB Clusters
ALLOYDB_CLUSTER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP AlloyDB Cluster",
    "description": "Schema for Google Cloud AlloyDB Clusters",
    "type": "object",
    "required": ["name", "network"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The cluster name (projects/{project}/locations/{location}/clusters/{cluster})",
        },
        "network": {
            "type": "string",
            "description": "The VPC network for the cluster",
        },
        "state": {
            "type": "string",
            "description": "The current state of the cluster",
            "enum": [
                "STATE_UNSPECIFIED",
                "READY",
                "STOPPED",
                "EMPTY",
                "CREATING",
                "DELETING",
                "FAILED",
                "BOOTSTRAPPING",
                "MAINTENANCE",
                "PROMOTING",
            ],
        },
        "databaseVersion": {
            "type": "string",
            "description": "The database engine version",
            "enum": [
                "DATABASE_VERSION_UNSPECIFIED",
                "POSTGRES_14",
                "POSTGRES_15",
            ],
        },
        "automatedBackupPolicy": {
            "type": "object",
            "description": "The automated backup policy configuration",
        },
        "continuousBackupConfig": {
            "type": "object",
            "description": "The continuous backup configuration",
        },
        "labels": {
            "type": "object",
            "description": "Labels for the cluster",
            "additionalProperties": {"type": "string"},
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

# JSON Schema for AlloyDB Instances
ALLOYDB_INSTANCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP AlloyDB Instance",
    "description": "Schema for Google Cloud AlloyDB Instances",
    "type": "object",
    "required": ["name", "instanceType"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The instance name (projects/{project}/locations/{location}/clusters/{cluster}/instances/{instance})",
        },
        "instanceType": {
            "type": "string",
            "description": "The type of the instance",
            "enum": ["INSTANCE_TYPE_UNSPECIFIED", "PRIMARY", "READ_POOL"],
        },
        "state": {
            "type": "string",
            "description": "The current state of the instance",
            "enum": [
                "STATE_UNSPECIFIED",
                "READY",
                "STOPPED",
                "CREATING",
                "DELETING",
                "MAINTENANCE",
                "FAILED",
                "BOOTSTRAPPING",
                "PROMOTING",
            ],
        },
        "machineConfig": {
            "type": "object",
            "description": "Machine configuration for the instance",
            "properties": {
                "cpuCount": {
                    "type": "integer",
                    "description": "The number of CPU cores",
                },
            },
        },
        "availabilityType": {
            "type": "string",
            "description": "Availability type of the instance",
            "enum": ["AVAILABILITY_TYPE_UNSPECIFIED", "ZONAL", "REGIONAL"],
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


def get_schema(resource_type: str = "cluster") -> Dict[str, Any]:
    """Get the JSON schema for a specific AlloyDB resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("cluster" or "instance")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "cluster": ALLOYDB_CLUSTER_SCHEMA,
        "instance": ALLOYDB_INSTANCE_SCHEMA,
    }
    return schemas.get(resource_type.lower(), ALLOYDB_CLUSTER_SCHEMA)
