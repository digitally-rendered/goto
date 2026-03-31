"""JSON Schema definitions for Google Cloud Storage Transfer Service resources."""

from typing import Dict, Any

# JSON Schema for Transfer Jobs
TRANSFER_JOB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Storage Transfer Job",
    "description": "Schema for Google Cloud Storage Transfer Jobs",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the transfer job",
        },
        "description": {
            "type": "string",
            "description": "A description of the transfer job",
        },
        "projectId": {
            "type": "string",
            "description": "The ID of the GCP project that owns the job",
        },
        "status": {
            "type": "string",
            "description": "The status of the transfer job",
            "enum": ["ENABLED", "DISABLED", "DELETED"],
        },
        "schedule": {
            "type": "object",
            "description": "The schedule for the transfer job",
            "properties": {
                "scheduleStartDate": {
                    "type": "object",
                    "description": "The start date of the schedule",
                    "properties": {
                        "year": {"type": "integer"},
                        "month": {"type": "integer"},
                        "day": {"type": "integer"},
                    },
                },
                "scheduleEndDate": {
                    "type": "object",
                    "description": "The end date of the schedule",
                    "properties": {
                        "year": {"type": "integer"},
                        "month": {"type": "integer"},
                        "day": {"type": "integer"},
                    },
                },
                "startTimeOfDay": {
                    "type": "object",
                    "description": "The time of day to start the job",
                    "properties": {
                        "hours": {"type": "integer"},
                        "minutes": {"type": "integer"},
                        "seconds": {"type": "integer"},
                    },
                },
                "repeatInterval": {
                    "type": "string",
                    "description": "Interval between runs (e.g. '86400s')",
                },
            },
        },
        "transferSpec": {
            "type": "object",
            "description": "The transfer specification",
            "properties": {
                "gcsDataSource": {
                    "type": "object",
                    "description": "GCS data source",
                    "properties": {
                        "bucketName": {"type": "string"},
                        "path": {"type": "string"},
                    },
                },
                "gcsDataSink": {
                    "type": "object",
                    "description": "GCS data sink",
                    "properties": {
                        "bucketName": {"type": "string"},
                        "path": {"type": "string"},
                    },
                },
                "awsS3DataSource": {
                    "type": "object",
                    "description": "AWS S3 data source",
                },
                "httpDataSource": {
                    "type": "object",
                    "description": "HTTP data source",
                },
                "objectConditions": {
                    "type": "object",
                    "description": "Object conditions for the transfer",
                },
                "transferOptions": {
                    "type": "object",
                    "description": "Transfer options",
                },
            },
        },
        "notificationConfig": {
            "type": "object",
            "description": "Notification configuration",
            "properties": {
                "pubsubTopic": {
                    "type": "string",
                    "description": "Pub/Sub topic for notifications",
                },
                "eventTypes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Event types to send notifications for",
                },
                "payloadFormat": {
                    "type": "string",
                    "description": "The payload format for notifications",
                },
            },
        },
        "latestOperationName": {
            "type": "string",
            "description": "The name of the most recent transfer operation",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the transfer job",
            "additionalProperties": {"type": "string"},
        },
        "creationTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the job was created",
        },
        "lastModificationTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the job was last modified",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Transfer Operations
TRANSFER_OPERATION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Storage Transfer Operation",
    "description": "Schema for Google Cloud Storage Transfer Operations",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the transfer operation",
        },
        "metadata": {
            "type": "object",
            "description": "The operation metadata",
            "properties": {
                "transferJobName": {
                    "type": "string",
                    "description": "The transfer job this operation belongs to",
                },
                "projectId": {
                    "type": "string",
                    "description": "The ID of the project",
                },
                "status": {
                    "type": "string",
                    "description": "The status of the operation",
                    "enum": [
                        "STATUS_UNSPECIFIED",
                        "IN_PROGRESS",
                        "PAUSED",
                        "SUCCESS",
                        "FAILED",
                        "ABORTED",
                        "QUEUED",
                    ],
                },
                "startTime": {
                    "type": "string",
                    "format": "date-time",
                    "description": "The start time of the operation",
                },
                "endTime": {
                    "type": "string",
                    "format": "date-time",
                    "description": "The end time of the operation",
                },
                "counters": {
                    "type": "object",
                    "description": "Transfer counters",
                    "properties": {
                        "objectsFoundFromSource": {"type": "string"},
                        "bytesFoundFromSource": {"type": "string"},
                        "objectsCopiedToSink": {"type": "string"},
                        "bytesCopiedToSink": {"type": "string"},
                    },
                },
                "errorBreakdowns": {
                    "type": "array",
                    "description": "Error breakdowns for the operation",
                    "items": {
                        "type": "object",
                        "properties": {
                            "errorCode": {"type": "string"},
                            "errorCount": {"type": "string"},
                            "errorLogEntries": {
                                "type": "array",
                                "items": {"type": "object"},
                            },
                        },
                    },
                },
            },
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "transfer_job") -> Dict[str, Any]:
    """Get the JSON schema for a specific Storage Transfer resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("transfer_job" or "transfer_operation")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "transfer_job": TRANSFER_JOB_SCHEMA,
        "transfer_operation": TRANSFER_OPERATION_SCHEMA,
    }
    return schemas.get(resource_type, TRANSFER_JOB_SCHEMA)
