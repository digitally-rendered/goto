"""JSON Schema definitions for Google Cloud CDN / Backend Services resources."""

from typing import Dict, Any


# JSON Schema for Backend Services
BACKEND_SERVICE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Backend Service",
    "description": "Schema for Google Cloud Backend Services",
    "type": "object",
    "required": ["name"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the backend service",
        },
        "name": {
            "type": "string",
            "description": "The name of the backend service",
        },
        "description": {
            "type": "string",
            "description": "A description of the backend service",
        },
        "backends": {
            "type": "array",
            "description": "The list of backends that serve this backend service",
            "items": {
                "type": "object",
                "properties": {
                    "group": {
                        "type": "string",
                        "description": "URL of the instance group or NEG",
                    },
                    "balancingMode": {
                        "type": "string",
                        "description": "Balancing mode (UTILIZATION, RATE, CONNECTION)",
                    },
                    "capacityScaler": {
                        "type": "number",
                        "description": "Capacity scaler (0.0 to 1.0)",
                    },
                    "maxUtilization": {
                        "type": "number",
                        "description": "Maximum utilization (0.0 to 1.0)",
                    },
                },
            },
        },
        "healthChecks": {
            "type": "array",
            "items": {"type": "string"},
            "description": "URLs of health checks for the backend service",
        },
        "protocol": {
            "type": "string",
            "description": "The protocol used to communicate with backends",
            "enum": ["HTTP", "HTTPS", "HTTP2", "TCP", "SSL", "GRPC"],
        },
        "port": {
            "type": "integer",
            "description": "The TCP port to connect on the backend",
        },
        "portName": {
            "type": "string",
            "description": "A named port on the backend instance groups",
        },
        "timeoutSec": {
            "type": "integer",
            "description": "Backend service timeout in seconds",
        },
        "enableCDN": {
            "type": "boolean",
            "description": "Whether Cloud CDN is enabled",
        },
        "cdnPolicy": {
            "type": "object",
            "description": "Cloud CDN configuration",
            "properties": {
                "cacheMode": {
                    "type": "string",
                    "description": "Cache mode (USE_ORIGIN_HEADERS, FORCE_CACHE_ALL, CACHE_ALL_STATIC)",
                },
                "defaultTtl": {
                    "type": "integer",
                    "description": "Default TTL in seconds",
                },
                "maxTtl": {
                    "type": "integer",
                    "description": "Maximum TTL in seconds",
                },
                "clientTtl": {
                    "type": "integer",
                    "description": "Client TTL in seconds",
                },
                "signedUrlCacheMaxAgeSec": {
                    "type": "integer",
                    "description": "Maximum age for signed URL cache",
                },
            },
        },
        "loadBalancingScheme": {
            "type": "string",
            "description": "The load balancing scheme",
            "enum": ["EXTERNAL", "INTERNAL", "INTERNAL_SELF_MANAGED", "INTERNAL_MANAGED"],
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the backend service",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the backend service",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for URL Maps
URL_MAP_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP URL Map",
    "description": "Schema for Google Cloud URL Maps",
    "type": "object",
    "required": ["name", "defaultService"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the URL map",
        },
        "name": {
            "type": "string",
            "description": "The name of the URL map",
        },
        "description": {
            "type": "string",
            "description": "A description of the URL map",
        },
        "defaultService": {
            "type": "string",
            "description": "The full URL of the default backend service",
        },
        "hostRules": {
            "type": "array",
            "description": "Host rules for routing requests",
            "items": {
                "type": "object",
                "properties": {
                    "hosts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of host patterns to match",
                    },
                    "pathMatcher": {
                        "type": "string",
                        "description": "Name of the path matcher to use",
                    },
                },
            },
        },
        "pathMatchers": {
            "type": "array",
            "description": "Path matchers for routing requests",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the path matcher",
                    },
                    "defaultService": {
                        "type": "string",
                        "description": "Default service for this path matcher",
                    },
                    "pathRules": {
                        "type": "array",
                        "description": "Path rules",
                    },
                },
            },
        },
        "fingerprint": {
            "type": "string",
            "description": "Fingerprint for optimistic locking",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the URL map",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the URL map",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Health Checks
HEALTH_CHECK_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Health Check",
    "description": "Schema for Google Cloud Health Checks",
    "type": "object",
    "required": ["name", "type"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the health check",
        },
        "name": {
            "type": "string",
            "description": "The name of the health check",
        },
        "description": {
            "type": "string",
            "description": "A description of the health check",
        },
        "type": {
            "type": "string",
            "description": "The type of health check",
            "enum": ["HTTP", "HTTPS", "TCP", "SSL", "HTTP2"],
        },
        "checkIntervalSec": {
            "type": "integer",
            "description": "How often to send a health check",
        },
        "timeoutSec": {
            "type": "integer",
            "description": "How long to wait before claiming failure",
        },
        "healthyThreshold": {
            "type": "integer",
            "description": "Consecutive successes required to mark healthy",
        },
        "unhealthyThreshold": {
            "type": "integer",
            "description": "Consecutive failures required to mark unhealthy",
        },
        "httpHealthCheck": {
            "type": "object",
            "description": "HTTP health check configuration",
            "properties": {
                "port": {"type": "integer"},
                "requestPath": {"type": "string"},
                "host": {"type": "string"},
            },
        },
        "httpsHealthCheck": {
            "type": "object",
            "description": "HTTPS health check configuration",
            "properties": {
                "port": {"type": "integer"},
                "requestPath": {"type": "string"},
                "host": {"type": "string"},
            },
        },
        "tcpHealthCheck": {
            "type": "object",
            "description": "TCP health check configuration",
            "properties": {
                "port": {"type": "integer"},
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the health check",
            "additionalProperties": {"type": "string"},
        },
        "creationTimestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the health check",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "backend_service") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud CDN resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("backend_service", "url_map", or "health_check")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "url_map": URL_MAP_SCHEMA,
        "health_check": HEALTH_CHECK_SCHEMA,
    }
    return schemas.get(resource_type.lower(), BACKEND_SERVICE_SCHEMA)
