"""JSON Schema definitions for Google Cloud Batch resources."""

from typing import Dict, Any

# JSON Schema for Batch Jobs
BATCH_JOB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Batch Job",
    "description": "Schema for Google Cloud Batch Jobs",
    "type": "object",
    "required": ["name", "taskGroups"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified job name",
        },
        "status": {
            "type": "object",
            "description": "Current status of the job",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "Job state",
                    "enum": [
                        "STATE_UNSPECIFIED",
                        "QUEUED",
                        "SCHEDULED",
                        "RUNNING",
                        "SUCCEEDED",
                        "FAILED",
                        "DELETION_IN_PROGRESS",
                    ],
                },
                "statusEvents": {
                    "type": "array",
                    "description": "Status events",
                    "items": {"type": "object"},
                },
                "taskGroups": {
                    "type": "object",
                    "description": "Aggregated task status for each task group",
                    "additionalProperties": {"type": "object"},
                },
            },
        },
        "taskGroups": {
            "type": "array",
            "description": "Task groups for the job",
            "items": {
                "type": "object",
                "properties": {
                    "taskSpec": {
                        "type": "object",
                        "description": "Task specification",
                        "properties": {
                            "runnables": {
                                "type": "array",
                                "description": "The sequence of scripts or containers to run",
                                "items": {"type": "object"},
                            },
                            "computeResource": {
                                "type": "object",
                                "description": "Compute resource requirements",
                            },
                            "maxRunDuration": {
                                "type": "string",
                                "description": "Maximum duration the task can run",
                            },
                        },
                    },
                    "taskCount": {
                        "type": "string",
                        "description": "Number of tasks in the group",
                    },
                    "parallelism": {
                        "type": "string",
                        "description": "Max number of tasks that can run in parallel",
                    },
                },
            },
        },
        "allocationPolicy": {
            "type": "object",
            "description": "Compute resource allocation policy",
            "properties": {
                "instances": {
                    "type": "array",
                    "description": "Instance configurations",
                    "items": {"type": "object"},
                },
                "location": {
                    "type": "object",
                    "description": "Location policy",
                },
            },
        },
        "schedulingPolicy": {
            "type": "object",
            "description": "Scheduling policy for task execution",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the job",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the job was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last time the job was updated",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Batch Tasks
BATCH_TASK_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Batch Task",
    "description": "Schema for Google Cloud Batch Tasks",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The fully qualified task name",
        },
        "status": {
            "type": "object",
            "description": "Current status of the task",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "Task state",
                    "enum": [
                        "STATE_UNSPECIFIED",
                        "PENDING",
                        "ASSIGNED",
                        "RUNNING",
                        "FAILED",
                        "SUCCEEDED",
                    ],
                },
                "statusEvents": {
                    "type": "array",
                    "description": "Status events",
                    "items": {"type": "object"},
                },
            },
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the task was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last time the task was updated",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "job") -> Dict[str, Any]:
    """Get the JSON schema for a specific Batch resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("job" or "task")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "task":
        return BATCH_TASK_SCHEMA
    else:  # Default to job
        return BATCH_JOB_SCHEMA
