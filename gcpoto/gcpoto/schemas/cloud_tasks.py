"""JSON Schema definitions for Google Cloud Tasks resources."""

from typing import Dict, Any

# JSON Schema for Cloud Tasks Queues
TASK_QUEUE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Tasks Queue",
    "description": "Schema for Google Cloud Tasks Queues",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified queue name",
        },
        "state": {
            "type": "string",
            "description": "The state of the queue",
            "enum": ["RUNNING", "PAUSED", "DISABLED"],
        },
        "rateLimits": {
            "type": "object",
            "description": "Rate limits for task dispatches",
            "properties": {
                "maxDispatchesPerSecond": {
                    "type": "number",
                    "description": "Maximum rate at which tasks are dispatched",
                },
                "maxBurstSize": {
                    "type": "integer",
                    "description": "Maximum number of tasks that can be dispatched in a burst",
                },
                "maxConcurrentDispatches": {
                    "type": "integer",
                    "description": "Maximum number of concurrent task dispatches",
                },
            },
        },
        "retryConfig": {
            "type": "object",
            "description": "Retry configuration for tasks in the queue",
            "properties": {
                "maxAttempts": {
                    "type": "integer",
                    "description": "Maximum number of attempts for a task",
                },
                "maxRetryDuration": {
                    "type": "string",
                    "description": "Maximum duration to retry a failed task",
                },
                "minBackoff": {
                    "type": "string",
                    "description": "Minimum backoff duration between retries",
                },
                "maxBackoff": {
                    "type": "string",
                    "description": "Maximum backoff duration between retries",
                },
                "maxDoublings": {
                    "type": "integer",
                    "description": "Maximum number of times the backoff interval is doubled",
                },
            },
        },
        "purgeTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last time this queue was purged",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the queue",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the queue was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last time the queue was updated",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Tasks Tasks
TASK_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Tasks Task",
    "description": "Schema for Google Cloud Tasks Tasks",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified task name",
        },
        "scheduleTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time when the task is scheduled to be attempted",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time that the task was created",
        },
        "dispatchDeadline": {
            "type": "string",
            "description": "The deadline for requests sent to the worker",
        },
        "dispatchCount": {
            "type": "integer",
            "description": "The number of attempts dispatched",
        },
        "responseCount": {
            "type": "integer",
            "description": "The number of attempts which have received a response",
        },
        "firstAttempt": {
            "type": "object",
            "description": "Information about the first attempt",
            "properties": {
                "scheduleTime": {
                    "type": "string",
                    "format": "date-time",
                },
                "dispatchTime": {
                    "type": "string",
                    "format": "date-time",
                },
                "responseTime": {
                    "type": "string",
                    "format": "date-time",
                },
                "responseStatus": {"type": "object"},
            },
        },
        "lastAttempt": {
            "type": "object",
            "description": "Information about the most recent attempt",
            "properties": {
                "scheduleTime": {
                    "type": "string",
                    "format": "date-time",
                },
                "dispatchTime": {
                    "type": "string",
                    "format": "date-time",
                },
                "responseTime": {
                    "type": "string",
                    "format": "date-time",
                },
                "responseStatus": {"type": "object"},
            },
        },
        "httpRequest": {
            "type": "object",
            "description": "HTTP request for the task",
            "properties": {
                "url": {"type": "string", "description": "The full URL"},
                "httpMethod": {
                    "type": "string",
                    "description": "The HTTP method",
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
                    "description": "HTTP request headers",
                    "additionalProperties": {"type": "string"},
                },
                "body": {
                    "type": "string",
                    "description": "HTTP request body (base64 encoded)",
                },
            },
        },
        "appEngineHttpRequest": {
            "type": "object",
            "description": "App Engine HTTP request for the task",
            "properties": {
                "httpMethod": {
                    "type": "string",
                    "description": "The HTTP method",
                },
                "appEngineRouting": {
                    "type": "object",
                    "description": "Task-level routing settings",
                },
                "relativeUri": {
                    "type": "string",
                    "description": "The relative URI",
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP request headers",
                    "additionalProperties": {"type": "string"},
                },
                "body": {
                    "type": "string",
                    "description": "HTTP request body (base64 encoded)",
                },
            },
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "queue") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud Tasks resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("queue" or "task")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "task":
        return TASK_SCHEMA
    else:  # Default to queue
        return TASK_QUEUE_SCHEMA
