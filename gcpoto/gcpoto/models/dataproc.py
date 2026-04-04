"""Models for Google Cloud Dataproc resources."""

from typing import Dict, List, Optional, Any

from pydantic import Field

from gcpoto.models.base import GCPResource


class DataprocCluster(GCPResource):
    """Model for a Google Cloud Dataproc cluster."""

    location: str = Field("", description="The GCP region of the cluster")
    cluster_name: str = Field("", description="The cluster name")
    config: Dict = Field(
        default_factory=dict,
        description="The cluster configuration",
    )
    status: Dict = Field(
        default_factory=dict,
        description="The cluster status",
    )
    status_history: Optional[List[Dict]] = Field(
        None, description="The history of cluster statuses"
    )
    cluster_uuid: Optional[str] = Field(
        None, description="The unique UUID of the cluster"
    )
    _tags: Optional[Dict[str, str]] = None

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "DataprocCluster":
        """Create a DataprocCluster from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new DataprocCluster instance
        """
        cluster_name = response.get("clusterName", "")
        labels = response.get("labels")

        instance = cls(
            id=response.get("clusterUuid", cluster_name),
            name=cluster_name,
            type="dataproc.cluster",
            project=response.get("projectId", ""),
            location=response.get("config", {}).get(
                "gceClusterConfig", {}
            ).get("zoneUri", ""),
            cluster_name=cluster_name,
            config=response.get("config", {}),
            status=response.get("status", {}),
            status_history=response.get("statusHistory"),
            cluster_uuid=response.get("clusterUuid"),
            labels=labels,
            created=response.get("status", {}).get("stateStartTime"),
            updated=response.get("status", {}).get("stateStartTime"),
        )
        if labels:
            instance._tags = labels
        return instance


class DataprocJob(GCPResource):
    """Model for a Google Cloud Dataproc job."""

    location: str = Field("", description="The GCP region of the job")
    cluster_name: str = Field("", description="The cluster the job runs on")
    job_type: str = Field("", description="The type of job (e.g. spark, hive)")
    status: Dict = Field(
        default_factory=dict,
        description="The job status",
    )
    placement: Optional[Dict] = Field(
        None, description="Job placement configuration"
    )
    scheduling: Optional[Dict] = Field(
        None, description="Job scheduling configuration"
    )
    driver_output_resource_uri: Optional[str] = Field(
        None, description="URI of the driver output resource"
    )
    _tags: Optional[Dict[str, str]] = None

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "DataprocJob":
        """Create a DataprocJob from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new DataprocJob instance
        """
        reference = response.get("reference", {})
        job_id = reference.get("jobId", "")
        placement = response.get("placement")
        cluster_name = placement.get("clusterName", "") if placement else ""
        labels = response.get("labels")

        # Determine job type from the job-specific config keys
        job_type = ""
        for jt in [
            "sparkJob",
            "pysparkJob",
            "hiveJob",
            "pigJob",
            "sparkRJob",
            "sparkSqlJob",
            "hadoopJob",
            "prestoJob",
            "trinoJob",
            "flinkJob",
        ]:
            if jt in response:
                job_type = jt.replace("Job", "")
                break

        instance = cls(
            id=job_id,
            name=job_id,
            type="dataproc.job",
            project=reference.get("projectId", ""),
            location=response.get("region", ""),
            cluster_name=cluster_name,
            job_type=job_type,
            status=response.get("status", {}),
            placement=placement,
            scheduling=response.get("scheduling"),
            driver_output_resource_uri=response.get("driverOutputResourceUri"),
            labels=labels,
            created=response.get("status", {}).get("stateStartTime"),
            updated=response.get("status", {}).get("stateStartTime"),
        )
        if labels:
            instance._tags = labels
        return instance
