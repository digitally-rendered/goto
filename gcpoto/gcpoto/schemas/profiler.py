"""JSON Schema definitions for Google Cloud Profiler resources."""

from typing import Dict, Any

# JSON Schema for Cloud Profiler Profile
PROFILE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Profiler Profile",
    "description": "Schema for Google Cloud Profiler profiles",
    "type": "object",
    "required": ["profileType"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the profile",
        },
        "profileType": {
            "type": "string",
            "description": "The type of profile",
            "enum": ["CPU", "HEAP", "THREADS", "CONTENTION", "WALL"],
        },
        "deployment": {
            "type": "object",
            "description": "Deployment information",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "The project ID",
                },
                "target": {
                    "type": "string",
                    "description": "The target of the deployment",
                },
                "labels": {
                    "type": "object",
                    "description": "Labels for the deployment",
                    "additionalProperties": {"type": "string"},
                },
            },
        },
        "duration": {
            "type": "string",
            "description": "Duration of the profile (e.g., '10s')",
        },
        "profileBytes": {
            "type": "string",
            "description": "Base64-encoded profile data",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the profile",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "profile") -> Dict[str, Any]:
    """Get the JSON schema for a Cloud Profiler resource type.

    Args:
        resource_type: The type of resource to get the schema for

    Returns:
        The JSON schema for the specified resource type
    """
    return PROFILE_SCHEMA
