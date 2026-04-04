"""JSON Schema definitions for Google Cloud NAT resources."""

from typing import Dict, Any


NAT_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud NAT Configuration",
    "description": "Schema for Google Cloud NAT configurations",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the NAT configuration",
        },
        "region": {
            "type": "string",
            "description": "The region of the NAT configuration",
        },
        "routerName": {
            "type": "string",
            "description": "The Cloud Router hosting this NAT",
        },
        "natIpAllocateOption": {
            "type": "string",
            "description": "NAT IP allocation option",
            "enum": ["AUTO_ONLY", "MANUAL_ONLY"],
        },
        "sourceSubnetworkIpRangesToNat": {
            "type": "string",
            "description": "Which subnetwork IP ranges to NAT",
            "enum": [
                "ALL_SUBNETWORKS_ALL_IP_RANGES",
                "ALL_SUBNETWORKS_ALL_PRIMARY_IP_RANGES",
                "LIST_OF_SUBNETWORKS",
            ],
        },
        "subnetworks": {
            "type": "array",
            "description": "Subnetworks to NAT",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "sourceIpRangesToNat": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "natIps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "NAT IP addresses for manual allocation",
        },
        "minPortsPerVm": {
            "type": "integer",
            "description": "Minimum number of ports per VM",
            "minimum": 64,
        },
        "logConfig": {
            "type": "object",
            "description": "Logging configuration",
            "properties": {
                "enable": {"type": "boolean"},
                "filter": {
                    "type": "string",
                    "enum": ["ALL", "ERRORS_ONLY", "TRANSLATIONS_ONLY"],
                },
            },
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "nat_config") -> Dict[str, Any]:
    """Get the JSON schema for a Cloud NAT resource type.

    Args:
        resource_type: The type of resource to get the schema for

    Returns:
        The JSON schema for the specified resource type
    """
    return NAT_CONFIG_SCHEMA
