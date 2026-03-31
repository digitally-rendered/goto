"""JSON Schema definitions for Google Cloud Certificate Manager resources."""

from typing import Dict, Any


CERTIFICATE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Certificate Manager Certificate",
    "description": "Schema for Google Cloud Certificate Manager Certificates",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The full resource name of the certificate",
        },
        "description": {
            "type": "string",
            "description": "A description of the certificate",
        },
        "sanDnsnames": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Subject Alternative Name DNS names",
        },
        "pemCertificate": {
            "type": "string",
            "description": "The PEM-encoded certificate chain",
        },
        "expireTime": {
            "type": "string",
            "format": "date-time",
            "description": "The expiration time of the certificate",
        },
        "scope": {
            "type": "string",
            "description": "The scope of the certificate",
            "enum": ["DEFAULT", "EDGE_CACHE"],
        },
        "managed": {
            "type": "object",
            "description": "Managed certificate configuration",
            "properties": {
                "domains": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "dnsAuthorizations": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "state": {"type": "string"},
            },
        },
        "selfManaged": {
            "type": "object",
            "description": "Self-managed certificate configuration",
            "properties": {
                "pemCertificate": {"type": "string"},
                "pemPrivateKey": {"type": "string"},
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the certificate",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the certificate",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the certificate",
        },
    },
    "additionalProperties": False,
}

CERTIFICATE_MAP_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Certificate Manager Certificate Map",
    "description": "Schema for Google Cloud Certificate Manager Certificate Maps",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The full resource name of the certificate map",
        },
        "description": {
            "type": "string",
            "description": "A description of the certificate map",
        },
        "gclbTargets": {
            "type": "array",
            "description": "GCLB targets associated with this map",
            "items": {
                "type": "object",
                "properties": {
                    "targetHttpsProxy": {"type": "string"},
                    "targetSslProxy": {"type": "string"},
                    "ipConfigs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ipAddress": {"type": "string"},
                                "ports": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                },
                            },
                        },
                    },
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the certificate map",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the certificate map",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the certificate map",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "certificate") -> Dict[str, Any]:
    """Get the JSON schema for a specific Certificate Manager resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("certificate" or "certificate_map")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "certificate_map":
        return CERTIFICATE_MAP_SCHEMA
    else:
        return CERTIFICATE_SCHEMA
