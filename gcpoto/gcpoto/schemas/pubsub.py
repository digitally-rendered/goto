"""JSON Schema definitions for Google Cloud Pub/Sub resources."""

from typing import Dict, Any

# JSON Schema for Pub/Sub Topics
PUBSUB_TOPIC_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Pub/Sub Topic",
    "description": "Schema for Google Cloud Pub/Sub Topics",
    "type": "object",
    "required": ["name", "project"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the topic"
        },
        "name": {
            "type": "string",
            "description": "The name of the topic"
        },
        "project": {
            "type": "string",
            "description": "The GCP project ID containing the topic"
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the topic",
            "additionalProperties": {"type": "string"}
        },
        "kmsKeyName": {
            "type": "string",
            "description": "The KMS key used to protect access to messages published on this topic"
        },
        "messageStoragePolicy": {
            "type": "object",
            "description": "Policy constraining the set of Google Cloud regions where messages can be stored",
            "properties": {
                "allowedPersistenceRegions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of regions where messages can be stored"
                }
            }
        },
        "schemaSettings": {
            "type": "object",
            "description": "Settings for schema validation of messages published to the topic",
            "properties": {
                "schema": {
                    "type": "string",
                    "description": "The name of the schema that messages published should be validated against"
                },
                "encoding": {
                    "type": "string",
                    "description": "The encoding of the messages validated against the schema",
                    "enum": ["JSON", "BINARY"]
                }
            }
        },
        "messageRetentionDuration": {
            "type": "string",
            "description": "The duration in seconds for which messages are retained (in ISO 8601 duration format)"
        },
        "satisfiesPzs": {
            "type": "boolean",
            "description": "Whether this topic satisfies the requirements for Assured Workloads"
        },
        "created": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the topic"
        },
        "updated": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the topic"
        }
    },
    "additionalProperties": False
}


# JSON Schema for Pub/Sub Subscriptions
PUBSUB_SUBSCRIPTION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Pub/Sub Subscription",
    "description": "Schema for Google Cloud Pub/Sub Subscriptions",
    "type": "object",
    "required": ["name", "topic", "project"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the subscription"
        },
        "name": {
            "type": "string",
            "description": "The name of the subscription"
        },
        "topic": {
            "type": "string",
            "description": "The name of the topic this subscription is attached to"
        },
        "project": {
            "type": "string",
            "description": "The GCP project ID containing the subscription"
        },
        "pushConfig": {
            "type": "object",
            "description": "Configuration for push delivery",
            "properties": {
                "pushEndpoint": {
                    "type": "string",
                    "description": "URL of the endpoint to push messages to"
                },
                "attributes": {
                    "type": "object",
                    "description": "Endpoint configuration attributes",
                    "additionalProperties": {"type": "string"}
                },
                "oidcToken": {
                    "type": "object",
                    "description": "OIDC token configuration for authentication",
                    "properties": {
                        "serviceAccountEmail": {
                            "type": "string",
                            "description": "Service account email to use for OIDC token generation"
                        },
                        "audience": {
                            "type": "string",
                            "description": "Audience to be used for the token"
                        }
                    }
                }
            }
        },
        "ackDeadlineSeconds": {
            "type": "integer",
            "description": "The maximum time in seconds after receiving a message before it must be acknowledged"
        },
        "retainAckedMessages": {
            "type": "boolean",
            "description": "Whether to retain acknowledged messages"
        },
        "messageRetentionDuration": {
            "type": "string",
            "description": "How long to retain unacknowledged messages (in ISO 8601 duration format)"
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the subscription",
            "additionalProperties": {"type": "string"}
        },
        "expirationPolicy": {
            "type": "object",
            "description": "Policy for subscription expiration",
            "properties": {
                "ttl": {
                    "type": "string",
                    "description": "TTL duration after which the subscription expires (in ISO 8601 duration format)"
                }
            }
        },
        "filter": {
            "type": "string",
            "description": "Expression to filter messages delivered to this subscription"
        },
        "deadLetterPolicy": {
            "type": "object",
            "description": "Dead letter policy for the subscription",
            "properties": {
                "deadLetterTopic": {
                    "type": "string",
                    "description": "The name of the topic to which dead letter messages are published"
                },
                "maxDeliveryAttempts": {
                    "type": "integer",
                    "description": "Maximum number of delivery attempts for any message"
                }
            }
        },
        "retryPolicy": {
            "type": "object",
            "description": "Retry policy for the subscription",
            "properties": {
                "minimumBackoff": {
                    "type": "string",
                    "description": "Minimum backoff time between retries (in ISO 8601 duration format)"
                },
                "maximumBackoff": {
                    "type": "string",
                    "description": "Maximum backoff time between retries (in ISO 8601 duration format)"
                }
            }
        },
        "detached": {
            "type": "boolean",
            "description": "Whether the subscription is detached from its topic"
        },
        "enableMessageOrdering": {
            "type": "boolean",
            "description": "Whether to enable message ordering for this subscription"
        },
        "created": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the subscription"
        },
        "updated": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the subscription"
        }
    },
    "additionalProperties": False
}


def get_schema(resource_type: str = "topic") -> Dict[str, Any]:
    """Get the JSON schema for a specific Pub/Sub resource type.
    
    Args:
        resource_type: The type of resource to get the schema for ("topic" or "subscription")
        
    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "subscription":
        return PUBSUB_SUBSCRIPTION_SCHEMA
    else:  # Default to topic
        return PUBSUB_TOPIC_SCHEMA
