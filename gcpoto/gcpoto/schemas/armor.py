"""JSON Schema definitions for Google Cloud Armor resources."""

from typing import Dict, Any


# JSON Schema for Cloud Armor Security Policies
SECURITY_POLICY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Armor Security Policy",
    "description": "Schema for Google Cloud Armor Security Policies",
    "type": "object",
    "required": ["name"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the security policy",
        },
        "name": {
            "type": "string",
            "description": "The name of the security policy",
        },
        "description": {
            "type": "string",
            "description": "A description of the security policy",
        },
        "rules": {
            "type": "array",
            "description": "The list of rules that belong to this policy",
            "items": {
                "type": "object",
                "properties": {
                    "priority": {
                        "type": "integer",
                        "description": "The priority of this rule",
                    },
                    "action": {
                        "type": "string",
                        "description": "The action to take when rule matches",
                    },
                    "match": {
                        "type": "object",
                        "description": "The match condition for this rule",
                    },
                    "description": {
                        "type": "string",
                        "description": "A description of the rule",
                    },
                    "preview": {
                        "type": "boolean",
                        "description": "Whether this rule is in preview mode",
                    },
                },
            },
        },
        "fingerprint": {
            "type": "string",
            "description": "Fingerprint of this resource for optimistic locking",
        },
        "adaptiveProtectionConfig": {
            "type": "object",
            "description": "Adaptive protection configuration",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the security policy",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the security policy",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Armor Security Policy Rules
SECURITY_POLICY_RULE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Armor Security Policy Rule",
    "description": "Schema for Google Cloud Armor Security Policy Rules",
    "type": "object",
    "required": ["priority", "action", "match"],
    "properties": {
        "priority": {
            "type": "integer",
            "description": "The priority of the rule (lower = higher priority)",
            "minimum": 0,
            "maximum": 2147483647,
        },
        "action": {
            "type": "string",
            "description": "The action to take when the rule matches",
            "enum": [
                "allow",
                "deny(403)",
                "deny(404)",
                "deny(502)",
                "redirect",
                "rate_based_ban",
                "throttle",
            ],
        },
        "match": {
            "type": "object",
            "description": "The match condition for the rule",
            "properties": {
                "versionedExpr": {
                    "type": "string",
                    "description": "Preconfigured versioned expression",
                },
                "config": {
                    "type": "object",
                    "description": "The configuration for the match",
                },
                "expr": {
                    "type": "object",
                    "description": "Custom CEL expression",
                },
            },
        },
        "description": {
            "type": "string",
            "description": "A description of the rule",
        },
        "preview": {
            "type": "boolean",
            "description": "Whether this rule is in preview mode",
        },
        "rateLimitOptions": {
            "type": "object",
            "description": "Rate limit options for rate-based rules",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "security_policy") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud Armor resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("security_policy" or "security_policy_rule")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "security_policy_rule":
        return SECURITY_POLICY_RULE_SCHEMA
    else:
        return SECURITY_POLICY_SCHEMA
