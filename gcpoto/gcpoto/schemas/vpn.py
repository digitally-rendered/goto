"""JSON Schema definitions for Google Cloud VPN resources."""

from typing import Dict, Any


VPN_GATEWAY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud VPN Gateway",
    "description": "Schema for Google Cloud VPN Gateways",
    "type": "object",
    "required": ["name", "network"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the VPN gateway",
        },
        "name": {
            "type": "string",
            "description": "The name of the VPN gateway",
        },
        "region": {
            "type": "string",
            "description": "The region of the VPN gateway",
        },
        "network": {
            "type": "string",
            "description": "The network this VPN gateway belongs to",
        },
        "vpnInterfaces": {
            "type": "array",
            "description": "VPN interfaces for the gateway",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "ipAddress": {"type": "string"},
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the VPN gateway",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the VPN gateway",
        },
    },
    "additionalProperties": False,
}

VPN_TUNNEL_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud VPN Tunnel",
    "description": "Schema for Google Cloud VPN Tunnels",
    "type": "object",
    "required": ["name", "vpnGateway", "peerIp", "sharedSecret"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the VPN tunnel",
        },
        "name": {
            "type": "string",
            "description": "The name of the VPN tunnel",
        },
        "region": {
            "type": "string",
            "description": "The region of the VPN tunnel",
        },
        "vpnGateway": {
            "type": "string",
            "description": "The VPN gateway this tunnel is associated with",
        },
        "peerIp": {
            "type": "string",
            "description": "The peer IP address",
        },
        "sharedSecret": {
            "type": "string",
            "description": "The shared secret for IKE",
        },
        "ikeVersion": {
            "type": "integer",
            "description": "The IKE protocol version (1 or 2)",
            "enum": [1, 2],
        },
        "status": {
            "type": "string",
            "description": "The status of the tunnel",
            "enum": [
                "PROVISIONING",
                "WAITING_FOR_FULL_CONFIG",
                "FIRST_HANDSHAKE",
                "ESTABLISHED",
                "NO_INCOMING_PACKETS",
                "AUTHORIZATION_ERROR",
                "NEGOTIATION_FAILURE",
                "DEPROVISIONING",
            ],
        },
        "detailedStatus": {
            "type": "string",
            "description": "Detailed status message",
        },
        "localTrafficSelector": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Local traffic selector CIDR ranges",
        },
        "remoteTrafficSelector": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Remote traffic selector CIDR ranges",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the VPN tunnel",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the VPN tunnel",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "vpn_gateway") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud VPN resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("vpn_gateway" or "vpn_tunnel")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "vpn_tunnel":
        return VPN_TUNNEL_SCHEMA
    else:
        return VPN_GATEWAY_SCHEMA
