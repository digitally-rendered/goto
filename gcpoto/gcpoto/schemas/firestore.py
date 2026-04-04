"""JSON Schema definitions for Google Cloud Firestore resources."""

from typing import Dict, Any

FIRESTORE_DOCUMENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Firestore Document",
    "description": "Schema for Google Cloud Firestore Documents",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the document in the format "
            "projects/{project}/databases/{database}/documents/{collection}/{document}",
        },
        "fields": {
            "type": "object",
            "description": "The document's fields and their values",
            "additionalProperties": True,
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the document was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time at which the document was last changed",
        },
    },
    "additionalProperties": False,
}

FIRESTORE_COLLECTION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Firestore Collection",
    "description": "Schema for Google Cloud Firestore Collections",
    "type": "object",
    "required": ["collectionId"],
    "properties": {
        "collectionId": {
            "type": "string",
            "description": "The ID of the collection",
        },
        "documentCount": {
            "type": "integer",
            "description": "The number of documents in the collection",
        },
    },
    "additionalProperties": False,
}

FIRESTORE_INDEX_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Firestore Index",
    "description": "Schema for Google Cloud Firestore Indexes",
    "type": "object",
    "required": ["name", "queryScope", "fields"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the index in the format "
            "projects/{project}/databases/{database}/collectionGroups/{collectionGroup}/indexes/{index}",
        },
        "queryScope": {
            "type": "string",
            "description": "The query scope of the index",
            "enum": ["COLLECTION", "COLLECTION_GROUP"],
        },
        "fields": {
            "type": "array",
            "description": "The fields supported by this index",
            "items": {
                "type": "object",
                "properties": {
                    "fieldPath": {
                        "type": "string",
                        "description": "The field path",
                    },
                    "order": {
                        "type": "string",
                        "description": "The sort order: ASCENDING or DESCENDING",
                        "enum": ["ASCENDING", "DESCENDING"],
                    },
                    "arrayConfig": {
                        "type": "string",
                        "description": "The array configuration: CONTAINS",
                        "enum": ["CONTAINS"],
                    },
                },
            },
        },
        "state": {
            "type": "string",
            "description": "The state of the index",
            "enum": ["CREATING", "READY", "NEEDS_REPAIR"],
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "document") -> Dict[str, Any]:
    """Get the JSON schema for a specific Firestore resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("document", "collection", or "index")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "collection":
        return FIRESTORE_COLLECTION_SCHEMA
    if resource_type.lower() == "index":
        return FIRESTORE_INDEX_SCHEMA
    return FIRESTORE_DOCUMENT_SCHEMA
