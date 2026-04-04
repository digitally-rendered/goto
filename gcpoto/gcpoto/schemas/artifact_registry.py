"""JSON Schema definitions for Google Cloud Artifact Registry resources."""

from typing import Dict, Any

REPOSITORY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Artifact Registry Repository",
    "description": "Schema for Google Cloud Artifact Registry Repositories",
    "type": "object",
    "required": ["name", "format"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the repository in the format "
            "projects/*/locations/*/repositories/*",
        },
        "format": {
            "type": "string",
            "description": "The format of packages stored in this repository",
            "enum": ["DOCKER", "MAVEN", "NPM", "APT", "YUM", "PYTHON", "GO"],
        },
        "description": {
            "type": "string",
            "description": "The user-provided description of the repository",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the repository",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time when the repository was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time when the repository was last updated",
        },
        "sizeBytes": {
            "type": "string",
            "description": "The size, in bytes, of all artifact storage in this repository",
        },
        "cleanupPolicies": {
            "type": "object",
            "description": "Cleanup policies for this repository",
        },
        "mode": {
            "type": "string",
            "description": "The mode of the repository",
            "enum": [
                "STANDARD_REPOSITORY",
                "VIRTUAL_REPOSITORY",
                "REMOTE_REPOSITORY",
            ],
        },
    },
    "additionalProperties": False,
}

DOCKER_IMAGE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Artifact Registry Docker Image",
    "description": "Schema for Google Cloud Artifact Registry Docker Images",
    "type": "object",
    "required": ["name", "uri"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the docker image",
        },
        "uri": {
            "type": "string",
            "description": "The URI of the docker image",
        },
        "tags": {
            "type": "array",
            "description": "Tags associated with this docker image",
            "items": {"type": "string"},
        },
        "imageSizeBytes": {
            "type": "string",
            "description": "The size of the docker image in bytes",
        },
        "mediaType": {
            "type": "string",
            "description": "The media type of the docker image",
        },
        "uploadTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time when the docker image was uploaded",
        },
        "buildTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time when the docker image was built",
        },
    },
    "additionalProperties": False,
}

PACKAGE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Artifact Registry Package",
    "description": "Schema for Google Cloud Artifact Registry Packages",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the package",
        },
        "displayName": {
            "type": "string",
            "description": "The display name of the package",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time when the package was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time when the package was last updated",
        },
    },
    "additionalProperties": False,
}

PACKAGE_VERSION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Artifact Registry Package Version",
    "description": "Schema for Google Cloud Artifact Registry Package Versions",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the version",
        },
        "description": {
            "type": "string",
            "description": "Optional description of the version",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time when the version was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time when the version was last updated",
        },
        "relatedTags": {
            "type": "array",
            "description": "Tags associated with this version",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The tag name",
                    },
                    "version": {
                        "type": "string",
                        "description": "The version the tag refers to",
                    },
                },
            },
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "repository") -> Dict[str, Any]:
    """Get the JSON schema for a specific Artifact Registry resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("repository", "docker_image", "package", or "version")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "repository": REPOSITORY_SCHEMA,
        "docker_image": DOCKER_IMAGE_SCHEMA,
        "package": PACKAGE_SCHEMA,
        "version": PACKAGE_VERSION_SCHEMA,
    }
    return schemas.get(resource_type.lower(), REPOSITORY_SCHEMA)
