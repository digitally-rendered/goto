"""JSON Schema definitions for Web Security Scanner resources."""

from typing import Dict, Any


SCAN_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Web Security Scanner Scan Config",
    "description": "Schema for Web Security Scanner Scan Configs",
    "type": "object",
    "required": ["name", "displayName", "startingUrls"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the scan config",
        },
        "displayName": {
            "type": "string",
            "description": "The display name of the scan config",
        },
        "startingUrls": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The starting URLs for the scan",
        },
        "maxQps": {
            "type": "integer",
            "description": "Maximum queries per second during scanning",
        },
        "authentication": {
            "type": "object",
            "description": "Authentication configuration",
        },
        "userAgent": {
            "type": "string",
            "description": "The user agent string for the scanner",
            "enum": [
                "USER_AGENT_UNSPECIFIED",
                "CHROME_LINUX",
                "CHROME_ANDROID",
                "SAFARI_IPHONE",
            ],
        },
        "blacklistPatterns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "URL patterns to exclude from the scan",
        },
        "schedule": {
            "type": "object",
            "description": "The schedule for automatic scanning",
            "properties": {
                "scheduleTime": {
                    "type": "string",
                    "format": "date-time",
                    "description": "When the next scan should start",
                },
                "intervalDurationDays": {
                    "type": "integer",
                    "description": "The number of days between scans",
                },
            },
        },
        "targetPlatforms": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "TARGET_PLATFORM_UNSPECIFIED",
                    "APP_ENGINE",
                    "COMPUTE",
                ],
            },
            "description": "Target platforms for the scan",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time",
        },
    },
    "additionalProperties": False,
}

SCAN_RUN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Web Security Scanner Scan Run",
    "description": "Schema for Web Security Scanner Scan Runs",
    "type": "object",
    "required": ["name", "executionState"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The resource name of the scan run",
        },
        "executionState": {
            "type": "string",
            "description": "The execution state of the scan run",
            "enum": ["QUEUED", "SCANNING", "FINISHED"],
        },
        "resultState": {
            "type": "string",
            "description": "The result state of the scan run",
            "enum": ["SUCCESS", "ERROR", "KILLED"],
        },
        "startTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the scan run started",
        },
        "endTime": {
            "type": "string",
            "format": "date-time",
            "description": "The time the scan run ended",
        },
        "urlsCrawledCount": {
            "type": "integer",
            "description": "The number of URLs crawled",
        },
        "urlsTestedCount": {
            "type": "integer",
            "description": "The number of URLs tested",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "scan_config") -> Dict[str, Any]:
    """Get the JSON schema for a specific Web Security Scanner resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("scan_config" or "scan_run")

    Returns:
        The JSON schema for the specified resource type
    """
    if resource_type.lower() == "scan_run":
        return SCAN_RUN_SCHEMA
    else:
        return SCAN_CONFIG_SCHEMA
