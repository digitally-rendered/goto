"""JSON Schema definitions for Google Cloud VPC / Networking resources."""

from typing import Dict, Any


# JSON Schema for VPC Networks
VPC_NETWORK_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP VPC Network",
    "description": "Schema for Google Cloud VPC Networks",
    "type": "object",
    "required": ["name"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the network",
        },
        "name": {
            "type": "string",
            "description": "The name of the VPC network",
        },
        "autoCreateSubnetworks": {
            "type": "boolean",
            "description": "Whether subnets are created automatically",
        },
        "routingConfig": {
            "type": "object",
            "description": "The network-wide routing configuration",
            "properties": {
                "routingMode": {
                    "type": "string",
                    "description": "The routing mode",
                    "enum": ["REGIONAL", "GLOBAL"],
                },
            },
        },
        "mtu": {
            "type": "integer",
            "description": "Maximum Transmission Unit in bytes",
            "minimum": 1300,
            "maximum": 8896,
        },
        "description": {
            "type": "string",
            "description": "A description of the VPC network",
        },
        "peerings": {
            "type": "array",
            "description": "List of network peerings",
            "items": {"type": "object"},
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the network",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the network",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Subnets
SUBNET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Subnet",
    "description": "Schema for Google Cloud VPC Subnets",
    "type": "object",
    "required": ["name", "network", "ipCidrRange"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the subnet",
        },
        "name": {
            "type": "string",
            "description": "The name of the subnet",
        },
        "network": {
            "type": "string",
            "description": "The URL of the network this subnet belongs to",
        },
        "region": {
            "type": "string",
            "description": "The region of the subnet",
        },
        "ipCidrRange": {
            "type": "string",
            "description": "The IPv4 CIDR range of the subnet",
        },
        "gatewayAddress": {
            "type": "string",
            "description": "The gateway address for the subnet",
        },
        "privateIpGoogleAccess": {
            "type": "boolean",
            "description": "Whether VMs can access Google services without external IP",
        },
        "secondaryIpRanges": {
            "type": "array",
            "description": "Secondary IP ranges for the subnet",
            "items": {
                "type": "object",
                "properties": {
                    "rangeName": {"type": "string"},
                    "ipCidrRange": {"type": "string"},
                },
            },
        },
        "purpose": {
            "type": "string",
            "description": "The purpose of the subnet",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the subnet",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the subnet",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Firewall Rules
FIREWALL_RULE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Firewall Rule",
    "description": "Schema for Google Cloud VPC Firewall Rules",
    "type": "object",
    "required": ["name", "network"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the firewall rule",
        },
        "name": {
            "type": "string",
            "description": "The name of the firewall rule",
        },
        "network": {
            "type": "string",
            "description": "The URL of the network this rule applies to",
        },
        "direction": {
            "type": "string",
            "description": "Direction of traffic",
            "enum": ["INGRESS", "EGRESS"],
        },
        "priority": {
            "type": "integer",
            "description": "Priority of the rule",
            "minimum": 0,
            "maximum": 65535,
        },
        "allowed": {
            "type": "array",
            "description": "List of allowed protocols and ports",
            "items": {
                "type": "object",
                "properties": {
                    "IPProtocol": {"type": "string"},
                    "ports": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "denied": {
            "type": "array",
            "description": "List of denied protocols and ports",
            "items": {
                "type": "object",
                "properties": {
                    "IPProtocol": {"type": "string"},
                    "ports": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "sourceRanges": {
            "type": "array",
            "description": "Source IP CIDR ranges",
            "items": {"type": "string"},
        },
        "destinationRanges": {
            "type": "array",
            "description": "Destination IP CIDR ranges",
            "items": {"type": "string"},
        },
        "sourceTags": {
            "type": "array",
            "description": "Source instance tags",
            "items": {"type": "string"},
        },
        "targetTags": {
            "type": "array",
            "description": "Target instance tags",
            "items": {"type": "string"},
        },
        "disabled": {
            "type": "boolean",
            "description": "Whether the rule is disabled",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the firewall rule",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the firewall rule",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Static Addresses
STATIC_ADDRESS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Static Address",
    "description": "Schema for Google Cloud Static Addresses",
    "type": "object",
    "required": ["name"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the address",
        },
        "name": {
            "type": "string",
            "description": "The name of the static address",
        },
        "region": {
            "type": "string",
            "description": "The region of the address",
        },
        "address": {
            "type": "string",
            "description": "The static IP address",
        },
        "addressType": {
            "type": "string",
            "description": "The type of address",
            "enum": ["INTERNAL", "EXTERNAL"],
        },
        "status": {
            "type": "string",
            "description": "The status of the address",
            "enum": ["RESERVED", "IN_USE", "RESERVING"],
        },
        "networkTier": {
            "type": "string",
            "description": "The network tier",
            "enum": ["PREMIUM", "STANDARD"],
        },
        "purpose": {
            "type": "string",
            "description": "The purpose of the address",
        },
        "subnetwork": {
            "type": "string",
            "description": "The URL of the subnetwork for INTERNAL addresses",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the address",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the address",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "network") -> Dict[str, Any]:
    """Get the JSON schema for a specific networking resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("network", "subnet", "firewall", or "address")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "network": VPC_NETWORK_SCHEMA,
        "subnet": SUBNET_SCHEMA,
        "firewall": FIREWALL_RULE_SCHEMA,
        "address": STATIC_ADDRESS_SCHEMA,
    }
    return schemas.get(resource_type.lower(), VPC_NETWORK_SCHEMA)
