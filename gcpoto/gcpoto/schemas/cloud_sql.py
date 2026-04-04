"""JSON Schema definitions for Google Cloud SQL resources."""

from typing import Dict, Any


# JSON Schema for Cloud SQL Instances
SQL_INSTANCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud SQL Instance",
    "description": "Schema for Google Cloud SQL Instances",
    "type": "object",
    "required": ["name", "databaseVersion", "region"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the Cloud SQL instance",
        },
        "databaseVersion": {
            "type": "string",
            "description": "The database engine version (e.g. MYSQL_8_0, POSTGRES_15)",
        },
        "region": {
            "type": "string",
            "description": "The GCP region of the instance",
        },
        "state": {
            "type": "string",
            "description": "The current state of the instance",
            "enum": [
                "SQL_INSTANCE_STATE_UNSPECIFIED",
                "RUNNABLE",
                "SUSPENDED",
                "PENDING_DELETE",
                "PENDING_CREATE",
                "MAINTENANCE",
                "FAILED",
            ],
        },
        "settings": {
            "type": "object",
            "description": "Instance settings",
            "properties": {
                "tier": {
                    "type": "string",
                    "description": "The machine tier (e.g. db-n1-standard-1)",
                },
                "availabilityType": {
                    "type": "string",
                    "description": "Availability type (ZONAL or REGIONAL)",
                    "enum": ["ZONAL", "REGIONAL"],
                },
                "dataDiskSizeGb": {
                    "type": "string",
                    "description": "The data disk size in GB",
                },
                "dataDiskType": {
                    "type": "string",
                    "description": "The type of data disk",
                    "enum": ["PD_SSD", "PD_HDD"],
                },
                "backupConfiguration": {
                    "type": "object",
                    "description": "Backup configuration",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "Whether backup is enabled",
                        },
                        "startTime": {
                            "type": "string",
                            "description": "Start time for the backup window (HH:MM format)",
                        },
                        "binaryLogEnabled": {
                            "type": "boolean",
                            "description": "Whether binary log is enabled",
                        },
                    },
                },
                "ipConfiguration": {
                    "type": "object",
                    "description": "IP configuration",
                    "properties": {
                        "ipv4Enabled": {
                            "type": "boolean",
                            "description": "Whether IPv4 is enabled",
                        },
                        "privateNetwork": {
                            "type": "string",
                            "description": "The VPC network for private IP",
                        },
                        "requireSsl": {
                            "type": "boolean",
                            "description": "Whether SSL is required",
                        },
                    },
                },
                "userLabels": {
                    "type": "object",
                    "description": "User-provided labels",
                    "additionalProperties": {"type": "string"},
                },
            },
        },
        "ipAddresses": {
            "type": "array",
            "description": "IP addresses assigned to the instance",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "The type of IP address",
                        "enum": ["PRIMARY", "OUTGOING", "PRIVATE"],
                    },
                    "ipAddress": {
                        "type": "string",
                        "description": "The IP address",
                    },
                },
            },
        },
        "connectionName": {
            "type": "string",
            "description": "Connection name in the form project:region:instance",
        },
        "gceZone": {
            "type": "string",
            "description": "The GCE zone the instance is in",
        },
        "project": {
            "type": "string",
            "description": "The GCP project ID",
        },
        "createTime": {
            "type": "string",
            "format": "date-time",
            "description": "The creation time of the instance",
        },
        "updateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The last update time of the instance",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud SQL Databases
SQL_DATABASE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud SQL Database",
    "description": "Schema for Google Cloud SQL Databases",
    "type": "object",
    "required": ["name", "instance"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the database",
        },
        "instance": {
            "type": "string",
            "description": "The Cloud SQL instance name",
        },
        "charset": {
            "type": "string",
            "description": "The character set for the database",
        },
        "collation": {
            "type": "string",
            "description": "The collation for the database",
        },
        "selfLink": {
            "type": "string",
            "description": "The URI of this resource",
        },
        "project": {
            "type": "string",
            "description": "The GCP project ID",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud SQL Users
SQL_USER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud SQL User",
    "description": "Schema for Google Cloud SQL Users",
    "type": "object",
    "required": ["name", "instance"],
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the user",
        },
        "instance": {
            "type": "string",
            "description": "The Cloud SQL instance name",
        },
        "host": {
            "type": "string",
            "description": "The host from which the user can connect",
        },
        "password": {
            "type": "string",
            "description": "The password for the user",
        },
        "project": {
            "type": "string",
            "description": "The GCP project ID",
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Cloud SQL Backup Runs
SQL_BACKUP_RUN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Cloud SQL Backup Run",
    "description": "Schema for Google Cloud SQL Backup Runs",
    "type": "object",
    "required": ["id", "instance"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier of the backup run",
        },
        "instance": {
            "type": "string",
            "description": "The Cloud SQL instance name",
        },
        "status": {
            "type": "string",
            "description": "The status of the backup run",
            "enum": [
                "SQL_BACKUP_RUN_STATUS_UNSPECIFIED",
                "ENQUEUED",
                "OVERDUE",
                "RUNNING",
                "FAILED",
                "SUCCESSFUL",
                "SKIPPED",
                "DELETION_PENDING",
                "DELETION_FAILED",
                "DELETED",
            ],
        },
        "startTime": {
            "type": "string",
            "format": "date-time",
            "description": "The start time of the backup run",
        },
        "endTime": {
            "type": "string",
            "format": "date-time",
            "description": "The end time of the backup run",
        },
        "backupKind": {
            "type": "string",
            "description": "The kind of backup",
            "enum": ["SQL_BACKUP_KIND_UNSPECIFIED", "SNAPSHOT", "PHYSICAL"],
        },
        "diskEncryptionStatus": {
            "type": "object",
            "description": "Disk encryption status for the backup",
            "properties": {
                "kmsKeyVersionName": {
                    "type": "string",
                    "description": "KMS key version used to encrypt the backup",
                },
            },
        },
        "location": {
            "type": "string",
            "description": "The location of the backup",
        },
        "project": {
            "type": "string",
            "description": "The GCP project ID",
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "instance") -> Dict[str, Any]:
    """Get the JSON schema for a specific Cloud SQL resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("instance", "database", "user", or "backup_run")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "instance": SQL_INSTANCE_SCHEMA,
        "database": SQL_DATABASE_SCHEMA,
        "user": SQL_USER_SCHEMA,
        "backup_run": SQL_BACKUP_RUN_SCHEMA,
    }
    return schemas.get(resource_type.lower(), SQL_INSTANCE_SCHEMA)
