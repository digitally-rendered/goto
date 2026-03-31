"""JSON Schema definitions for Google Cloud Scheduler resources."""

from typing import Dict, Any

SCHEDULER_JOB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Scheduler Job",
    "description": "Schema for Google Cloud Scheduler Jobs",
    "type": "object",
    "required": ["name", "schedule", "timeZone"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The full resource name of the job",
        },
        "description": {
            "type": "string",
            "description": "A human-readable description of the job",
        },
        "schedule": {
            "type": "string",
            "description": "Cron expression for the job schedule",
        },
        "timeZone": {
            "type": "string",
            "description": "The time zone for the cron schedule (e.g. America/New_York)",
        },
        "state": {
            "type": "string",
            "description": "The state of the job",
            "enum": ["ENABLED", "PAUSED", "DISABLED", "UPDATE_FAILED"],
        },
        "retryConfig": {
            "type": "object",
            "description": "Settings for retrying failed job attempts",
            "properties": {
                "retryCount": {
                    "type": "integer",
                    "description": "Number of times to retry a failed job",
                },
                "maxRetryDuration": {
                    "type": "string",
                    "description": "Maximum duration for retries (in seconds, e.g. '0s')",
                },
                "minBackoffDuration": {
                    "type": "string",
                    "description": "Minimum backoff duration (in seconds, e.g. '5s')",
                },
                "maxBackoffDuration": {
                    "type": "string",
                    "description": "Maximum backoff duration (in seconds, e.g. '3600s')",
                },
                "maxDoublings": {
                    "type": "integer",
                    "description": "Maximum number of times the backoff interval is doubled",
                },
            },
        },
        "attemptDeadline": {
            "type": "string",
            "description": "The deadline for job attempts (duration in seconds, e.g. '180s')",
        },
        "httpTarget": {
            "type": "object",
            "description": "HTTP target configuration",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "The full URI of the HTTP target",
                },
                "httpMethod": {
                    "type": "string",
                    "description": "The HTTP method to use",
                    "enum": [
                        "HTTP_METHOD_UNSPECIFIED",
                        "POST",
                        "GET",
                        "HEAD",
                        "PUT",
                        "DELETE",
                        "PATCH",
                        "OPTIONS",
                    ],
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP headers to include in the request",
                    "additionalProperties": {"type": "string"},
                },
                "body": {
                    "type": "string",
                    "description": "The body of the HTTP request (base64 encoded)",
                },
            },
        },
        "pubsubTarget": {
            "type": "object",
            "description": "Pub/Sub target configuration",
            "properties": {
                "topicName": {
                    "type": "string",
                    "description": "The full resource name of the Pub/Sub topic",
                },
                "data": {
                    "type": "string",
                    "description": "The message data (base64 encoded)",
                },
                "attributes": {
                    "type": "object",
                    "description": "Attributes for the Pub/Sub message",
                    "additionalProperties": {"type": "string"},
                },
            },
        },
        "appEngineHttpTarget": {
            "type": "object",
            "description": "App Engine HTTP target configuration",
            "properties": {
                "httpMethod": {
                    "type": "string",
                    "description": "The HTTP method to use",
                },
                "appEngineRouting": {
                    "type": "object",
                    "description": "App Engine routing information",
                },
                "relativeUri": {
                    "type": "string",
                    "description": "The relative URI of the App Engine handler",
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP headers to include",
                    "additionalProperties": {"type": "string"},
                },
                "body": {
                    "type": "string",
                    "description": "The body of the HTTP request (base64 encoded)",
                },
            },
        },
        "lastAttemptTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the last job attempt started",
        },
        "scheduleTime": {
            "type": "string",
            "format": "date-time",
            "description": "The next time the job is scheduled to run",
        },
        "status": {
            "type": "object",
            "description": "The status of the last execution attempt",
            "properties": {
                "code": {
                    "type": "integer",
                    "description": "The status code",
                },
                "message": {
                    "type": "string",
                    "description": "The status message",
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the job",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the job",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the job",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "job") -> Dict[str, Any]:
    """Get the JSON schema for a Cloud Scheduler resource type.

    Args:
        resource_type: The type of resource to get the schema for (default: "job")

    Returns:
        The JSON schema for the specified resource type
    """
    return SCHEDULER_JOB_SCHEMA
