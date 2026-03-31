"""JSON Schema definitions for Google Cloud Dataproc resources."""

from typing import Dict, Any


# JSON Schema for Dataproc Clusters
DATAPROC_CLUSTER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Dataproc Cluster",
    "description": "Schema for Google Cloud Dataproc Clusters",
    "type": "object",
    "required": ["clusterName", "projectId"],
    "properties": {
        "clusterName": {
            "type": "string",
            "description": "The cluster name",
        },
        "projectId": {
            "type": "string",
            "description": "The GCP project ID",
        },
        "clusterUuid": {
            "type": "string",
            "description": "The unique UUID of the cluster",
        },
        "config": {
            "type": "object",
            "description": "The cluster configuration",
            "properties": {
                "masterConfig": {
                    "type": "object",
                    "description": "Master node configuration",
                    "properties": {
                        "numInstances": {
                            "type": "integer",
                            "description": "Number of master instances",
                        },
                        "machineTypeUri": {
                            "type": "string",
                            "description": "Machine type URI",
                        },
                        "diskConfig": {
                            "type": "object",
                            "description": "Disk configuration",
                            "properties": {
                                "bootDiskSizeGb": {
                                    "type": "integer",
                                    "description": "Boot disk size in GB",
                                },
                                "bootDiskType": {
                                    "type": "string",
                                    "description": "Boot disk type",
                                },
                            },
                        },
                    },
                },
                "workerConfig": {
                    "type": "object",
                    "description": "Worker node configuration",
                    "properties": {
                        "numInstances": {
                            "type": "integer",
                            "description": "Number of worker instances",
                        },
                        "machineTypeUri": {
                            "type": "string",
                            "description": "Machine type URI",
                        },
                        "diskConfig": {
                            "type": "object",
                            "description": "Disk configuration",
                            "properties": {
                                "bootDiskSizeGb": {
                                    "type": "integer",
                                    "description": "Boot disk size in GB",
                                },
                                "bootDiskType": {
                                    "type": "string",
                                    "description": "Boot disk type",
                                },
                            },
                        },
                    },
                },
                "softwareConfig": {
                    "type": "object",
                    "description": "Software configuration",
                    "properties": {
                        "imageVersion": {
                            "type": "string",
                            "description": "The image version to use",
                        },
                        "optionalComponents": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional components to install",
                        },
                    },
                },
                "gceClusterConfig": {
                    "type": "object",
                    "description": "GCE cluster configuration",
                    "properties": {
                        "zoneUri": {
                            "type": "string",
                            "description": "The GCE zone URI",
                        },
                        "networkUri": {
                            "type": "string",
                            "description": "The network URI",
                        },
                        "subnetworkUri": {
                            "type": "string",
                            "description": "The subnetwork URI",
                        },
                    },
                },
            },
        },
        "status": {
            "type": "object",
            "description": "The cluster status",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "The cluster state",
                    "enum": [
                        "UNKNOWN",
                        "CREATING",
                        "RUNNING",
                        "ERROR",
                        "ERROR_DUE_TO_UPDATE",
                        "DELETING",
                        "UPDATING",
                        "STOPPING",
                        "STOPPED",
                        "STARTING",
                        "REPAIRING",
                    ],
                },
                "stateStartTime": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Time when the state was entered",
                },
            },
        },
        "statusHistory": {
            "type": "array",
            "description": "The history of cluster statuses",
            "items": {
                "type": "object",
                "properties": {
                    "state": {"type": "string"},
                    "stateStartTime": {
                        "type": "string",
                        "format": "date-time",
                    },
                },
            },
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the cluster",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

# JSON Schema for Dataproc Jobs
DATAPROC_JOB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP Dataproc Job",
    "description": "Schema for Google Cloud Dataproc Jobs",
    "type": "object",
    "required": ["placement"],
    "properties": {
        "reference": {
            "type": "object",
            "description": "Job reference",
            "properties": {
                "projectId": {
                    "type": "string",
                    "description": "The GCP project ID",
                },
                "jobId": {
                    "type": "string",
                    "description": "The job ID",
                },
            },
        },
        "placement": {
            "type": "object",
            "description": "Job placement configuration",
            "required": ["clusterName"],
            "properties": {
                "clusterName": {
                    "type": "string",
                    "description": "The cluster to run the job on",
                },
            },
        },
        "status": {
            "type": "object",
            "description": "The job status",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "The job state",
                    "enum": [
                        "STATE_UNSPECIFIED",
                        "PENDING",
                        "SETUP_DONE",
                        "RUNNING",
                        "CANCEL_PENDING",
                        "CANCEL_STARTED",
                        "CANCELLED",
                        "DONE",
                        "ERROR",
                        "ATTEMPT_FAILURE",
                    ],
                },
                "stateStartTime": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Time when the state was entered",
                },
            },
        },
        "sparkJob": {
            "type": "object",
            "description": "Spark job configuration",
        },
        "pysparkJob": {
            "type": "object",
            "description": "PySpark job configuration",
        },
        "hiveJob": {
            "type": "object",
            "description": "Hive job configuration",
        },
        "pigJob": {
            "type": "object",
            "description": "Pig job configuration",
        },
        "hadoopJob": {
            "type": "object",
            "description": "Hadoop job configuration",
        },
        "sparkSqlJob": {
            "type": "object",
            "description": "Spark SQL job configuration",
        },
        "scheduling": {
            "type": "object",
            "description": "Job scheduling configuration",
            "properties": {
                "maxFailuresPerHour": {
                    "type": "integer",
                    "description": "Maximum number of failures per hour",
                },
                "maxFailuresTotal": {
                    "type": "integer",
                    "description": "Maximum total number of failures",
                },
            },
        },
        "driverOutputResourceUri": {
            "type": "string",
            "description": "URI of the driver output resource",
        },
        "labels": {
            "type": "object",
            "description": "Labels associated with the job",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def get_schema(resource_type: str = "cluster") -> Dict[str, Any]:
    """Get the JSON schema for a specific Dataproc resource type.

    Args:
        resource_type: The type of resource to get the schema for
            ("cluster" or "job")

    Returns:
        The JSON schema for the specified resource type
    """
    schemas = {
        "cluster": DATAPROC_CLUSTER_SCHEMA,
        "job": DATAPROC_JOB_SCHEMA,
    }
    return schemas.get(resource_type.lower(), DATAPROC_CLUSTER_SCHEMA)
