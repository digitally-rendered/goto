"""JSON Schema definitions for Google Cloud Logging resources."""

from typing import Dict, Any

# JSON Schema for Cloud Logging Log Entries
LOG_ENTRY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Logging Log Entry",
    "description": "Schema for Google Cloud Logging log entries",
    "type": "object",
    "required": ["logName"],
    "properties": {
        "logName": {
            "type": "string",
            "description": "The resource name of the log",
        },
        "severity": {
            "type": "string",
            "description": "The severity of the log entry",
            "enum": [
                "DEFAULT",
                "DEBUG",
                "INFO",
                "NOTICE",
                "WARNING",
                "ERROR",
                "CRITICAL",
                "ALERT",
                "EMERGENCY",
            ],
        },
        "textPayload": {
            "type": "string",
            "description": "The log entry payload as a text string",
        },
        "jsonPayload": {
            "type": "object",
            "description": "The log entry payload as a JSON object",
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "The time the event described by the log entry occurred",
        },
        "resource": {
            "type": "object",
            "description": "The monitored resource that produced the log entry",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "The monitored resource type",
                },
                "labels": {
                    "type": "object",
                    "description": "Labels for the monitored resource",
                    "additionalProperties": {"type": "string"},
                },
            },
        },
        "insertId": {
            "type": "string",
            "description": "A unique identifier for the log entry",
        },
        "trace": {
            "type": "string",
            "description": "The trace associated with the log entry",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the log entry",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Logging Sinks
LOG_SINK_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Logging Sink",
    "description": "Schema for Google Cloud Logging sinks",
    "type": "object",
    "required": ["name", "destination"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the sink",
        },
        "destination": {
            "type": "string",
            "description": "The export destination (e.g., storage bucket, BigQuery dataset, Pub/Sub topic)",
        },
        "filter": {
            "type": "string",
            "description": "An advanced logs filter to match log entries for export",
        },
        "description": {
            "type": "string",
            "description": "A description of this sink",
        },
        "disabled": {
            "type": "boolean",
            "description": "Whether the sink is disabled",
        },
        "writerIdentity": {
            "type": "string",
            "description": "The service account used for writing to the destination",
        },
        "includeChildren": {
            "type": "boolean",
            "description": "Whether to include log entries from child projects/folders/orgs",
        },
        "exclusions": {
            "type": "array",
            "description": "Log entries to exclude from the sink",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "A name for the exclusion rule",
                    },
                    "filter": {
                        "type": "string",
                        "description": "An advanced logs filter to match log entries to exclude",
                    },
                    "description": {
                        "type": "string",
                        "description": "A description of the exclusion rule",
                    },
                    "disabled": {
                        "type": "boolean",
                        "description": "Whether the exclusion rule is disabled",
                    },
                },
            },
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the sink",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the sink",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Logging Metrics
LOG_METRIC_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Logging Metric",
    "description": "Schema for Google Cloud Logging log-based metrics",
    "type": "object",
    "required": ["name", "filter"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the metric",
        },
        "description": {
            "type": "string",
            "description": "A description of this metric",
        },
        "filter": {
            "type": "string",
            "description": "An advanced logs filter to match log entries",
        },
        "metricDescriptor": {
            "type": "object",
            "description": "The metric descriptor associated with the metric",
        },
        "valueExtractor": {
            "type": "string",
            "description": "A value_extractor for the metric",
        },
        "labelExtractors": {
            "type": "object",
            "description": "A map from label key to extractor expression",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the metric",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the metric",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "log_entry") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud Logging resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("log_entry", "sink", or "metric")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "sink":
        return LOG_SINK_SCHEMA
    elif resource_type.lower() == "metric":
        return LOG_METRIC_SCHEMA
    else:
        return LOG_ENTRY_SCHEMA
