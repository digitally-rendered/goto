"""JSON Schema definitions for Bare Metal Solution resources."""

from typing import Dict, Any


BARE_METAL_INSTANCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Bare Metal Solution Instance",
    "description": "Schema for Bare Metal Solution Instances",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the instance",
        },
        "location": {
            "type": "string",
            "description": "The location of the instance",
        },
        "machineType": {
            "type": "string",
            "description": "The machine type of the instance",
        },
        "state": {
            "type": "string",
            "description": "The current state of the instance",
            "enum": [
                "STATE_UNSPECIFIED",
                "PROVISIONING",
                "RUNNING",
                "DELETED",
                "UPDATING",
                "STARTING",
                "STOPPING",
                "SHUTDOWN",
            ],
        },
        "osImage": {
            "type": "string",
            "description": "The OS image currently installed",
        },
        "networkTemplate": {
            "type": "string",
            "description": "The network template for the instance",
        },
        "networks": {
            "type": "array",
            "description": "The networks associated with the instance",
            "items": {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "description": "The network name",
                    },
                    "ipAddress": {
                        "type": "string",
                        "description": "The IP address",
                    },
                },
            },
        },
        "luns": {
            "type": "array",
            "description": "The LUNs associated with the instance",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The LUN name",
                    },
                    "sizeGb": {
                        "type": "integer",
                        "description": "The LUN size in GB",
                    },
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels for the instance",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the instance was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the instance was last updated",
        },
    },
    "additionalProperties": False,
}

BARE_METAL_VOLUME_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Bare Metal Solution Volume",
    "description": "Schema for Bare Metal Solution Volumes",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the volume",
        },
        "location": {
            "type": "string",
            "description": "The location of the volume",
        },
        "storageType": {
            "type": "string",
            "description": "The storage type of the volume",
            "enum": ["STORAGE_TYPE_UNSPECIFIED", "SSD", "HDD"],
        },
        "sizeGib": {
            "type": "integer",
            "description": "The size of the volume in GiB",
        },
        "state": {
            "type": "string",
            "description": "The current state of the volume",
            "enum": [
                "STATE_UNSPECIFIED",
                "CREATING",
                "READY",
                "DELETING",
                "UPDATING",
                "COOL_OFF",
            ],
        },
        "snapshotAutoDeleteBehavior": {
            "type": "string",
            "description": "The snapshot auto-delete behavior",
            "enum": [
                "SNAPSHOT_AUTO_DELETE_BEHAVIOR_UNSPECIFIED",
                "DISABLED",
                "OLDEST_FIRST",
                "NEWEST_FIRST",
            ],
        },
        "labels": {
            "type": "object",
            "description": "Labels for the volume",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the volume was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the volume was last updated",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "instance") -> Dict[str, Any]:
    """Get the JSON schema for a specific Bare Metal Solution resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("instance" or "volume")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "instance": BARE_METAL_INSTANCE_SCHEMA,
        "volume": BARE_METAL_VOLUME_SCHEMA,
    }
    return schemas.get(resource_type.lower(), BARE_METAL_INSTANCE_SCHEMA)
