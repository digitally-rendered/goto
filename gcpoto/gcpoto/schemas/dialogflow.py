"""JSON Schema definitions for Google Cloud Dialogflow CX resources."""

from typing import Dict, Any


AGENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Dialogflow CX Agent",
    "description": "Schema for Google Cloud Dialogflow CX agents",
    "type": "object",
    "required": ["displayName", "defaultLanguageCode", "timeZone"],
    "properties": {
        "name": {"type": "string", "description": "Full resource name of the agent"},
        "displayName": {"type": "string", "description": "Display name of the agent"},
        "defaultLanguageCode": {"type": "string", "description": "Default language code (e.g., en)"},
        "supportedLanguageCodes": {
            "type": "array",
            "description": "Supported language codes",
            "items": {"type": "string"},
        },
        "timeZone": {"type": "string", "description": "Time zone (e.g., America/New_York)"},
        "description": {"type": "string", "description": "Description of the agent"},
        "startFlow": {"type": "string", "description": "Resource name of the start flow"},
        "createTime": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
        "updateTime": {"type": "string", "format": "date-time", "description": "Last update timestamp"},
        "labels": {
            "type": "object",
            "description": "Labels associated with the agent",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

FLOW_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Dialogflow CX Flow",
    "description": "Schema for Google Cloud Dialogflow CX flows",
    "type": "object",
    "required": ["displayName"],
    "properties": {
        "name": {"type": "string", "description": "Full resource name of the flow"},
        "displayName": {"type": "string", "description": "Display name of the flow"},
        "description": {"type": "string", "description": "Description of the flow"},
        "transitionRoutes": {
            "type": "array",
            "description": "Transition routes for the flow",
            "items": {"type": "object"},
        },
        "eventHandlers": {
            "type": "array",
            "description": "Event handlers for the flow",
            "items": {"type": "object"},
        },
        "createTime": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
        "updateTime": {"type": "string", "format": "date-time", "description": "Last update timestamp"},
    },
    "additionalProperties": False,
}

INTENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Dialogflow CX Intent",
    "description": "Schema for Google Cloud Dialogflow CX intents",
    "type": "object",
    "required": ["displayName"],
    "properties": {
        "name": {"type": "string", "description": "Full resource name of the intent"},
        "displayName": {"type": "string", "description": "Display name of the intent"},
        "trainingPhrases": {
            "type": "array",
            "description": "Training phrases for the intent",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "parts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "parameterId": {"type": "string"},
                            },
                        },
                    },
                    "repeatCount": {"type": "integer"},
                },
            },
        },
        "parameters": {
            "type": "array",
            "description": "Parameters for the intent",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "entityType": {"type": "string"},
                    "isList": {"type": "boolean"},
                    "redact": {"type": "boolean"},
                },
            },
        },
        "priority": {"type": "integer", "description": "Priority of the intent"},
        "createTime": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
        "updateTime": {"type": "string", "format": "date-time", "description": "Last update timestamp"},
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "agent") -> Dict[str, Any]:
    """Get the JSON schema for a specific Dialogflow CX resource type.

    Args:
        resource_type: The type of resource ("agent", "flow", "intent")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "agent": AGENT_SCHEMA,
        "flow": FLOW_SCHEMA,
        "intent": INTENT_SCHEMA,
    }
    return schemas.get(resource_type.lower(), AGENT_SCHEMA)
