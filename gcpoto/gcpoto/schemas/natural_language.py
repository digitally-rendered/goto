"""JSON Schema definitions for Google Cloud Natural Language resources."""

from typing import Dict, Any


NL_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Natural Language Result",
    "description": "Schema for Google Cloud Natural Language analysis results",
    "type": "object",
    "required": [],
    "properties": {
        "sentences": {
            "type": "array",
            "description": "Sentences in the input document",
            "items": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "beginOffset": {"type": "integer"},
                        },
                    },
                    "sentiment": {
                        "type": "object",
                        "properties": {
                            "magnitude": {"type": "number"},
                            "score": {"type": "number"},
                        },
                    },
                },
            },
        },
        "tokens": {
            "type": "array",
            "description": "Tokens and their syntactic information",
            "items": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "beginOffset": {"type": "integer"},
                        },
                    },
                    "partOfSpeech": {
                        "type": "object",
                        "properties": {
                            "tag": {"type": "string"},
                        },
                    },
                    "dependencyEdge": {
                        "type": "object",
                        "properties": {
                            "headTokenIndex": {"type": "integer"},
                            "label": {"type": "string"},
                        },
                    },
                    "lemma": {"type": "string"},
                },
            },
        },
        "entities": {
            "type": "array",
            "description": "Entities found in the input text",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "salience": {"type": "number"},
                    "mentions": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                    "metadata": {"type": "object"},
                },
            },
        },
        "documentSentiment": {
            "type": "object",
            "description": "Overall sentiment of the document",
            "properties": {
                "magnitude": {"type": "number"},
                "score": {"type": "number"},
            },
        },
        "categories": {
            "type": "array",
            "description": "Categories that the document belongs to",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "confidence": {"type": "number"},
                },
            },
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "nl_result") -> Dict[str, Any]:
    """Get the JSON schema for a specific Natural Language resource type.

    Args:
        resource_type: The type of resource ("nl_result")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "nl_result": NL_RESULT_SCHEMA,
    }
    return schemas.get(resource_type.lower(), NL_RESULT_SCHEMA)
