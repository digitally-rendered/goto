"""JSON Schema definitions for Network Security resources."""

from typing import Dict, Any


SERVER_TLS_POLICY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Network Security Server TLS Policy",
    "description": "Schema for Network Security Server TLS Policies",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the server TLS policy",
        },
        "description": {
            "type": "string",
            "description": "A description of the policy",
        },
        "allowOpen": {
            "type": "boolean",
            "description": "Whether to allow open (non-TLS) connections",
        },
        "serverCertificate": {
            "type": "object",
            "description": "The server certificate configuration",
            "additionalProperties": True,
        },
        "mtlsPolicy": {
            "type": "object",
            "description": "The mutual TLS policy configuration",
            "additionalProperties": True,
        },
        "labels": {
            "type": "object",
            "description": "Labels for the policy",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the policy",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the policy",
        },
    },
    "additionalProperties": False,
}

AUTHORIZATION_POLICY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Network Security Authorization Policy",
    "description": "Schema for Network Security Authorization Policies",
    "type": "object",
    "required": ["name", "action"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the authorization policy",
        },
        "description": {
            "type": "string",
            "description": "A description of the policy",
        },
        "action": {
            "type": "string",
            "description": "The action to take when a rule match is found",
            "enum": ["ALLOW", "DENY"],
        },
        "rules": {
            "type": "array",
            "description": "The authorization rules",
            "items": {"type": "object", "additionalProperties": True},
        },
        "labels": {
            "type": "object",
            "description": "Labels for the policy",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the policy",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the policy",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "server_tls_policy") -> Dict[str, Any]:
    """Get the JSON schema for a specific Network Security resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("server_tls_policy" or "authorization_policy")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "authorization_policy":
        return AUTHORIZATION_POLICY_SCHEMA
    else:
        return SERVER_TLS_POLICY_SCHEMA
