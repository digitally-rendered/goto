"""JSON Schema definitions for Google Cloud Monitoring resources."""

from typing import Dict, Any

# JSON Schema for Cloud Monitoring Metric Descriptors
METRIC_DESCRIPTOR_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Monitoring Metric Descriptor",
    "description": "Schema for Google Cloud Monitoring metric descriptors",
    "type": "object",
    "required": ["type", "metricKind", "valueType"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the metric descriptor",
        },
        "type": {
            "type": "string",
            "description": "The metric type (e.g., custom.googleapis.com/my_metric)",
        },
        "displayName": {
            "type": "string",
            "description": "A concise name for the metric",
        },
        "description": {
            "type": "string",
            "description": "A detailed description of the metric",
        },
        "metricKind": {
            "type": "string",
            "description": "The kind of measurement",
            "enum": ["GAUGE", "DELTA", "CUMULATIVE"],
        },
        "valueType": {
            "type": "string",
            "description": "The value type of the metric",
            "enum": ["BOOL", "INT64", "DOUBLE", "STRING", "DISTRIBUTION"],
        },
        "unit": {
            "type": "string",
            "description": "The units in which the metric value is reported",
        },
        "labels": {
            "type": "array",
            "description": "The set of labels that can be used to describe a specific instance of this metric type",
            "items": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The label key",
                    },
                    "valueType": {
                        "type": "string",
                        "description": "The type of data that can be assigned to the label",
                        "enum": ["STRING", "BOOL", "INT64"],
                    },
                    "description": {
                        "type": "string",
                        "description": "A human-readable description for the label",
                    },
                },
            },
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Monitoring Alert Policies
ALERT_POLICY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Monitoring Alert Policy",
    "description": "Schema for Google Cloud Monitoring alert policies",
    "type": "object",
    "required": ["displayName", "conditions", "combiner"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the alert policy",
        },
        "displayName": {
            "type": "string",
            "description": "A short name for the policy",
        },
        "documentation": {
            "type": "object",
            "description": "Documentation for the policy",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The documentation content in Markdown format",
                },
                "mimeType": {
                    "type": "string",
                    "description": "The MIME type of the content",
                },
            },
        },
        "conditions": {
            "type": "array",
            "description": "A list of conditions for the policy",
            "items": {
                "type": "object",
                "properties": {
                    "displayName": {
                        "type": "string",
                        "description": "A short name for the condition",
                    },
                    "conditionThreshold": {
                        "type": "object",
                        "description": "A condition that compares a time series against a threshold",
                    },
                    "conditionAbsent": {
                        "type": "object",
                        "description": "A condition that checks for the absence of time series data",
                    },
                },
            },
        },
        "combiner": {
            "type": "string",
            "description": "How to combine the conditions",
            "enum": ["OR", "AND", "AND_WITH_MATCHING_RESOURCE"],
        },
        "enabled": {
            "type": "boolean",
            "description": "Whether the policy is enabled",
        },
        "notificationChannels": {
            "type": "array",
            "description": "Notification channels to use when the policy fires",
            "items": {"type": "string"},
        },
        "userLabels": {
            "type": "object",
            "description": "User-defined labels for the policy",
            "additionalProperties": {"type": "string"},
        },
        "creationRecord": {
            "type": "object",
            "description": "A record of the creation of the policy",
        },
        "mutationRecord": {
            "type": "object",
            "description": "A record of the most recent change to the policy",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Monitoring Notification Channels
NOTIFICATION_CHANNEL_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Monitoring Notification Channel",
    "description": "Schema for Google Cloud Monitoring notification channels",
    "type": "object",
    "required": ["displayName", "type"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the notification channel",
        },
        "displayName": {
            "type": "string",
            "description": "A human-readable name for the channel",
        },
        "type": {
            "type": "string",
            "description": "The type of the notification channel (e.g., email, sms, slack)",
        },
        "description": {
            "type": "string",
            "description": "A description of the channel",
        },
        "labels": {
            "type": "object",
            "description": "Configuration fields for the channel type",
            "additionalProperties": {"type": "string"},
        },
        "enabled": {
            "type": "boolean",
            "description": "Whether the channel is enabled",
        },
        "verificationStatus": {
            "type": "string",
            "description": "The verification status of the channel",
            "enum": [
                "VERIFICATION_STATUS_UNSPECIFIED",
                "UNVERIFIED",
                "VERIFIED",
            ],
        },
        "userLabels": {
            "type": "object",
            "description": "User-defined labels for the channel",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud Monitoring Uptime Check Configs
UPTIME_CHECK_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud Monitoring Uptime Check Config",
    "description": "Schema for Google Cloud Monitoring uptime check configurations",
    "type": "object",
    "required": ["displayName"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the uptime check config",
        },
        "displayName": {
            "type": "string",
            "description": "A human-friendly name for the uptime check",
        },
        "monitoredResource": {
            "type": "object",
            "description": "The monitored resource associated with the check",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "The monitored resource type",
                },
                "labels": {
                    "type": "object",
                    "description": "Values for the resource type labels",
                    "additionalProperties": {"type": "string"},
                },
            },
        },
        "httpCheck": {
            "type": "object",
            "description": "Contains information for an HTTP uptime check",
            "properties": {
                "requestMethod": {
                    "type": "string",
                    "description": "The HTTP request method",
                    "enum": ["GET", "POST"],
                },
                "useSsl": {
                    "type": "boolean",
                    "description": "Whether to use SSL",
                },
                "path": {
                    "type": "string",
                    "description": "The path to check",
                },
                "port": {
                    "type": "integer",
                    "description": "The TCP port to use",
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP headers to send with the request",
                    "additionalProperties": {"type": "string"},
                },
            },
        },
        "tcpCheck": {
            "type": "object",
            "description": "Contains information for a TCP uptime check",
            "properties": {
                "port": {
                    "type": "integer",
                    "description": "The TCP port to check",
                },
            },
        },
        "period": {
            "type": "string",
            "description": "How often the uptime check is performed (e.g., '60s', '300s')",
        },
        "timeout": {
            "type": "string",
            "description": "The maximum time to wait for the request to complete (e.g., '10s')",
        },
        "selectedRegions": {
            "type": "array",
            "description": "The list of regions from which the check is run",
            "items": {"type": "string"},
        },
        "isInternal": {
            "type": "boolean",
            "description": "Whether the check is internal",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "metric_descriptor") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud Monitoring resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("metric_descriptor", "alert_policy", "notification_channel",
             or "uptime_check_config")

    Returns:
        The JSON schema for the specified resource type
    """
    resource_type_lower = resource_type.lower()
    if resource_type_lower == "alert_policy":
        return ALERT_POLICY_SCHEMA
    elif resource_type_lower == "notification_channel":
        return NOTIFICATION_CHANNEL_SCHEMA
    elif resource_type_lower == "uptime_check_config":
        return UPTIME_CHECK_CONFIG_SCHEMA
    else:
        return METRIC_DESCRIPTOR_SCHEMA
