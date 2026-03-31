"""JSON Schema definitions for Google Cloud Speech-to-Text resources."""

from typing import Dict, Any


RECOGNITION_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Speech-to-Text Recognition Result",
    "description": "Schema for Google Cloud Speech-to-Text recognition results",
    "type": "object",
    "required": [],
    "properties": {
        "alternatives": {
            "type": "array",
            "description": "List of recognition alternatives",
            "items": {
                "type": "object",
                "properties": {
                    "transcript": {"type": "string"},
                    "confidence": {"type": "number"},
                    "words": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "startTime": {"type": "string"},
                                "endTime": {"type": "string"},
                                "word": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
        "channelTag": {
            "type": "integer",
            "description": "For multi-channel audio, the channel number",
        },
        "resultEndTime": {
            "type": "string",
            "description": "Time offset of the end of the result",
        },
    },
    "additionalProperties": False,
}

RECOGNITION_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Speech-to-Text Recognition Config",
    "description": "Schema for Google Cloud Speech-to-Text recognition configuration",
    "type": "object",
    "required": ["encoding", "sampleRateHertz", "languageCode"],
    "properties": {
        "encoding": {
            "type": "string",
            "description": "Audio encoding format",
            "enum": [
                "ENCODING_UNSPECIFIED",
                "LINEAR16",
                "FLAC",
                "MULAW",
                "AMR",
                "AMR_WB",
                "OGG_OPUS",
                "SPEEX_WITH_HEADER_BYTE",
                "WEBM_OPUS",
            ],
        },
        "sampleRateHertz": {
            "type": "integer",
            "description": "Sample rate in Hertz",
        },
        "languageCode": {
            "type": "string",
            "description": "BCP-47 language code",
        },
        "model": {
            "type": "string",
            "description": "Speech recognition model to use",
        },
        "useEnhanced": {
            "type": "boolean",
            "description": "Whether to use an enhanced model",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "recognition_result") -> Dict[str, Any]:
    """Get the JSON schema for a specific Speech-to-Text resource type.

    Args:
        resource_type: The type of resource
            ("recognition_result" or "recognition_config")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "recognition_result": RECOGNITION_RESULT_SCHEMA,
        "recognition_config": RECOGNITION_CONFIG_SCHEMA,
    }
    return schemas.get(resource_type.lower(), RECOGNITION_RESULT_SCHEMA)
