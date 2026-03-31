"""JSON Schema definitions for Binary Authorization resources."""

from typing import Dict, Any


POLICY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Binary Authorization Policy",
    "description": "Schema for Binary Authorization Policies",
    "type": "object",
    "required": ["name", "defaultAdmissionRule"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the policy",
        },
        "globalPolicyEvaluationMode": {
            "type": "string",
            "description": "The global policy evaluation mode",
            "enum": ["ENABLE", "DISABLE"],
        },
        "defaultAdmissionRule": {
            "type": "object",
            "description": "The default admission rule",
            "properties": {
                "evaluationMode": {
                    "type": "string",
                    "description": "How this admission rule will be evaluated",
                },
                "enforcementMode": {
                    "type": "string",
                    "description": "The action when a pod is denied",
                },
                "requireAttestationsBy": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Required attestors",
                },
            },
        },
        "clusterAdmissionRules": {
            "type": "object",
            "description": "Per-cluster admission rules",
            "additionalProperties": True,
        },
        "istioServiceIdentityAdmissionRules": {
            "type": "object",
            "description": "Per-Istio-service-identity admission rules",
            "additionalProperties": True,
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the policy",
        },
    },
    "additionalProperties": False,
}

ATTESTOR_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Binary Authorization Attestor",
    "description": "Schema for Binary Authorization Attestors",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the attestor",
        },
        "description": {
            "type": "string",
            "description": "A description of the attestor",
        },
        "userOwnedGrafeasNote": {
            "type": "object",
            "description": "A Grafeas note reference",
            "properties": {
                "noteReference": {
                    "type": "string",
                    "description": "The Grafeas note resource name",
                },
                "publicKeys": {
                    "type": "array",
                    "description": "Public keys that verify attestations",
                    "items": {"type": "object"},
                },
            },
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the attestor",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the attestor",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "policy") -> Dict[str, Any]:
    """Get the JSON schema for a specific Binary Authorization resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("policy" or "attestor")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "attestor":
        return ATTESTOR_SCHEMA
    else:
        return POLICY_SCHEMA
