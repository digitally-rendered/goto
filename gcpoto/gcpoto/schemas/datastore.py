"""JSON Schema definitions for Google Cloud Datastore resources."""

from typing import Dict, Any

DATASTORE_ENTITY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Datastore Entity",
    "description": "Schema for Google Cloud Datastore Entities",
    "type": "object",
    "required": ["key"],
    "properties": {
        "key": {
            "type": "object",
            "description": "The entity key, containing partitionId and path",
            "properties": {
                "partitionId": {
                    "type": "object",
                    "properties": {
                        "projectId": {"type": "string"},
                        "namespaceId": {"type": "string"},
                    },
                },
                "path": {
                    "type": "array",
                    "description": "The entity path consisting of kind/id pairs",
                    "items": {
                        "type": "object",
                        "properties": {
                            "kind": {"type": "string"},
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                        },
                    },
                },
            },
        },
        "properties": {
            "type": "object",
            "description": "The entity properties",
            "additionalProperties": True,
        },
    },
    "additionalProperties": False,
}

DATASTORE_ENTITY_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Datastore EntityResult",
    "description": "Schema for Google Cloud Datastore EntityResults",
    "type": "object",
    "required": ["entity"],
    "properties": {
        "entity": {
            "type": "object",
            "description": "The result entity",
        },
        "cursor": {
            "type": "string",
            "description": "A cursor that points to the position after the result entity",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "entity") -> Dict[str, Any]:
    """Get the JSON schema for a specific Datastore resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("entity" or "entity_result")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "entity_result":
        return DATASTORE_ENTITY_RESULT_SCHEMA
    return DATASTORE_ENTITY_SCHEMA
