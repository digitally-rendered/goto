"""JSON Schema definitions for Media CDN resources."""

from typing import Dict, Any


EDGE_CACHE_SERVICE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Media CDN Edge Cache Service",
    "description": "Schema for Media CDN Edge Cache Services",
    "type": "object",
    "required": ["name", "routing"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the service",
        },
        "location": {
            "type": "string",
            "description": "The location of the service",
        },
        "description": {
            "type": "string",
            "description": "An optional description of the service",
        },
        "routing": {
            "type": "object",
            "description": "Routing configuration for the service",
            "properties": {
                "hostRules": {
                    "type": "array",
                    "description": "Host rules for routing",
                    "items": {
                        "type": "object",
                        "properties": {
                            "hosts": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "pathMatcher": {
                                "type": "string",
                            },
                        },
                    },
                },
                "pathMatchers": {
                    "type": "array",
                    "description": "Path matchers for routing",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "routeRules": {
                                "type": "array",
                                "items": {"type": "object"},
                            },
                        },
                    },
                },
            },
        },
        "edgeSslCertificates": {
            "type": "array",
            "description": "SSL certificates for the edge",
            "items": {"type": "string"},
        },
        "edgeSecurityPolicy": {
            "type": "string",
            "description": "The edge security policy",
        },
        "disableQuic": {
            "type": "boolean",
            "description": "Whether QUIC is disabled",
        },
        "labels": {
            "type": "object",
            "description": "Labels for the service",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the service was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the service was last updated",
        },
    },
    "additionalProperties": False,
}

EDGE_CACHE_ORIGIN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Media CDN Edge Cache Origin",
    "description": "Schema for Media CDN Edge Cache Origins",
    "type": "object",
    "required": ["name", "originAddress"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the origin",
        },
        "location": {
            "type": "string",
            "description": "The location of the origin",
        },
        "originAddress": {
            "type": "string",
            "description": "The origin address (IP or hostname)",
        },
        "protocol": {
            "type": "string",
            "description": "The protocol used to connect to the origin",
            "enum": ["HTTP", "HTTPS", "HTTP2"],
        },
        "port": {
            "type": "integer",
            "description": "The port to connect to the origin",
        },
        "retryConditions": {
            "type": "array",
            "description": "Conditions under which retries are attempted",
            "items": {"type": "string"},
        },
        "maxAttempts": {
            "type": "integer",
            "description": "Maximum number of attempts for origin requests",
        },
        "failoverOrigin": {
            "type": "string",
            "description": "The failover origin resource",
        },
        "labels": {
            "type": "object",
            "description": "Labels for the origin",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the origin was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the origin was last updated",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "edge_cache_service") -> Dict[str, Any]:
    """Get the JSON schema for a specific Media CDN resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("edge_cache_service" or "edge_cache_origin")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "edge_cache_service": EDGE_CACHE_SERVICE_SCHEMA,
        "edge_cache_origin": EDGE_CACHE_ORIGIN_SCHEMA,
    }
    return schemas.get(resource_type.lower(), EDGE_CACHE_SERVICE_SCHEMA)
