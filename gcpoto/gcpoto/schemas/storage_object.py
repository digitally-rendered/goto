"""JSON Schema definitions for Google Cloud Storage Objects."""

from typing import Dict, Any

# JSON Schema for Cloud Storage Objects
STORAGE_OBJECT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Storage Object",
    "description": "Schema for Google Cloud Storage objects",
    "type": "object",
    "required": ["name", "bucket"],
    "properties": {
        "id": {"type": "string", "description": "The unique identifier for the object"},
        "name": {"type": "string", "description": "The name of the object"},
        "bucket": {"type": "string", "description": "The bucket containing the object"},
        "contentType": {
            "type": "string",
            "description": "The content type of the object data",
        },
        "size": {"type": "integer", "description": "Size of the object in bytes"},
        "etag": {"type": "string", "description": "HTTP 1.1 Entity tag for the object"},
        "generation": {
            "type": "string",
            "description": "The content generation of this object",
        },
        "md5Hash": {"type": "string", "description": "MD5 hash of the object data"},
        "crc32c": {
            "type": "string",
            "description": "CRC32c checksum of the object data",
        },
        "timeCreated": {
            "type": "string",
            "format": "date-time",
            "description": "The time the object was created",
        },
        "updated": {
            "type": "string",
            "format": "date-time",
            "description": "The time the object was last updated",
        },
        "storageClass": {
            "type": "string",
            "description": "Storage class of the object",
            "enum": ["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"],
        },
        "contentEncoding": {
            "type": "string",
            "description": "Content encoding of the object data",
        },
        "contentDisposition": {
            "type": "string",
            "description": "Content disposition of the object data",
        },
        "cacheControl": {
            "type": "string",
            "description": "Cache control for the object data",
        },
        "metadata": {
            "type": "object",
            "description": "User-provided metadata for the object",
            "additionalProperties": {"type": "string"},
        },
        "acl": {
            "type": "array",
            "description": "Access control list for the object",
            "items": {
                "type": "object",
                "properties": {
                    "entity": {"type": "string"},
                    "role": {"type": "string"},
                },
            },
        },
    },
    "additionalProperties": False,
}


def get_schema() -> Dict[str, Any]:
    """Get the JSON schema for Storage Objects.

    Returns:
        The JSON schema for Storage Objects
    """
    return STORAGE_OBJECT_SCHEMA
