"""JSON Schema definitions for Google Cloud KMS resources."""

from typing import Dict, Any

# JSON Schema for KMS Key Rings
KEY_RING_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP KMS Key Ring",
    "description": "Schema for Google Cloud KMS Key Rings",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name for the key ring",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which this key ring was created",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for KMS Crypto Keys
CRYPTO_KEY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP KMS Crypto Key",
    "description": "Schema for Google Cloud KMS Crypto Keys",
    "type": "object",
    "required": ["name", "purpose"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name for the crypto key",
        },
        "purpose": {
            "type": "string",
            "description": "The immutable purpose of this crypto key",
            "enum": [
                "ENCRYPT_DECRYPT",
                "ASYMMETRIC_SIGN",
                "ASYMMETRIC_DECRYPT",
                "MAC",
            ],
        },
        "primary": {
            "type": "object",
            "description": "The primary version of this crypto key",
            "properties": {
                "name": {"type": "string"},
                "state": {"type": "string"},
                "algorithm": {"type": "string"},
                "protectionLevel": {"type": "string"},
                "generateTime": {
                    "type": "string",
                    "format": "date-time",
                },
                "createTime": {
                    "type": "string",
                    "format": "date-time",
                },
            },
        },
        "rotationPeriod": {
            "type": "string",
            "description": "The period for automatic key rotation (e.g. '7776000s' for 90 days)",
        },
        "nextRotationTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the next automatic rotation will occur",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the crypto key",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which this crypto key was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which this crypto key was last updated",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for KMS Crypto Key Versions
CRYPTO_KEY_VERSION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP KMS Crypto Key Version",
    "description": "Schema for Google Cloud KMS Crypto Key Versions",
    "type": "object",
    "required": ["name", "state", "algorithm"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name for the crypto key version",
        },
        "state": {
            "type": "string",
            "description": "The current state of the crypto key version",
            "enum": [
                "CRYPTO_KEY_VERSION_STATE_UNSPECIFIED",
                "PENDING_GENERATION",
                "ENABLED",
                "DISABLED",
                "DESTROYED",
                "DESTROY_SCHEDULED",
                "PENDING_IMPORT",
                "IMPORT_FAILED",
            ],
        },
        "algorithm": {
            "type": "string",
            "description": "The algorithm of this crypto key version",
        },
        "protectionLevel": {
            "type": "string",
            "description": "The protection level of this crypto key version",
            "enum": ["SOFTWARE", "HSM", "EXTERNAL", "EXTERNAL_VPC"],
        },
        "generateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which this version's key material was generated",
        },
        "destroyTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time this version is scheduled for destruction",
        },
        "destroyEventTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time this version's key material was destroyed",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which this crypto key version was created",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "key_ring") -> Dict[str, Any]:
    """Get the JSON schema for a specific KMS resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("key_ring", "crypto_key", or "crypto_key_version")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "key_ring": KEY_RING_SCHEMA,
        "crypto_key": CRYPTO_KEY_SCHEMA,
        "crypto_key_version": CRYPTO_KEY_VERSION_SCHEMA,
    }
    return schemas.get(resource_type, KEY_RING_SCHEMA)
