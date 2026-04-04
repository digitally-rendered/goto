"""JSON Schema definitions for Google Cloud Pub/Sub Lite resources."""

from typing import Dict, Any

LITE_TOPIC_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Pub/Sub Lite Topic",
    "description": "Schema for Google Cloud Pub/Sub Lite Topics",
    "type": "object",
    "required": ["name", "partitionConfig", "retentionConfig"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the topic",
        },
        "partitionConfig": {
            "type": "object",
            "description": "Partition configuration for the topic",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "The number of partitions",
                },
                "capacity": {
                    "type": "object",
                    "description": "The throughput capacity per partition",
                    "properties": {
                        "publishMibPerSec": {
                            "type": "integer",
                            "description": "Publish throughput per partition in MiB/s",
                        },
                        "subscribeMibPerSec": {
                            "type": "integer",
                            "description": "Subscribe throughput per partition in MiB/s",
                        },
                    },
                },
            },
        },
        "retentionConfig": {
            "type": "object",
            "description": "Retention configuration for the topic",
            "properties": {
                "perPartitionBytes": {
                    "type": "string",
                    "description": "Storage per partition in bytes",
                },
                "period": {
                    "type": "string",
                    "description": "Retention period (e.g. '86400s')",
                },
            },
        },
        "reservationConfig": {
            "type": "object",
            "description": "Reservation configuration for the topic",
            "properties": {
                "throughputReservation": {
                    "type": "string",
                    "description": "The reservation to use",
                },
            },
        },
    },
    "additionalProperties": False,
}

LITE_SUBSCRIPTION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Pub/Sub Lite Subscription",
    "description": "Schema for Google Cloud Pub/Sub Lite Subscriptions",
    "type": "object",
    "required": ["name", "topic"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the subscription",
        },
        "topic": {
            "type": "string",
            "description": "The topic this subscription is attached to",
        },
        "deliveryConfig": {
            "type": "object",
            "description": "Delivery configuration",
            "properties": {
                "deliveryRequirement": {
                    "type": "string",
                    "description": "The delivery requirement",
                    "enum": [
                        "DELIVERY_REQUIREMENT_UNSPECIFIED",
                        "DELIVER_IMMEDIATELY",
                        "DELIVER_AFTER_STORED",
                    ],
                },
            },
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "topic") -> Dict[str, Any]:
    """Get the JSON schema for a specific Pub/Sub Lite resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("topic" or "subscription")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "topic": LITE_TOPIC_SCHEMA,
        "subscription": LITE_SUBSCRIPTION_SCHEMA,
    }
    return schemas.get(resource_type.lower(), LITE_TOPIC_SCHEMA)
