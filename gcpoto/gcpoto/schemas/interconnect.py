"""JSON Schema definitions for Google Cloud Interconnect resources."""

from typing import Dict, Any


# JSON Schema for Interconnect
INTERCONNECT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Interconnect",
    "description": "Schema for Google Cloud Interconnect",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the interconnect",
        },
        "location": {
            "type": "string",
            "description": "The location of the interconnect facility",
        },
        "interconnectType": {
            "type": "string",
            "description": "The type of interconnect",
            "enum": ["IT_PRIVATE", "PARTNER"],
        },
        "linkType": {
            "type": "string",
            "description": "The link type of the interconnect",
            "enum": [
                "LINK_TYPE_ETHERNET_10G_LR",
                "LINK_TYPE_ETHERNET_100G_LR",
            ],
        },
        "requestedLinkCount": {
            "type": "integer",
            "description": "The number of requested physical links",
        },
        "state": {
            "type": "string",
            "description": "The current state of the interconnect",
            "enum": ["ACTIVE", "UNPROVISIONED"],
        },
        "operationalStatus": {
            "type": "string",
            "description": "The operational status of the interconnect",
            "enum": ["OS_ACTIVE", "OS_UNPROVISIONED"],
        },
        "peerIpAddress": {
            "type": "string",
            "description": "The peer IP address for BGP",
        },
        "googleIpAddress": {
            "type": "string",
            "description": "The Google IP address for BGP",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the interconnect",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the interconnect",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Interconnect Attachment
INTERCONNECT_ATTACHMENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Interconnect Attachment",
    "description": "Schema for Google Cloud Interconnect Attachment (VLAN)",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the attachment",
        },
        "region": {
            "type": "string",
            "description": "The region of the attachment",
        },
        "interconnect": {
            "type": "string",
            "description": "The interconnect this attachment is associated with",
        },
        "router": {
            "type": "string",
            "description": "The Cloud Router for the attachment",
        },
        "type": {
            "type": "string",
            "description": "The type of attachment",
            "enum": ["DEDICATED", "PARTNER", "PARTNER_PROVIDER"],
        },
        "state": {
            "type": "string",
            "description": "The current state of the attachment",
            "enum": [
                "ACTIVE",
                "UNPROVISIONED",
                "PENDING_PARTNER",
                "PARTNER_REQUEST_RECEIVED",
                "PENDING_CUSTOMER",
                "DEFUNCT",
            ],
        },
        "bandwidth": {
            "type": "string",
            "description": "The bandwidth of the attachment",
            "enum": [
                "BPS_50M",
                "BPS_100M",
                "BPS_200M",
                "BPS_300M",
                "BPS_400M",
                "BPS_500M",
                "BPS_1G",
                "BPS_2G",
                "BPS_5G",
                "BPS_10G",
                "BPS_20G",
                "BPS_50G",
            ],
        },
        "vlanTag8021q": {
            "type": "integer",
            "description": "The 802.1q VLAN tag for the attachment",
        },
        "pairingKey": {
            "type": "string",
            "description": "The pairing key for partner interconnect",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the attachment",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the attachment",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "interconnect") -> Dict[str, Any]:
    """Get the JSON schema for a specific Interconnect resource type.

    Args:
        resource_type: The type of resource to get the schema for
            (``"interconnect"`` or ``"attachment"``).

    Returns:
        The JSON schema for the specified resource type.
    """
    schemas = {
        "interconnect": INTERCONNECT_SCHEMA,
        "attachment": INTERCONNECT_ATTACHMENT_SCHEMA,
    }
    return schemas.get(resource_type.lower(), INTERCONNECT_SCHEMA)
