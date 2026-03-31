"""JSON Schema definitions for Google Cloud Memorystore (Redis) resources."""

from typing import Dict, Any


REDIS_INSTANCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Memorystore Redis Instance",
    "description": "Schema for Google Cloud Memorystore Redis Instances",
    "type": "object",
    "required": ["name", "tier", "memorySizeGb"],
    "properties": {
        "name": {
            "type": "string",
            "description": "Unique name of the resource (projects/{project}/locations/{location}/instances/{instance})",
        },
        "displayName": {
            "type": "string",
            "description": "An arbitrary user-provided name for the instance",
        },
        "tier": {
            "type": "string",
            "description": "The service tier of the instance",
            "enum": ["BASIC", "STANDARD_HA"],
        },
        "memorySizeGb": {
            "type": "integer",
            "description": "Redis memory size in GiB",
            "minimum": 1,
        },
        "host": {
            "type": "string",
            "description": "Hostname or IP address of the exposed Redis endpoint",
        },
        "port": {
            "type": "integer",
            "description": "The port number of the exposed Redis endpoint",
        },
        "currentLocationId": {
            "type": "string",
            "description": "The current zone where the Redis primary node is located",
        },
        "redisVersion": {
            "type": "string",
            "description": "The version of Redis software (e.g. REDIS_7_0)",
        },
        "state": {
            "type": "string",
            "description": "The current state of the instance",
            "enum": [
                "STATE_UNSPECIFIED",
                "CREATING",
                "READY",
                "UPDATING",
                "DELETING",
                "REPAIRING",
                "MAINTENANCE",
                "IMPORTING",
                "FAILING_OVER",
            ],
        },
        "statusMessage": {
            "type": "string",
            "description": "Additional information about the current status",
        },
        "redisConfigs": {
            "type": "object",
            "description": "Redis configuration parameters",
            "additionalProperties": {"type": "string"},
        },
        "authorizedNetwork": {
            "type": "string",
            "description": "The full name of the Google Compute Engine network to which the instance is connected",
        },
        "connectMode": {
            "type": "string",
            "description": "The network connect mode of the Redis instance",
            "enum": [
                "CONNECT_MODE_UNSPECIFIED",
                "DIRECT_PEERING",
                "PRIVATE_SERVICE_ACCESS",
            ],
        },
        "authEnabled": {
            "type": "boolean",
            "description": "Whether AUTH is enabled for the instance",
        },
        "transitEncryptionMode": {
            "type": "string",
            "description": "The TLS mode of the Redis instance",
            "enum": [
                "TRANSIT_ENCRYPTION_MODE_UNSPECIFIED",
                "SERVER_AUTHENTICATION",
                "DISABLED",
            ],
        },
        "maintenancePolicy": {
            "type": "object",
            "description": "The maintenance policy for the instance",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the maintenance policy",
                },
                "weeklyMaintenanceWindow": {
                    "type": "array",
                    "description": "Maintenance window specifications",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day": {
                                "type": "string",
                                "description": "Day of the week",
                            },
                            "startTime": {
                                "type": "object",
                                "description": "Start time of the window",
                                "properties": {
                                    "hours": {"type": "integer"},
                                    "minutes": {"type": "integer"},
                                },
                            },
                            "duration": {
                                "type": "string",
                                "description": "Duration of the window",
                            },
                        },
                    },
                },
            },
        },
        "maintenanceSchedule": {
            "type": "object",
            "description": "The upcoming maintenance schedule",
            "properties": {
                "startTime": {
                    "type": "string",
                    "format": "date-time",
                    "description": "The start time of the scheduled maintenance",
                },
                "endTime": {
                    "type": "string",
                    "format": "date-time",
                    "description": "The end time of the scheduled maintenance",
                },
                "canReschedule": {
                    "type": "boolean",
                    "description": "Whether the maintenance can be rescheduled",
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Resource labels",
            "additionalProperties": {"type": "string"},
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the instance was created",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the instance was last updated",
        },
    },
    "additionalProperties": False,
}


def get_schema() -> Dict[str, Any]:
    """Get the JSON schema for a Memorystore Redis instance.

    Returns:
        The JSON schema for the Redis instance resource
    """
    return REDIS_INSTANCE_SCHEMA
