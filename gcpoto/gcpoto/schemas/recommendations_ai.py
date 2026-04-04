"""JSON Schema definitions for Google Cloud Recommendations AI resources."""

from typing import Dict, Any

CATALOG_ITEM_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Recommendations AI Catalog Item",
    "description": "Schema for Google Cloud Recommendations AI Catalog Items",
    "type": "object",
    "required": ["id", "title", "categoryHierarchies"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The catalog item ID",
        },
        "name": {
            "type": "string",
            "description": "The fully qualified resource name",
        },
        "title": {
            "type": "string",
            "description": "The catalog item title",
        },
        "categoryHierarchies": {
            "type": "array",
            "description": "Category hierarchies for the item",
            "items": {
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "description": {
            "type": "string",
            "description": "The catalog item description",
        },
        "itemAttributes": {
            "type": "object",
            "description": "Extra item attributes",
        },
        "languageCode": {
            "type": "string",
            "description": "Language code (BCP-47)",
        },
        "productMetadata": {
            "type": "object",
            "description": "Product metadata for retail items",
        },
    },
    "additionalProperties": False,
}

PREDICTION_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Recommendations AI Prediction Result",
    "description": "Schema for Google Cloud Recommendations AI Prediction Results",
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "description": "List of recommended items",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "metadata": {"type": "object"},
                },
            },
        },
        "attributionToken": {
            "type": "string",
            "description": "Attribution token for tracking",
        },
        "missingIds": {
            "type": "array",
            "description": "IDs of items missing from the catalog",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "catalog_item") -> Dict[str, Any]:
    """Get the JSON schema for a specific Recommendations AI resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("catalog_item" or "prediction_result")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "prediction_result":
        return PREDICTION_RESULT_SCHEMA
    return CATALOG_ITEM_SCHEMA
