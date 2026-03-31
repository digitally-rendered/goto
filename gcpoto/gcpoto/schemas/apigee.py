"""JSON Schema definitions for Google Cloud Apigee resources."""

from typing import Dict, Any


# JSON Schema for Apigee Organization
APIGEE_ORGANIZATION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Apigee Organization",
    "description": "Schema for Google Cloud Apigee Organization",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the organization",
        },
        "projectId": {
            "type": "string",
            "description": "The GCP project ID associated with the organization",
        },
        "analyticsRegion": {
            "type": "string",
            "description": "The analytics region for the organization",
        },
        "authorizedNetwork": {
            "type": "string",
            "description": "The authorized network for the organization",
        },
        "runtimeType": {
            "type": "string",
            "description": "The runtime type of the organization",
            "enum": ["CLOUD", "HYBRID"],
        },
        "state": {
            "type": "string",
            "description": "The current state of the organization",
            "enum": [
                "STATE_UNSPECIFIED",
                "CREATING",
                "ACTIVE",
                "DELETING",
            ],
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the organization",
            "additionalProperties": {"type": "string"},
        },
        "createdAt": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the organization",
        },
        "lastModifiedAt": {
            "type": "string",
            "format": "date-time",
            "description": "The last modification time of the organization",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Apigee Environment
APIGEE_ENVIRONMENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Apigee Environment",
    "description": "Schema for Google Cloud Apigee Environment",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the environment",
        },
        "displayName": {
            "type": "string",
            "description": "Display name for the environment",
        },
        "description": {
            "type": "string",
            "description": "Description of the environment",
        },
        "state": {
            "type": "string",
            "description": "The current state of the environment",
            "enum": [
                "STATE_UNSPECIFIED",
                "CREATING",
                "ACTIVE",
                "DELETING",
            ],
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the environment",
            "additionalProperties": {"type": "string"},
        },
        "createdAt": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the environment",
        },
        "lastModifiedAt": {
            "type": "string",
            "format": "date-time",
            "description": "The last modification time of the environment",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Apigee API Proxy
APIGEE_API_PROXY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Apigee API Proxy",
    "description": "Schema for Google Cloud Apigee API Proxy",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the API proxy",
        },
        "revision": {
            "type": "array",
            "description": "List of revisions for this proxy",
            "items": {"type": "string"},
        },
        "latestRevisionId": {
            "type": "string",
            "description": "The latest revision ID",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the API proxy",
            "additionalProperties": {"type": "string"},
        },
        "createdAt": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the API proxy",
        },
        "lastModifiedAt": {
            "type": "string",
            "format": "date-time",
            "description": "The last modification time of the API proxy",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "organization") -> Dict[str, Any]:
    """Get the JSON schema for a specific Apigee resource type.

    Args:
        resource_type: The type of resource to get the schema for
            (``"organization"``, ``"environment"``, or ``"api_proxy"``).

    Returns:
        The JSON schema for the specified resource type.
    """
    schemas = {
        "organization": APIGEE_ORGANIZATION_SCHEMA,
        "environment": APIGEE_ENVIRONMENT_SCHEMA,
        "api_proxy": APIGEE_API_PROXY_SCHEMA,
    }
    return schemas.get(resource_type.lower(), APIGEE_ORGANIZATION_SCHEMA)
