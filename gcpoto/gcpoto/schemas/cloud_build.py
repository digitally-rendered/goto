"""JSON Schema definitions for Google Cloud Build resources."""

from typing import Dict, Any

# JSON Schema for Cloud Build Builds
BUILD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Build",
    "description": "Schema for Google Cloud Build Builds",
    "type": "object",
    "required": ["steps"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique ID of the build",
        },
        "name": {
            "type": "string",
            "description": "The name of the build",
        },
        "projectId": {
            "type": "string",
            "description": "The ID of the Cloud Platform project",
        },
        "status": {
            "type": "string",
            "description": "The status of the build",
            "enum": [
                "STATUS_UNKNOWN",
                "QUEUED",
                "WORKING",
                "SUCCESS",
                "FAILURE",
                "INTERNAL_ERROR",
                "TIMEOUT",
                "CANCELLED",
                "EXPIRED",
            ],
        },
        "source": {
            "type": "object",
            "description": "The source code to build",
            "properties": {
                "storageSource": {
                    "type": "object",
                    "description": "Cloud Storage source",
                    "properties": {
                        "bucket": {"type": "string"},
                        "object": {"type": "string"},
                        "generation": {"type": "string"},
                    },
                },
                "repoSource": {
                    "type": "object",
                    "description": "Cloud Source Repository source",
                    "properties": {
                        "projectId": {"type": "string"},
                        "repoName": {"type": "string"},
                        "branchName": {"type": "string"},
                        "tagName": {"type": "string"},
                        "commitSha": {"type": "string"},
                    },
                },
            },
        },
        "steps": {
            "type": "array",
            "description": "The build steps",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The container image name",
                    },
                    "args": {
                        "type": "array",
                        "description": "Arguments to the step",
                        "items": {"type": "string"},
                    },
                    "env": {
                        "type": "array",
                        "description": "Environment variables",
                        "items": {"type": "string"},
                    },
                    "dir": {
                        "type": "string",
                        "description": "Working directory",
                    },
                    "id": {
                        "type": "string",
                        "description": "Unique identifier for the step",
                    },
                    "waitFor": {
                        "type": "array",
                        "description": "Step IDs to wait for",
                        "items": {"type": "string"},
                    },
                    "entrypoint": {
                        "type": "string",
                        "description": "Entrypoint for the step",
                    },
                    "timeout": {
                        "type": "string",
                        "description": "Timeout for the step",
                    },
                },
            },
        },
        "results": {
            "type": "object",
            "description": "Results of the build",
            "properties": {
                "images": {
                    "type": "array",
                    "description": "Built images",
                    "items": {"type": "object"},
                },
                "buildStepImages": {
                    "type": "array",
                    "description": "Images from build steps",
                    "items": {"type": "string"},
                },
                "artifactManifest": {
                    "type": "string",
                    "description": "Manifest of artifacts",
                },
            },
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The timestamp when the build was created",
        },
        "startTime": {
            "type": "string",
            "format": "date-time",
            "description": "The timestamp when the build started",
        },
        "finishTime": {
            "type": "string",
            "format": "date-time",
            "description": "The timestamp when the build finished",
        },
        "timeout": {
            "type": "string",
            "description": "Amount of time the build should be allowed to run",
        },
        "images": {
            "type": "array",
            "description": "List of images expected to be built",
            "items": {"type": "string"},
        },
        "artifacts": {
            "type": "object",
            "description": "Artifacts produced by the build",
            "properties": {
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "objects": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "paths": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
        },
        "logsBucket": {
            "type": "string",
            "description": "Cloud Storage bucket for build logs",
        },
        "sourceProvenance": {
            "type": "object",
            "description": "Provenance of the source",
        },
        "options": {
            "type": "object",
            "description": "Special options for this build",
            "properties": {
                "machineType": {
                    "type": "string",
                    "description": "Machine type for the build",
                },
                "diskSizeGb": {
                    "type": "string",
                    "description": "Disk size in GB",
                },
                "logging": {
                    "type": "string",
                    "description": "Logging mode",
                },
                "substitutionOption": {
                    "type": "string",
                    "description": "Substitution option",
                },
            },
        },
        "substitutions": {
            "type": "object",
            "description": "Substitution variables",
            "additionalProperties": {"type": "string"},
        },
        "labels": {
            "type": "object",
            "description": "User-defined labels for the build",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Build Triggers
BUILD_TRIGGER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Build Trigger",
    "description": "Schema for Google Cloud Build Triggers",
    "type": "object",
    "required": ["name"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique ID of the trigger",
        },
        "name": {
            "type": "string",
            "description": "The name of the trigger",
        },
        "projectId": {
            "type": "string",
            "description": "The ID of the Cloud Platform project",
        },
        "description": {
            "type": "string",
            "description": "Human-readable description of the trigger",
        },
        "disabled": {
            "type": "boolean",
            "description": "Whether the trigger is disabled",
        },
        "substitutions": {
            "type": "object",
            "description": "Substitution variables for the trigger",
            "additionalProperties": {"type": "string"},
        },
        "filename": {
            "type": "string",
            "description": "Path to the build configuration file",
        },
        "triggerTemplate": {
            "type": "object",
            "description": "Template describing source changes to trigger",
            "properties": {
                "projectId": {"type": "string"},
                "repoName": {"type": "string"},
                "branchName": {"type": "string"},
                "tagName": {"type": "string"},
                "commitSha": {"type": "string"},
            },
        },
        "github": {
            "type": "object",
            "description": "GitHub-specific trigger configuration",
            "properties": {
                "owner": {"type": "string"},
                "name": {"type": "string"},
                "push": {"type": "object"},
                "pullRequest": {"type": "object"},
            },
        },
        "pubsubConfig": {
            "type": "object",
            "description": "Pub/Sub configuration for the trigger",
            "properties": {
                "subscription": {"type": "string"},
                "topic": {"type": "string"},
                "serviceAccountEmail": {"type": "string"},
            },
        },
        "webhookConfig": {
            "type": "object",
            "description": "Webhook configuration for the trigger",
            "properties": {
                "secret": {"type": "string"},
                "state": {"type": "string"},
            },
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The timestamp when the trigger was created",
        },
        "labels": {
            "type": "object",
            "description": "User-defined labels for the trigger",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "build") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud Build resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("build" or "trigger")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "trigger":
        return BUILD_TRIGGER_SCHEMA
    else:  # Default to build
        return BUILD_SCHEMA
