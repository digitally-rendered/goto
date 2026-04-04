"""JSON Schema definitions for Google Cloud reCAPTCHA Enterprise resources."""

from typing import Dict, Any


# JSON Schema for reCAPTCHA Key
RECAPTCHA_KEY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP reCAPTCHA Enterprise Key",
    "description": "Schema for Google Cloud reCAPTCHA Enterprise Key",
    "type": "object",
    "required": ["name", "displayName"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the key",
        },
        "displayName": {
            "type": "string",
            "description": "Human-readable display name of the key",
        },
        "webSettings": {
            "type": "object",
            "description": "Settings for keys that can be used by websites",
            "properties": {
                "allowAllDomains": {"type": "boolean"},
                "allowedDomains": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "allowAmpTraffic": {"type": "boolean"},
                "integrationType": {
                    "type": "string",
                    "enum": [
                        "INTEGRATION_TYPE_UNSPECIFIED",
                        "SCORE",
                        "CHECKBOX",
                        "INVISIBLE",
                    ],
                },
                "challengeSecurityPreference": {
                    "type": "string",
                    "enum": [
                        "CHALLENGE_SECURITY_PREFERENCE_UNSPECIFIED",
                        "USABILITY",
                        "BALANCE",
                        "SECURITY",
                    ],
                },
            },
        },
        "androidSettings": {
            "type": "object",
            "description": "Settings for keys that can be used by Android apps",
            "properties": {
                "allowAllPackageNames": {"type": "boolean"},
                "allowedPackageNames": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
        "iosSettings": {
            "type": "object",
            "description": "Settings for keys that can be used by iOS apps",
            "properties": {
                "allowAllBundleIds": {"type": "boolean"},
                "allowedBundleIds": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the key",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the key",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the key",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Assessment
ASSESSMENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP reCAPTCHA Enterprise Assessment",
    "description": "Schema for Google Cloud reCAPTCHA Enterprise Assessment",
    "type": "object",
    "required": ["event"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the assessment",
        },
        "event": {
            "type": "object",
            "description": "The event being assessed",
            "properties": {
                "token": {"type": "string"},
                "siteKey": {"type": "string"},
                "userAgent": {"type": "string"},
                "userIpAddress": {"type": "string"},
                "expectedAction": {"type": "string"},
            },
        },
        "tokenProperties": {
            "type": "object",
            "description": "Properties of the token provided",
            "properties": {
                "valid": {"type": "boolean"},
                "invalidReason": {"type": "string"},
                "hostname": {"type": "string"},
                "action": {"type": "string"},
                "createTime": {
                    "type": "string",
                    "format": "date-time",
                },
            },
        },
        "riskAnalysis": {
            "type": "object",
            "description": "The risk analysis result",
            "properties": {
                "score": {"type": "number"},
                "reasons": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "recaptcha_key") -> Dict[str, Any]:
    """Get the JSON schema for a specific reCAPTCHA Enterprise resource type.

    Args:
        resource_type: The type of resource to get the schema for
            (``"recaptcha_key"`` or ``"assessment"``).

    Returns:
        The JSON schema for the specified resource type.
    """
    if resource_type.lower() == "assessment":
        return ASSESSMENT_SCHEMA
    else:
        return RECAPTCHA_KEY_SCHEMA
