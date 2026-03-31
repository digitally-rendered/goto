"""JSON Schema definitions for Google Cloud Translation resources."""

from typing import Dict, Any


TRANSLATION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Translation",
    "description": "Schema for Google Cloud Translation results",
    "type": "object",
    "required": ["translatedText"],
    "properties": {
        "translatedText": {
            "type": "string",
            "description": "The translated text",
        },
        "detectedLanguageCode": {
            "type": "string",
            "description": "The BCP-47 language code of the detected source language",
        },
        "model": {
            "type": "string",
            "description": "The model used for translation",
        },
    },
    "additionalProperties": False,
}

DETECTED_LANGUAGE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Detected Language",
    "description": "Schema for Google Cloud Translation detected language results",
    "type": "object",
    "required": ["languageCode", "confidence"],
    "properties": {
        "languageCode": {
            "type": "string",
            "description": "The BCP-47 language code of the detected language",
        },
        "confidence": {
            "type": "number",
            "description": "The confidence of the detection result",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "translation") -> Dict[str, Any]:
    """Get the JSON schema for a specific Translation resource type.

    Args:
        resource_type: The type of resource
            ("translation" or "detected_language")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "translation": TRANSLATION_SCHEMA,
        "detected_language": DETECTED_LANGUAGE_SCHEMA,
    }
    return schemas.get(resource_type.lower(), TRANSLATION_SCHEMA)
