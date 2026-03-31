"""JSON Schema definitions for Google Cloud IAM resources."""

from typing import Dict, Any

# JSON Schema for IAM Service Accounts
SERVICE_ACCOUNT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP IAM Service Account",
    "description": "Schema for Google Cloud IAM Service Accounts",
    "type": "object",
    "required": ["name", "projectId"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the service account",
        },
        "projectId": {
            "type": "string",
            "description": "The GCP project ID that owns the service account",
        },
        "uniqueId": {
            "type": "string",
            "description": "The unique numeric ID for the service account",
        },
        "email": {
            "type": "string",
            "format": "email",
            "description": "The email address of the service account",
        },
        "displayName": {
            "type": "string",
            "description": "A user-specified display name for the service account",
        },
        "description": {
            "type": "string",
            "description": "A user-specified description of the service account",
        },
        "disabled": {
            "type": "boolean",
            "description": "Whether the service account is disabled",
        },
        "oauth2ClientId": {
            "type": "string",
            "description": "The OAuth 2.0 client ID for the service account",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the service account",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the service account",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for IAM Service Account Keys
SERVICE_ACCOUNT_KEY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP IAM Service Account Key",
    "description": "Schema for Google Cloud IAM Service Account Keys",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the service account key",
        },
        "keyAlgorithm": {
            "type": "string",
            "description": "The algorithm used for the key",
            "enum": [
                "KEY_ALG_UNSPECIFIED",
                "KEY_ALG_RSA_1024",
                "KEY_ALG_RSA_2048",
            ],
        },
        "keyOrigin": {
            "type": "string",
            "description": "The origin of the key",
            "enum": [
                "ORIGIN_UNSPECIFIED",
                "USER_PROVIDED",
                "GOOGLE_PROVIDED",
            ],
        },
        "keyType": {
            "type": "string",
            "description": "The type of the key",
            "enum": [
                "KEY_TYPE_UNSPECIFIED",
                "USER_MANAGED",
                "SYSTEM_MANAGED",
            ],
        },
        "validAfterTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time after which the key is valid",
        },
        "validBeforeTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time before which the key is valid",
        },
        "privateKeyData": {
            "type": "string",
            "description": "The private key data (only returned on creation)",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for IAM Roles
ROLE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP IAM Role",
    "description": "Schema for Google Cloud IAM Roles",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the role",
        },
        "title": {
            "type": "string",
            "description": "A human-readable title for the role",
        },
        "description": {
            "type": "string",
            "description": "A description of the role",
        },
        "includedPermissions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The permissions included in this role",
        },
        "stage": {
            "type": "string",
            "description": "The launch stage of the role",
            "enum": ["ALPHA", "BETA", "GA", "DEPRECATED"],
        },
        "deleted": {
            "type": "boolean",
            "description": "Whether the role has been deleted",
        },
        "etag": {
            "type": "string",
            "description": "An etag for optimistic concurrency control",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "service_account") -> Dict[str, Any]:
    """Get the JSON schema for a specific IAM resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("service_account", "service_account_key", or "role")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "service_account_key":
        return SERVICE_ACCOUNT_KEY_SCHEMA
    elif resource_type.lower() == "role":
        return ROLE_SCHEMA
    else:
        return SERVICE_ACCOUNT_SCHEMA
