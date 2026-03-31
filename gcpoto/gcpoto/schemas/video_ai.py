"""JSON Schema definitions for Google Cloud Video Intelligence AI resources."""

from typing import Dict, Any

VIDEO_ANNOTATION_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Video Intelligence Annotation Result",
    "description": "Schema for Google Cloud Video Intelligence annotation results",
    "type": "object",
    "properties": {
        "inputUri": {
            "type": "string",
            "description": "The video input URI (Cloud Storage URI)",
        },
        "segmentLabelAnnotations": {
            "type": "array",
            "description": "Label annotations on video level",
            "items": {"type": "object"},
        },
        "shotLabelAnnotations": {
            "type": "array",
            "description": "Label annotations on shot level",
            "items": {"type": "object"},
        },
        "frameLabelAnnotations": {
            "type": "array",
            "description": "Label annotations on frame level",
            "items": {"type": "object"},
        },
        "faceDetectionAnnotations": {
            "type": "array",
            "description": "Face detection annotations",
            "items": {"type": "object"},
        },
        "shotAnnotations": {
            "type": "array",
            "description": "Shot annotations (scene changes)",
            "items": {"type": "object"},
        },
        "explicitAnnotation": {
            "type": "object",
            "description": "Explicit content annotation",
        },
        "speechTranscriptions": {
            "type": "array",
            "description": "Speech transcription results",
            "items": {"type": "object"},
        },
        "textAnnotations": {
            "type": "array",
            "description": "OCR text detection annotations",
            "items": {"type": "object"},
        },
        "objectAnnotations": {
            "type": "array",
            "description": "Object tracking annotations",
            "items": {"type": "object"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "annotation_result") -> Dict[str, Any]:
    """Get the JSON schema for a specific Video Intelligence resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("annotation_result")

    Returns:
        The JSON schema for the specified resource type
    """
    return VIDEO_ANNOTATION_RESULT_SCHEMA
