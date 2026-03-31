"""JSON Schema definitions for Google Cloud Vision AI resources."""

from typing import Dict, Any


ANNOTATION_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Vision AI Annotation Result",
    "description": "Schema for Google Cloud Vision AI annotation results",
    "type": "object",
    "required": [],
    "properties": {
        "labelAnnotations": {
            "type": "array",
            "description": "Label annotations detected in the image",
            "items": {
                "type": "object",
                "properties": {
                    "mid": {"type": "string"},
                    "description": {"type": "string"},
                    "score": {"type": "number"},
                    "topicality": {"type": "number"},
                },
            },
        },
        "faceAnnotations": {
            "type": "array",
            "description": "Face annotations detected in the image",
            "items": {
                "type": "object",
                "properties": {
                    "boundingPoly": {"type": "object"},
                    "detectionConfidence": {"type": "number"},
                    "joyLikelihood": {"type": "string"},
                    "sorrowLikelihood": {"type": "string"},
                    "angerLikelihood": {"type": "string"},
                    "surpriseLikelihood": {"type": "string"},
                },
            },
        },
        "fullTextAnnotation": {
            "type": "object",
            "description": "Full text annotation detected in the image",
            "properties": {
                "text": {"type": "string"},
                "pages": {"type": "array", "items": {"type": "object"}},
            },
        },
        "localizedObjectAnnotations": {
            "type": "array",
            "description": "Localized object annotations detected in the image",
            "items": {
                "type": "object",
                "properties": {
                    "mid": {"type": "string"},
                    "name": {"type": "string"},
                    "score": {"type": "number"},
                    "boundingPoly": {"type": "object"},
                },
            },
        },
        "logoAnnotations": {
            "type": "array",
            "description": "Logo annotations detected in the image",
            "items": {
                "type": "object",
                "properties": {
                    "mid": {"type": "string"},
                    "description": {"type": "string"},
                    "score": {"type": "number"},
                    "boundingPoly": {"type": "object"},
                },
            },
        },
        "landmarkAnnotations": {
            "type": "array",
            "description": "Landmark annotations detected in the image",
            "items": {
                "type": "object",
                "properties": {
                    "mid": {"type": "string"},
                    "description": {"type": "string"},
                    "score": {"type": "number"},
                    "locations": {"type": "array", "items": {"type": "object"}},
                },
            },
        },
        "safeSearchAnnotation": {
            "type": "object",
            "description": "Safe search annotation for the image",
            "properties": {
                "adult": {"type": "string"},
                "spoof": {"type": "string"},
                "medical": {"type": "string"},
                "violence": {"type": "string"},
                "racy": {"type": "string"},
            },
        },
        "webDetection": {
            "type": "object",
            "description": "Web detection results for the image",
            "properties": {
                "webEntities": {"type": "array", "items": {"type": "object"}},
                "fullMatchingImages": {
                    "type": "array",
                    "items": {"type": "object"},
                },
                "pagesWithMatchingImages": {
                    "type": "array",
                    "items": {"type": "object"},
                },
            },
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "annotation_result") -> Dict[str, Any]:
    """Get the JSON schema for a specific Vision AI resource type.

    Args:
        resource_type: The type of resource ("annotation_result")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "annotation_result": ANNOTATION_RESULT_SCHEMA,
    }
    return schemas.get(resource_type.lower(), ANNOTATION_RESULT_SCHEMA)
