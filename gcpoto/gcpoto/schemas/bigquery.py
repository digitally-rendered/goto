"""JSON Schema definitions for Google Cloud BigQuery resources."""

from typing import Dict, Any


BIGQUERY_DATASET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP BigQuery Dataset",
    "description": "Schema for Google Cloud BigQuery Datasets",
    "type": "object",
    "required": ["datasetReference"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the dataset",
        },
        "datasetReference": {
            "type": "object",
            "description": "Reference to the dataset",
            "required": ["datasetId", "projectId"],
            "properties": {
                "datasetId": {
                    "type": "string",
                    "description": "The dataset ID",
                },
                "projectId": {
                    "type": "string",
                    "description": "The project ID",
                },
            },
        },
        "friendlyName": {
            "type": "string",
            "description": "A descriptive name for the dataset",
        },
        "description": {
            "type": "string",
            "description": "A user-friendly description of the dataset",
        },
        "location": {
            "type": "string",
            "description": "The geographic location where the dataset resides",
        },
        "defaultTableExpirationMs": {
            "type": "integer",
            "description": "Default expiration time for tables in milliseconds",
        },
        "defaultPartitionExpirationMs": {
            "type": "integer",
            "description": "Default partition expiration time in milliseconds",
        },
        "access": {
            "type": "array",
            "description": "Access control list for the dataset",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "userByEmail": {"type": "string"},
                    "groupByEmail": {"type": "string"},
                    "specialGroup": {"type": "string"},
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the dataset",
            "additionalProperties": {"type": "string"},
        },
        "creationTime": {
            "type": "string",
            "description": "The time when the dataset was created",
        },
        "lastModifiedTime": {
            "type": "string",
            "description": "The time when the dataset was last modified",
        },
    },
    "additionalProperties": False,
}


BIGQUERY_TABLE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP BigQuery Table",
    "description": "Schema for Google Cloud BigQuery Tables",
    "type": "object",
    "required": ["tableReference"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the table",
        },
        "tableReference": {
            "type": "object",
            "description": "Reference to the table",
            "required": ["tableId", "datasetId", "projectId"],
            "properties": {
                "tableId": {
                    "type": "string",
                    "description": "The table ID",
                },
                "datasetId": {
                    "type": "string",
                    "description": "The dataset ID",
                },
                "projectId": {
                    "type": "string",
                    "description": "The project ID",
                },
            },
        },
        "friendlyName": {
            "type": "string",
            "description": "A descriptive name for the table",
        },
        "description": {
            "type": "string",
            "description": "A user-friendly description of the table",
        },
        "schema": {
            "type": "object",
            "description": "The table schema",
            "properties": {
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "mode": {"type": "string"},
                            "description": {"type": "string"},
                        },
                        "required": ["name", "type"],
                    },
                }
            },
        },
        "numRows": {
            "type": "string",
            "description": "The number of rows in the table",
        },
        "numBytes": {
            "type": "string",
            "description": "The size of the table in bytes",
        },
        "type": {
            "type": "string",
            "description": "The type of the table (TABLE, VIEW, EXTERNAL)",
            "enum": ["TABLE", "VIEW", "EXTERNAL", "MATERIALIZED_VIEW", "SNAPSHOT"],
        },
        "timePartitioning": {
            "type": "object",
            "description": "Time-based partitioning configuration",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "The partitioning type (DAY, HOUR, MONTH, YEAR)",
                },
                "field": {
                    "type": "string",
                    "description": "The field used for partitioning",
                },
                "expirationMs": {
                    "type": "string",
                    "description": "Partition expiration in milliseconds",
                },
            },
        },
        "clustering": {
            "type": "object",
            "description": "Clustering configuration",
            "properties": {
                "fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fields used for clustering",
                }
            },
        },
        "expirationTime": {
            "type": "string",
            "description": "The time when the table expires",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the table",
            "additionalProperties": {"type": "string"},
        },
        "creationTime": {
            "type": "string",
            "description": "The time when the table was created",
        },
        "lastModifiedTime": {
            "type": "string",
            "description": "The time when the table was last modified",
        },
    },
    "additionalProperties": False,
}


BIGQUERY_JOB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP BigQuery Job",
    "description": "Schema for Google Cloud BigQuery Jobs",
    "type": "object",
    "required": ["jobReference"],
    "properties": {
        "id": {
            "type": "string",
            "description": "The unique identifier for the job",
        },
        "jobReference": {
            "type": "object",
            "description": "Reference to the job",
            "required": ["jobId", "projectId"],
            "properties": {
                "jobId": {
                    "type": "string",
                    "description": "The job ID",
                },
                "projectId": {
                    "type": "string",
                    "description": "The project ID",
                },
            },
        },
        "status": {
            "type": "object",
            "description": "The status of the job",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "The state of the job (PENDING, RUNNING, DONE)",
                    "enum": ["PENDING", "RUNNING", "DONE"],
                },
                "errorResult": {
                    "type": "object",
                    "description": "Error result if the job failed",
                    "properties": {
                        "reason": {"type": "string"},
                        "location": {"type": "string"},
                        "message": {"type": "string"},
                    },
                },
            },
        },
        "configuration": {
            "type": "object",
            "description": "The job configuration",
        },
        "statistics": {
            "type": "object",
            "description": "Job statistics",
            "properties": {
                "startTime": {"type": "string"},
                "endTime": {"type": "string"},
                "creationTime": {"type": "string"},
                "totalBytesProcessed": {"type": "string"},
                "totalBytesBilled": {"type": "string"},
            },
        },
        "user_email": {
            "type": "string",
            "description": "The email of the user who ran the job",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the job",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "dataset") -> Dict[str, Any]:
    """Get the JSON schema for a specific BigQuery resource type.

    Args:
        resource_type: The type of resource ("dataset", "table", or "job")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "dataset": BIGQUERY_DATASET_SCHEMA,
        "table": BIGQUERY_TABLE_SCHEMA,
        "job": BIGQUERY_JOB_SCHEMA,
    }
    return schemas.get(resource_type.lower(), BIGQUERY_DATASET_SCHEMA)
