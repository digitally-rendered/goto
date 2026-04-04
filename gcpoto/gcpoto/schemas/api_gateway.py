"""JSON Schema definitions for Google Cloud API Gateway resources."""

from typing import Dict, Any


# JSON Schema for API Gateway
API_GATEWAY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP API Gateway",
    "description": "Schema for Google Cloud API Gateway",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the gateway",
        },
        "displayName": {
            "type": "string",
            "description": "Display name for the gateway",
        },
        "state": {
            "type": "string",
            "description": "The current state of the gateway",
            "enum": [
                "STATE_UNSPECIFIED",
                "CREATING",
                "ACTIVE",
                "FAILED",
                "DELETING",
                "UPDATING",
            ],
        },
        "defaultHostname": {
            "type": "string",
            "description": "The default hostname of the gateway",
        },
        "apiConfig": {
            "type": "string",
            "description": "The API config associated with this gateway",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the gateway",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the gateway",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the gateway",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for API Config
API_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP API Gateway API Config",
    "description": "Schema for Google Cloud API Gateway API Config",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the API config",
        },
        "displayName": {
            "type": "string",
            "description": "Display name for the API config",
        },
        "state": {
            "type": "string",
            "description": "The current state of the API config",
            "enum": [
                "STATE_UNSPECIFIED",
                "CREATING",
                "ACTIVE",
                "FAILED",
                "DELETING",
                "ACTIVATING",
            ],
        },
        "serviceConfigId": {
            "type": "string",
            "description": "The service config ID from Service Management",
        },
        "gatewayServiceAccount": {
            "type": "string",
            "description": "The service account associated with the gateway",
        },
        "openapiDocuments": {
            "type": "array",
            "description": "OpenAPI specification documents",
            "items": {
                "type": "object",
                "properties": {
                    "document": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "contents": {"type": "string"},
                        },
                    },
                },
            },
        },
        "grpcServices": {
            "type": "array",
            "description": "gRPC service definitions",
            "items": {
                "type": "object",
                "properties": {
                    "fileDescriptorSet": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "contents": {"type": "string"},
                        },
                    },
                    "source": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "contents": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the API config",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the API config",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the API config",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "gateway") -> Dict[str, Any]:
    """Get the JSON schema for a specific API Gateway resource type.

    Args:
        resource_type: The type of resource to get the schema for
            (``"gateway"`` or ``"api_config"``).

    Returns:
        The JSON schema for the specified resource type.
    """
    if resource_type.lower() == "api_config":
        return API_CONFIG_SCHEMA
    else:
        return API_GATEWAY_SCHEMA
