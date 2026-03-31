"""Models for Google Cloud Logging resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class LogEntry(GCPResource):
    """Model for a Google Cloud Logging log entry."""

    log_name: str = Field("", description="The resource name of the log")
    severity: str = Field(
        "DEFAULT",
        description="The severity of the log entry",
    )
    text_payload: Optional[str] = Field(
        None, description="The log entry payload as a text string"
    )
    json_payload: Optional[Dict[str, Any]] = Field(
        None, description="The log entry payload as a JSON object"
    )
    timestamp: Optional[datetime] = Field(
        None, description="The time the event described by the log entry occurred"
    )
    resource_type: Optional[str] = Field(
        None, description="The monitored resource type"
    )
    resource_labels: Optional[Dict[str, str]] = Field(
        None, description="Labels for the monitored resource"
    )
    insert_id: Optional[str] = Field(
        None, description="A unique identifier for the log entry"
    )
    trace: Optional[str] = Field(
        None, description="The trace associated with the log entry"
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
    def from_api_response(cls, response: Dict[str, Any]) -> "LogEntry":
        """Create a LogEntry from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new LogEntry instance
        """
        log_name = response.get("logName", "")
        entry_name = log_name.split("/")[-1] if log_name else ""

        # Extract project from logName: projects/{project}/logs/{log}
        project_id = ""
        if log_name:
            parts = log_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        # Parse timestamp
        timestamp = None
        ts_str = response.get("timestamp")
        if ts_str:
            try:
                timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                timestamp = None

        # Extract monitored resource info
        resource = response.get("resource", {})
        resource_type = resource.get("type")
        resource_labels = resource.get("labels")

        instance = cls(
            id=response.get("insertId", ""),
            name=entry_name,
            type="logging.logEntry",
            project=project_id,
            labels=response.get("labels"),
            log_name=log_name,
            severity=response.get("severity", "DEFAULT"),
            text_payload=response.get("textPayload"),
            json_payload=response.get("jsonPayload"),
            timestamp=timestamp,
            resource_type=resource_type,
            resource_labels=resource_labels,
            insert_id=response.get("insertId"),
            trace=response.get("trace"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class LogSink(GCPResource):
    """Model for a Google Cloud Logging sink."""

    destination: str = Field("", description="The export destination")
    filter_str: Optional[str] = Field(
        None, description="An advanced logs filter"
    )
    description: Optional[str] = Field(
        None, description="A description of this sink"
    )
    disabled: bool = Field(
        False, description="Whether the sink is disabled"
    )
    writer_identity: Optional[str] = Field(
        None, description="The service account used for writing to the destination"
    )
    include_children: bool = Field(
        False,
        description="Whether to include log entries from child projects/folders/orgs",
    )
    exclusions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Log entries to exclude from the sink"
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
    def from_api_response(cls, response: Dict[str, Any]) -> "LogSink":
        """Create a LogSink from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new LogSink instance
        """
        full_name = response.get("name", "")
        sink_name = full_name.split("/")[-1] if "/" in full_name else full_name

        # Extract project from name: projects/{project}/sinks/{sink}
        project_id = ""
        if "/" in full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        instance = cls(
            id=full_name,
            name=sink_name,
            type="logging.sink",
            project=project_id,
            destination=response.get("destination", ""),
            filter_str=response.get("filter"),
            description=response.get("description"),
            disabled=response.get("disabled", False),
            writer_identity=response.get("writerIdentity"),
            include_children=response.get("includeChildren", False),
            exclusions=response.get("exclusions"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        return instance


class LogMetric(GCPResource):
    """Model for a Google Cloud Logging metric."""

    description: Optional[str] = Field(
        None, description="A description of this metric"
    )
    filter_str: str = Field("", description="An advanced logs filter")
    metric_descriptor: Optional[Dict[str, Any]] = Field(
        None, description="The metric descriptor associated with the metric"
    )
    value_extractor: Optional[str] = Field(
        None, description="A value_extractor for the metric"
    )
    label_extractors: Optional[Dict[str, str]] = Field(
        None, description="A map from label key to extractor expression"
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
    def from_api_response(cls, response: Dict[str, Any]) -> "LogMetric":
        """Create a LogMetric from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new LogMetric instance
        """
        full_name = response.get("name", "")
        metric_name = full_name.split("/")[-1] if "/" in full_name else full_name

        # Extract project from name: projects/{project}/metrics/{metric}
        project_id = ""
        if "/" in full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        instance = cls(
            id=full_name,
            name=metric_name,
            type="logging.metric",
            project=project_id,
            description=response.get("description"),
            filter_str=response.get("filter", ""),
            metric_descriptor=response.get("metricDescriptor"),
            value_extractor=response.get("valueExtractor"),
            label_extractors=response.get("labelExtractors"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        return instance
