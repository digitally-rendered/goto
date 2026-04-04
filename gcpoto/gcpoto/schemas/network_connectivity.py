"""JSON Schema definitions for Network Connectivity Center resources."""

from typing import Dict, Any


HUB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Network Connectivity Hub",
    "description": "Schema for Network Connectivity Center Hubs",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the hub",
        },
        "description": {
            "type": "string",
            "description": "A description of the hub",
        },
        "routingVpcs": {
            "type": "array",
            "description": "The VPC networks associated with this hub",
            "items": {
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": "The URI of the VPC network",
                    },
                },
            },
        },
        "state": {
            "type": "string",
            "description": "The current state of the hub",
            "enum": ["CREATING", "ACTIVE", "DELETING"],
        },
        "labels": {
            "type": "object",
            "description": "Labels for the hub",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the hub",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the hub",
        },
    },
    "additionalProperties": False,
}

SPOKE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Network Connectivity Spoke",
    "description": "Schema for Network Connectivity Center Spokes",
    "type": "object",
    "required": ["name", "hub"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the spoke",
        },
        "hub": {
            "type": "string",
            "description": "The hub this spoke is attached to",
        },
        "description": {
            "type": "string",
            "description": "A description of the spoke",
        },
        "linkedVpnTunnels": {
            "type": "object",
            "description": "VPN tunnels linked to this spoke",
            "additionalProperties": True,
        },
        "linkedInterconnectAttachments": {
            "type": "object",
            "description": "Interconnect attachments linked to this spoke",
            "additionalProperties": True,
        },
        "linkedRouterApplianceInstances": {
            "type": "object",
            "description": "Router appliance instances linked to this spoke",
            "additionalProperties": True,
        },
        "state": {
            "type": "string",
            "description": "The current state of the spoke",
            "enum": ["CREATING", "ACTIVE", "DELETING", "INACTIVE"],
        },
        "labels": {
            "type": "object",
            "description": "Labels for the spoke",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the spoke",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the spoke",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "hub") -> Dict[str, Any]:
    """Get the JSON schema for a specific Network Connectivity resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("hub" or "spoke")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "spoke":
        return SPOKE_SCHEMA
    else:
        return HUB_SCHEMA
