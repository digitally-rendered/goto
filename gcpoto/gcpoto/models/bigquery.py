"""Models for Google Cloud BigQuery resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.bigquery import get_schema


class BigQueryDataset(GCPResource):
    """Model for a Google Cloud BigQuery Dataset."""

    dataset_id: str = ""
    friendly_name: Optional[str] = None
    description: Optional[str] = None
    location: str = ""
    default_table_expiration_ms: Optional[int] = None
    default_partition_expiration_ms: Optional[int] = None
    access: List[Dict[str, Any]] = Field(default_factory=list)
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("dataset")}

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
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "BigQueryDataset":
        """Create a BigQueryDataset from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new BigQueryDataset instance
        """
        ref = response.get("datasetReference", {})
        ds_id = ref.get("datasetId", "")
        proj = ref.get("projectId", "") or project_id

        instance = cls(
            id=response.get("id", ""),
            name=ds_id,
            type="bigquery.dataset",
            project=proj,
            dataset_id=ds_id,
            friendly_name=response.get("friendlyName"),
            description=response.get("description"),
            location=response.get("location", ""),
            default_table_expiration_ms=response.get("defaultTableExpirationMs"),
            default_partition_expiration_ms=response.get(
                "defaultPartitionExpirationMs"
            ),
            access=response.get("access", []),
            labels=response.get("labels"),
            created=response.get("creationTime"),
            updated=response.get("lastModifiedTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class BigQueryTable(GCPResource):
    """Model for a Google Cloud BigQuery Table."""

    dataset_id: str = ""
    table_id: str = ""
    friendly_name: Optional[str] = None
    description: Optional[str] = None
    schema_fields: List[Dict[str, Any]] = Field(default_factory=list)
    num_rows: int = 0
    num_bytes: int = 0
    table_type: str = ""
    time_partitioning: Optional[Dict[str, Any]] = None
    clustering_fields: Optional[List[str]] = None
    expiration_time: Optional[str] = None
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("table")}

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
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "BigQueryTable":
        """Create a BigQueryTable from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new BigQueryTable instance
        """
        ref = response.get("tableReference", {})
        tbl_id = ref.get("tableId", "")
        ds_id = ref.get("datasetId", "")
        proj = ref.get("projectId", "") or project_id

        # Extract schema fields
        schema_fields = []
        schema_data = response.get("schema", {})
        if schema_data:
            schema_fields = schema_data.get("fields", [])

        # Extract clustering fields
        clustering_fields = None
        clustering_data = response.get("clustering")
        if clustering_data:
            clustering_fields = clustering_data.get("fields")

        instance = cls(
            id=response.get("id", ""),
            name=tbl_id,
            type="bigquery.table",
            project=proj,
            dataset_id=ds_id,
            table_id=tbl_id,
            friendly_name=response.get("friendlyName"),
            description=response.get("description"),
            schema_fields=schema_fields,
            num_rows=int(response.get("numRows", 0)),
            num_bytes=int(response.get("numBytes", 0)),
            table_type=response.get("type", ""),
            time_partitioning=response.get("timePartitioning"),
            clustering_fields=clustering_fields,
            expiration_time=response.get("expirationTime"),
            labels=response.get("labels"),
            created=response.get("creationTime"),
            updated=response.get("lastModifiedTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class BigQueryJob(GCPResource):
    """Model for a Google Cloud BigQuery Job."""

    job_id: str = ""
    job_type: str = ""
    state: str = ""
    user_email: str = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    error_result: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("job")}

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "BigQueryJob":
        """Create a BigQueryJob from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new BigQueryJob instance
        """
        ref = response.get("jobReference", {})
        job_id = ref.get("jobId", "")
        proj = ref.get("projectId", "") or project_id

        status = response.get("status", {})
        config = response.get("configuration", {})
        stats = response.get("statistics", {})

        # Determine job type from configuration
        job_type = ""
        for jtype in ("query", "load", "extract", "copy"):
            if jtype in config:
                job_type = jtype
                break

        instance = cls(
            id=response.get("id", ""),
            name=job_id,
            type="bigquery.job",
            project=proj,
            job_id=job_id,
            job_type=job_type,
            state=status.get("state", ""),
            user_email=response.get("user_email", ""),
            start_time=stats.get("startTime"),
            end_time=stats.get("endTime"),
            configuration=config,
            statistics=stats,
            error_result=status.get("errorResult"),
            labels=response.get("labels"),
            created=stats.get("creationTime"),
        )

        return instance
