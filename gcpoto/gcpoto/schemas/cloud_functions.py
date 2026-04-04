"""JSON Schema definitions for Google Cloud Functions resources."""

from typing import Dict, Any


CLOUD_FUNCTION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Function",
    "description": "Schema for Google Cloud Functions",
    "type": "object",
    "required": ["name", "runtime", "entryPoint"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified name of the function (projects/{project}/locations/{location}/functions/{function})",
        },
        "runtime": {
            "type": "string",
            "description": "The runtime environment for the function (e.g. python39, nodejs16, go119)",
        },
        "entryPoint": {
            "type": "string",
            "description": "The name of the function entry point in the source code",
        },
        "sourceArchiveUrl": {
            "type": "string",
            "description": "The Google Cloud Storage URL pointing to the zip archive with the function source code",
        },
        "sourceRepository": {
            "type": "object",
            "description": "The source repository where the function is defined",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the source repository",
                },
            },
        },
        "sourceUploadUrl": {
            "type": "string",
            "description": "The Google Cloud Storage signed URL for uploading function source code",
        },
        "status": {
            "type": "string",
            "description": "The status of the function deployment",
            "enum": [
                "CLOUD_FUNCTION_STATUS_UNSPECIFIED",
                "ACTIVE",
                "OFFLINE",
                "DEPLOY_IN_PROGRESS",
                "DELETE_IN_PROGRESS",
                "UNKNOWN",
            ],
        },
        "timeout": {
            "type": "string",
            "description": "The function execution timeout (e.g. '60s')",
        },
        "availableMemoryMb": {
            "type": "integer",
            "description": "The amount of memory in MB available for the function",
            "minimum": 128,
            "maximum": 8192,
        },
        "serviceAccountEmail": {
            "type": "string",
            "description": "The email of the service account used by the function",
        },
        "environmentVariables": {
            "type": "object",
            "description": "Environment variables available during function execution",
            "additionalProperties": {"type": "string"},
        },
        "buildEnvironmentVariables": {
            "type": "object",
            "description": "Environment variables available during build time",
            "additionalProperties": {"type": "string"},
        },
        "maxInstances": {
            "type": "integer",
            "description": "The maximum number of function instances",
            "minimum": 0,
        },
        "minInstances": {
            "type": "integer",
            "description": "The minimum number of function instances",
            "minimum": 0,
        },
        "vpcConnector": {
            "type": "string",
            "description": "The VPC Network Connector that the function can connect to",
        },
        "ingressSettings": {
            "type": "string",
            "description": "The ingress settings for the function",
            "enum": [
                "INGRESS_SETTINGS_UNSPECIFIED",
                "ALLOW_ALL",
                "ALLOW_INTERNAL_ONLY",
                "ALLOW_INTERNAL_AND_GCLB",
            ],
        },
        "httpsTrigger": {
            "type": "object",
            "description": "HTTPS trigger configuration",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The deployed URL for the function",
                },
                "securityLevel": {
                    "type": "string",
                    "description": "The security level for the function",
                    "enum": [
                        "SECURITY_LEVEL_UNSPECIFIED",
                        "SECURE_ALWAYS",
                        "SECURE_OPTIONAL",
                    ],
                },
            },
        },
        "eventTrigger": {
            "type": "object",
            "description": "Event trigger configuration",
            "properties": {
                "eventType": {
                    "type": "string",
                    "description": "The type of event to observe",
                },
                "resource": {
                    "type": "string",
                    "description": "The resource from which to observe events",
                },
                "service": {
                    "type": "string",
                    "description": "The hostname of the service that should be observed",
                },
                "failurePolicy": {
                    "type": "object",
                    "description": "Specifies policy for failed executions",
                    "properties": {
                        "retry": {
                            "type": "object",
                            "description": "Retry on failure policy",
                        },
                    },
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the function",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the function was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the function was last updated",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "function") -> Dict[str, Any]:
    """Get the JSON schema for a Cloud Functions resource type.

    Args:
        resource_type: The type of resource to get the schema for
            (currently only "function" is supported)

    Returns:
        The JSON schema for the specified resource type
    """
    return CLOUD_FUNCTION_SCHEMA
