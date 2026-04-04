"""JSON Schema definitions for Google Kubernetes Engine (GKE) resources."""

from typing import Dict, Any


# JSON Schema for GKE Clusters
GKE_CLUSTER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP GKE Cluster",
    "description": "Schema for Google Kubernetes Engine Clusters",
    "type": "object",
    "required": ["name", "location"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the cluster",
        },
        "location": {
            "type": "string",
            "description": "The location (zone or region) of the cluster",
        },
        "description": {
            "type": "string",
            "description": "An optional description of the cluster",
        },
        "initialNodeCount": {
            "type": "integer",
            "description": "The initial number of nodes for the cluster",
        },
        "nodeConfig": {
            "type": "object",
            "description": "The node configuration for the cluster",
            "properties": {
                "machineType": {
                    "type": "string",
                    "description": "The machine type for nodes",
                },
                "diskSizeGb": {
                    "type": "integer",
                    "description": "Size of the disk in GB",
                },
                "oauthScopes": {
                    "type": "array",
                    "description": "OAuth scopes for the nodes",
                    "items": {"type": "string"},
                },
                "labels": {
                    "type": "object",
                    "description": "Labels applied to each node",
                    "additionalProperties": {"type": "string"},
                },
            },
        },
        "masterAuth": {
            "type": "object",
            "description": "The authentication information for the master",
            "properties": {
                "clusterCaCertificate": {
                    "type": "string",
                    "description": "Base64-encoded public certificate of the cluster CA",
                },
            },
        },
        "network": {
            "type": "string",
            "description": "The name of the VPC network",
        },
        "subnetwork": {
            "type": "string",
            "description": "The name of the subnetwork",
        },
        "clusterIpv4Cidr": {
            "type": "string",
            "description": "The IP address range of the container pods",
        },
        "endpoint": {
            "type": "string",
            "description": "The IP address of the cluster master",
        },
        "status": {
            "type": "string",
            "description": "The current status of the cluster",
            "enum": [
                "STATUS_UNSPECIFIED",
                "PROVISIONING",
                "RUNNING",
                "RECONCILING",
                "STOPPING",
                "ERROR",
                "DEGRADED",
            ],
        },
        "currentMasterVersion": {
            "type": "string",
            "description": "The current software version of the master",
        },
        "currentNodeVersion": {
            "type": "string",
            "description": "The current version of the node software",
        },
        "nodePools": {
            "type": "array",
            "description": "The node pools associated with this cluster",
            "items": {"$ref": "#/definitions/nodePool"},
        },
        "resourceLabels": {
            "type": "object",
            "description": "The resource labels for the cluster",
            "additionalProperties": {"type": "string"},
        },
        "projectId": {
            "type": "string",
            "description": "The GCP project ID",
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

# JSON Schema for GKE Node Pools
NODE_POOL_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP GKE Node Pool",
    "description": "Schema for Google Kubernetes Engine Node Pools",
    "type": "object",
    "required": ["name", "initialNodeCount"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the node pool",
        },
        "clusterName": {
            "type": "string",
            "description": "The name of the parent cluster",
        },
        "location": {
            "type": "string",
            "description": "The location (zone or region) of the cluster",
        },
        "config": {
            "type": "object",
            "description": "The node configuration for this pool",
            "properties": {
                "machineType": {
                    "type": "string",
                    "description": "The machine type for nodes",
                },
                "diskSizeGb": {
                    "type": "integer",
                    "description": "Size of the disk in GB",
                },
                "oauthScopes": {
                    "type": "array",
                    "description": "OAuth scopes for the nodes",
                    "items": {"type": "string"},
                },
                "labels": {
                    "type": "object",
                    "description": "Labels applied to each node",
                    "additionalProperties": {"type": "string"},
                },
            },
        },
        "initialNodeCount": {
            "type": "integer",
            "description": "The initial node count for the pool",
        },
        "autoscaling": {
            "type": "object",
            "description": "Autoscaling configuration for this pool",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Whether autoscaling is enabled",
                },
                "minNodeCount": {
                    "type": "integer",
                    "description": "Minimum number of nodes",
                },
                "maxNodeCount": {
                    "type": "integer",
                    "description": "Maximum number of nodes",
                },
            },
        },
        "management": {
            "type": "object",
            "description": "Node management configuration",
            "properties": {
                "autoUpgrade": {
                    "type": "boolean",
                    "description": "Whether auto-upgrade is enabled",
                },
                "autoRepair": {
                    "type": "boolean",
                    "description": "Whether auto-repair is enabled",
                },
            },
        },
        "status": {
            "type": "string",
            "description": "The current status of the node pool",
            "enum": [
                "STATUS_UNSPECIFIED",
                "PROVISIONING",
                "RUNNING",
                "RUNNING_WITH_ERROR",
                "RECONCILING",
                "STOPPING",
                "ERROR",
            ],
        },
        "version": {
            "type": "string",
            "description": "The Kubernetes version of the nodes",
        },
        "instanceGroupUrls": {
            "type": "array",
            "description": "The URLs of the instance groups managed by this pool",
            "items": {"type": "string"},
        },
        "projectId": {
            "type": "string",
            "description": "The GCP project ID",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "cluster") -> Dict[str, Any]:
    """Get the JSON schema for a specific GKE resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("cluster" or "node_pool")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "cluster": GKE_CLUSTER_SCHEMA,
        "node_pool": NODE_POOL_SCHEMA,
    }
    return schemas.get(resource_type.lower(), GKE_CLUSTER_SCHEMA)
