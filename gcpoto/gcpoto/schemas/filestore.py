"""JSON Schema definitions for Google Cloud Filestore resources."""

from typing import Dict, Any

# JSON Schema for Filestore Instances
FILESTORE_INSTANCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Filestore Instance",
    "description": "Schema for Google Cloud Filestore Instances",
    "type": "object",
    "required": ["name", "tier"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name for the instance",
        },
        "description": {
            "type": "string",
            "description": "A description of the instance",
        },
        "tier": {
            "type": "string",
            "description": "The service tier of the instance",
            "enum": [
                "BASIC_HDD",
                "BASIC_SSD",
                "HIGH_SCALE_SSD",
                "ENTERPRISE",
            ],
        },
        "state": {
            "type": "string",
            "description": "The current state of the instance",
            "enum": [
                "STATE_UNSPECIFIED",
                "CREATING",
                "READY",
                "REPAIRING",
                "DELETING",
                "ERROR",
                "RESTORING",
                "SUSPENDED",
                "SUSPENDING",
                "RESUMING",
                "REVERTING",
            ],
        },
        "statusMessage": {
            "type": "string",
            "description": "Additional status information about the instance",
        },
        "fileShares": {
            "type": "array",
            "description": "File shares configured on the instance",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the file share",
                    },
                    "capacityGb": {
                        "type": "string",
                        "description": "The capacity of the file share in GB",
                    },
                },
            },
        },
        "networks": {
            "type": "array",
            "description": "VPC networks connected to the instance",
            "items": {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "The name of the VPC network",
                    },
                    "modes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Internet protocol versions for the network",
                    },
                    "reservedIpRange": {
                        "type": "string",
                        "description": "A /29 CIDR block for the instance",
                    },
                    "ipAddresses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "IP addresses assigned to the instance",
                    },
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the instance",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the instance was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the instance was last updated",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Filestore Snapshots
FILESTORE_SNAPSHOT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Filestore Snapshot",
    "description": "Schema for Google Cloud Filestore Snapshots",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the snapshot",
        },
        "description": {
            "type": "string",
            "description": "A description of the snapshot",
        },
        "state": {
            "type": "string",
            "description": "The current state of the snapshot",
            "enum": ["STATE_UNSPECIFIED", "CREATING", "READY", "DELETING"],
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the snapshot was created",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the snapshot",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "instance") -> Dict[str, Any]:
    """Get the JSON schema for a specific Filestore resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("instance" or "snapshot")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "instance": FILESTORE_INSTANCE_SCHEMA,
        "snapshot": FILESTORE_SNAPSHOT_SCHEMA,
    }
    return schemas.get(resource_type, FILESTORE_INSTANCE_SCHEMA)
