"""JSON Schema definitions for Google Cloud DNS resources."""

from typing import Dict, Any


# JSON Schema for Cloud DNS Managed Zones
DNS_MANAGED_ZONE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud DNS Managed Zone",
    "description": "Schema for Google Cloud DNS Managed Zones",
    "type": "object",
    "required": ["name", "dnsName"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the managed zone",
        },
        "name": {
            "type": "string",
            "description": "The name of the managed zone",
        },
        "dnsName": {
            "type": "string",
            "description": "The DNS name of the managed zone (e.g. example.com.)",
        },
        "description": {
            "type": "string",
            "description": "A description of the managed zone",
        },
        "visibility": {
            "type": "string",
            "description": "The zone's visibility",
            "enum": ["public", "private"],
        },
        "nameServers": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Name servers assigned to this managed zone",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the managed zone",
            "additionalProperties": {"type": "string"},
        },
        "project": {
            "type": "string",
            "description": "The GCP project ID containing the managed zone",
        },
        "creationTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the managed zone",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the managed zone",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud DNS Resource Record Sets
DNS_RESOURCE_RECORD_SET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud DNS Resource Record Set",
    "description": "Schema for Google Cloud DNS Resource Record Sets",
    "type": "object",
    "required": ["name", "type", "rrdatas"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The DNS name of the record set (e.g. www.example.com.)",
        },
        "type": {
            "type": "string",
            "description": "The type of DNS record",
            "enum": [
                "A",
                "AAAA",
                "CNAME",
                "MX",
                "TXT",
                "NS",
                "SOA",
                "SRV",
                "PTR",
            ],
        },
        "ttl": {
            "type": "integer",
            "description": "Time to live in seconds",
            "minimum": 0,
        },
        "rrdatas": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The resource record data for this record set",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the record set",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "zone") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud DNS resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("zone" or "record_set")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "record_set":
        return DNS_RESOURCE_RECORD_SET_SCHEMA
    else:
        return DNS_MANAGED_ZONE_SCHEMA
