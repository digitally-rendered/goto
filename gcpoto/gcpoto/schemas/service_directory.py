"""JSON Schema definitions for Google Cloud Service Directory resources."""

from typing import Dict, Any


# JSON Schema for Service Directory Namespaces
NAMESPACE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Service Directory Namespace",
    "description": "Schema for Google Cloud Service Directory Namespaces",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The namespace name (projects/{project}/locations/{location}/namespaces/{namespace})",
        },
        "labels": {
            "type": "object",
            "description": "Labels for the namespace",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the namespace",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the namespace",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Service Directory Services
SERVICE_ENTRY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Service Directory Service",
    "description": "Schema for Google Cloud Service Directory Services",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The service name (projects/{project}/locations/{location}/namespaces/{namespace}/services/{service})",
        },
        "metadata": {
            "type": "object",
            "description": "Metadata for the service",
            "additionalProperties": {"type": "string"},
        },
        "endpoints": {
            "type": "array",
            "description": "Endpoints associated with the service",
            "items": {"type": "object"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the service",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the service",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Service Directory Endpoints
ENDPOINT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Service Directory Endpoint",
    "description": "Schema for Google Cloud Service Directory Endpoints",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The endpoint name (projects/{project}/locations/{location}/namespaces/{namespace}/services/{service}/endpoints/{endpoint})",
        },
        "address": {
            "type": "string",
            "description": "The IP address of the endpoint",
        },
        "port": {
            "type": "integer",
            "description": "The port number of the endpoint",
            "minimum": 0,
            "maximum": 65535,
        },
        "metadata": {
            "type": "object",
            "description": "Metadata for the endpoint",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the endpoint",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the endpoint",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "namespace") -> Dict[str, Any]:
    """Get the JSON schema for a specific Service Directory resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("namespace", "service", or "endpoint")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "namespace": NAMESPACE_SCHEMA,
        "service": SERVICE_ENTRY_SCHEMA,
        "endpoint": ENDPOINT_SCHEMA,
    }
    return schemas.get(resource_type.lower(), NAMESPACE_SCHEMA)
