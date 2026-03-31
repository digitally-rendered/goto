"""JSON Schema definitions for Google Cloud Data Catalog resources."""

from typing import Dict, Any

ENTRY_GROUP_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Data Catalog Entry Group",
    "description": "Schema for Google Cloud Data Catalog Entry Groups",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the entry group",
        },
        "displayName": {
            "type": "string",
            "description": "Display name of the entry group",
        },
        "description": {
            "type": "string",
            "description": "Description of the entry group",
        },
        "dataCatalogTimestamps": {
            "type": "object",
            "description": "Timestamps for the entry group",
            "properties": {
                "createTime": {
                    "type": "string",
                    "format": "date-time",
                },
                "updateTime": {
                    "type": "string",
                    "format": "date-time",
                },
            },
        },
    },
    "additionalProperties": False,
}

ENTRY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Data Catalog Entry",
    "description": "Schema for Google Cloud Data Catalog Entries",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the entry",
        },
        "type": {
            "type": "string",
            "description": "The type of the entry",
        },
        "linkedResource": {
            "type": "string",
            "description": "The resource this entry represents",
        },
        "displayName": {
            "type": "string",
            "description": "Display name of the entry",
        },
        "description": {
            "type": "string",
            "description": "Description of the entry",
        },
        "schema": {
            "type": "object",
            "description": "Schema of the entry",
        },
        "sourceSystemTimestamps": {
            "type": "object",
            "description": "Timestamps from the source system",
            "properties": {
                "createTime": {
                    "type": "string",
                    "format": "date-time",
                },
                "updateTime": {
                    "type": "string",
                    "format": "date-time",
                },
            },
        },
    },
    "additionalProperties": False,
}

TAG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Data Catalog Tag",
    "description": "Schema for Google Cloud Data Catalog Tags",
    "type": "object",
    "required": ["template", "fields"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the tag",
        },
        "template": {
            "type": "string",
            "description": "The tag template name",
        },
        "fields": {
            "type": "object",
            "description": "Tag fields",
            "additionalProperties": {"type": "object"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "entry_group") -> Dict[str, Any]:
    """Get the JSON schema for a specific Data Catalog resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("entry_group", "entry", or "tag")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "entry_group": ENTRY_GROUP_SCHEMA,
        "entry": ENTRY_SCHEMA,
        "tag": TAG_SCHEMA,
    }
    return schemas.get(resource_type.lower(), ENTRY_GROUP_SCHEMA)
