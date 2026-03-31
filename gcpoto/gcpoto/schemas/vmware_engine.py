"""JSON Schema definitions for VMware Engine resources."""

from typing import Dict, Any


PRIVATE_CLOUD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP VMware Engine Private Cloud",
    "description": "Schema for VMware Engine Private Clouds",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the private cloud",
        },
        "location": {
            "type": "string",
            "description": "The location of the private cloud",
        },
        "description": {
            "type": "string",
            "description": "An optional description of the private cloud",
        },
        "state": {
            "type": "string",
            "description": "The current state of the private cloud",
            "enum": [
                "STATE_UNSPECIFIED",
                "ACTIVE",
                "CREATING",
                "UPDATING",
                "FAILED",
                "DELETED",
                "PURGING",
            ],
        },
        "networkConfig": {
            "type": "object",
            "description": "Network configuration for the private cloud",
            "properties": {
                "managementCidr": {
                    "type": "string",
                    "description": "Management CIDR for the private cloud",
                },
                "vmwareEngineNetwork": {
                    "type": "string",
                    "description": "The VMware Engine network resource",
                },
            },
        },
        "managementCluster": {
            "type": "object",
            "description": "Management cluster configuration",
            "properties": {
                "clusterId": {
                    "type": "string",
                    "description": "The cluster ID",
                },
                "nodeTypeConfigs": {
                    "type": "object",
                    "description": "Node type configurations",
                },
            },
        },
        "hcx": {
            "type": "object",
            "description": "HCX appliance configuration",
        },
        "nsx": {
            "type": "object",
            "description": "NSX appliance configuration",
        },
        "vcenter": {
            "type": "object",
            "description": "vCenter appliance configuration",
        },
        "labels": {
            "type": "object",
            "description": "Labels for the private cloud",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the private cloud was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the private cloud was last updated",
        },
    },
    "additionalProperties": False,
}

CLUSTER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP VMware Engine Cluster",
    "description": "Schema for VMware Engine Clusters",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the cluster",
        },
        "privateCloudName": {
            "type": "string",
            "description": "The name of the parent private cloud",
        },
        "location": {
            "type": "string",
            "description": "The location of the cluster",
        },
        "nodeTypeConfigs": {
            "type": "object",
            "description": "Node type configurations for the cluster",
        },
        "state": {
            "type": "string",
            "description": "The current state of the cluster",
            "enum": [
                "STATE_UNSPECIFIED",
                "ACTIVE",
                "CREATING",
                "UPDATING",
                "DELETING",
                "REPAIRING",
            ],
        },
        "labels": {
            "type": "object",
            "description": "Labels for the cluster",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the cluster was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the cluster was last updated",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "private_cloud") -> Dict[str, Any]:
    """Get the JSON schema for a specific VMware Engine resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("private_cloud" or "cluster")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "private_cloud": PRIVATE_CLOUD_SCHEMA,
        "cluster": CLUSTER_SCHEMA,
    }
    return schemas.get(resource_type.lower(), PRIVATE_CLOUD_SCHEMA)
