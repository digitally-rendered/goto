"""JSON Schema definitions for Google Cloud Endpoints resources."""

from typing import Dict, Any


# JSON Schema for Managed Service
MANAGED_SERVICE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Endpoints Managed Service",
    "description": "Schema for Google Cloud Endpoints Managed Service",
    "type": "object",
    "required": ["serviceName"],
    "properties": {
        "serviceName": {
            "type": "string",
            "description": "The name of the managed service",
        },
        "producerProjectId": {
            "type": "string",
            "description": "ID of the project that produces and owns this service",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Service Config
SERVICE_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Endpoints Service Config",
    "description": "Schema for Google Cloud Endpoints Service Config",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the service config",
        },
        "id": {
            "type": "string",
            "description": "The unique identifier of the service config",
        },
        "serviceName": {
            "type": "string",
            "description": "The name of the service this config belongs to",
        },
        "title": {
            "type": "string",
            "description": "The product title for this service",
        },
        "documentation": {
            "type": "object",
            "description": "Documentation configuration",
        },
        "apis": {
            "type": "array",
            "description": "A list of API interfaces exported by this service",
            "items": {"type": "object"},
        },
        "quota": {
            "type": "object",
            "description": "Quota configuration",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the service config",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the service config",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "managed_service") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud Endpoints resource type.

    Args:
        resource_type: The type of resource to get the schema for
            (``"managed_service"`` or ``"service_config"``).

    Returns:
        The JSON schema for the specified resource type.
    """
    if resource_type.lower() == "service_config":
        return SERVICE_CONFIG_SCHEMA
    else:
        return MANAGED_SERVICE_SCHEMA
