"""Service implementation for Google Cloud Logging."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.logging_service import LogEntry, LogSink, LogMetric
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class LoggingService(GCPService[LogEntry]):
    """Service for interacting with Google Cloud Logging."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Logging service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="logging",
            version="v2",
            credentials_file=credentials_file,
            resource_model=LogEntry,
            **kwargs,
        )

    def _format_log_path(self, log_name: str) -> str:
        """Format a log name into its full resource path.

        Args:
            log_name: Either a short log name or a full resource path.

        Returns:
            The fully-qualified log resource path.
        """
        if "/" not in log_name:
            return f"projects/{self.project_id}/logs/{log_name}"
        return log_name

    def _format_sink_path(self, sink_name: str) -> str:
        """Format a sink name into its full resource path.

        Args:
            sink_name: Either a short sink name or a full resource path.

        Returns:
            The fully-qualified sink resource path.
        """
        if "/" not in sink_name:
            return f"projects/{self.project_id}/sinks/{sink_name}"
        return sink_name

    def _format_metric_path(self, metric_name: str) -> str:
        """Format a metric name into its full resource path.

        Args:
            metric_name: Either a short metric name or a full resource path.

        Returns:
            The fully-qualified metric resource path.
        """
        if "/" not in metric_name:
            return f"projects/{self.project_id}/metrics/{metric_name}"
        return metric_name

    # ---- Log Entries ----

    def list_log_entries(
        self,
        filter_str: Optional[str] = None,
        order_by: Optional[str] = None,
        page_size: int = 100,
        **kwargs,
    ) -> List[LogEntry]:
        """List log entries for the project.

        Args:
            filter_str: Optional advanced logs filter expression.
            order_by: Optional ordering (e.g. "timestamp desc").
            page_size: Maximum number of entries to return per page.
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of LogEntry instances.
        """
        body: Dict[str, Any] = {
            "resourceNames": [f"projects/{self.project_id}"],
            "pageSize": page_size,
        }
        if filter_str:
            body["filter"] = filter_str
        if order_by:
            body["orderBy"] = order_by

        logger.debug("Listing log entries for project %s", self.project_id)

        request = self.service.entries().list(body=body)
        response = request.execute()

        entries = []
        for entry_data in response.get("entries", []):
            entries.append(LogEntry.from_api_response(entry_data))

        return entries

    def write_log_entry(
        self,
        log_name: str,
        severity: str = "DEFAULT",
        text_payload: Optional[str] = None,
        json_payload: Optional[Dict[str, Any]] = None,
        resource_type: Optional[str] = None,
        resource_labels: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Write a log entry.

        Args:
            log_name: The log name to write to.
            severity: The severity level of the entry.
            text_payload: Optional text payload.
            json_payload: Optional JSON payload.
            resource_type: Optional monitored resource type.
            resource_labels: Optional monitored resource labels.
            labels: Optional labels for the log entry.

        Returns:
            The API response dictionary.
        """
        full_log_name = self._format_log_path(log_name)

        entry: Dict[str, Any] = {
            "logName": full_log_name,
            "severity": severity,
        }

        if text_payload is not None:
            entry["textPayload"] = text_payload
        if json_payload is not None:
            entry["jsonPayload"] = json_payload
        if labels is not None:
            entry["labels"] = labels

        resource: Dict[str, Any] = {
            "type": resource_type or "global",
        }
        if resource_labels:
            resource["labels"] = resource_labels
        entry["resource"] = resource

        body = {
            "logName": full_log_name,
            "resource": resource,
            "entries": [entry],
        }

        logger.debug("Writing log entry to %s", full_log_name)

        request = self.service.entries().write(body=body)
        response = request.execute()

        return response

    def delete_log(self, log_name: str) -> bool:
        """Delete a log and all its entries.

        Args:
            log_name: The name of the log to delete.

        Returns:
            True if the deletion was successful.
        """
        full_log_name = self._format_log_path(log_name)

        logger.debug("Deleting log %s", full_log_name)

        request = self.service.projects().logs().delete(logName=full_log_name)
        request.execute()

        return True

    def list_logs(self, **kwargs) -> List[str]:
        """List log names for the project.

        Args:
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of log name strings.
        """
        logger.debug("Listing logs for project %s", self.project_id)

        parent = f"projects/{self.project_id}"
        request = self.service.projects().logs().list(parent=parent, **kwargs)
        response = request.execute()

        return response.get("logNames", [])

    # ---- Sinks ----

    def list_sinks(self, **kwargs) -> List[LogSink]:
        """List log sinks for the project.

        Args:
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of LogSink instances.
        """
        logger.debug("Listing sinks for project %s", self.project_id)

        parent = f"projects/{self.project_id}"
        request = self.service.projects().sinks().list(parent=parent, **kwargs)
        response = request.execute()

        sinks = []
        for sink_data in response.get("sinks", []):
            sinks.append(LogSink.from_api_response(sink_data))

        return sinks

    def get_sink(self, sink_name: str) -> LogSink:
        """Get a specific log sink by name.

        Args:
            sink_name: The name of the sink to retrieve.

        Returns:
            A LogSink instance.
        """
        full_sink_name = self._format_sink_path(sink_name)

        logger.debug("Getting sink %s", full_sink_name)

        try:
            request = self.service.projects().sinks().get(
                sinkName=full_sink_name
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("sink", sink_name)
            raise

        return LogSink.from_api_response(response)

    def create_sink(
        self,
        sink_name: str,
        destination: str,
        filter_str: Optional[str] = None,
        description: Optional[str] = None,
    ) -> LogSink:
        """Create a new log sink.

        Args:
            sink_name: The name for the new sink.
            destination: The export destination URI.
            filter_str: Optional advanced logs filter expression.
            description: Optional description for the sink.

        Returns:
            The newly created LogSink instance.
        """
        parent = f"projects/{self.project_id}"

        body: Dict[str, Any] = {
            "name": sink_name,
            "destination": destination,
        }
        if filter_str is not None:
            body["filter"] = filter_str
        if description is not None:
            body["description"] = description

        logger.debug("Creating sink %s in project %s", sink_name, self.project_id)

        request = self.service.projects().sinks().create(
            parent=parent, body=body
        )
        response = request.execute()

        return LogSink.from_api_response(response)

    def update_sink(
        self,
        sink_name: str,
        destination: Optional[str] = None,
        filter_str: Optional[str] = None,
        description: Optional[str] = None,
    ) -> LogSink:
        """Update an existing log sink.

        Args:
            sink_name: The name of the sink to update.
            destination: Optional new export destination URI.
            filter_str: Optional new advanced logs filter expression.
            description: Optional new description for the sink.

        Returns:
            The updated LogSink instance.
        """
        full_sink_name = self._format_sink_path(sink_name)

        body: Dict[str, Any] = {}
        if destination is not None:
            body["destination"] = destination
        if filter_str is not None:
            body["filter"] = filter_str
        if description is not None:
            body["description"] = description

        logger.debug("Updating sink %s", full_sink_name)

        request = self.service.projects().sinks().update(
            sinkName=full_sink_name, body=body
        )
        response = request.execute()

        return LogSink.from_api_response(response)

    def delete_sink(self, sink_name: str) -> bool:
        """Delete a log sink.

        Args:
            sink_name: The name of the sink to delete.

        Returns:
            True if the deletion was successful.
        """
        full_sink_name = self._format_sink_path(sink_name)

        logger.debug("Deleting sink %s", full_sink_name)

        request = self.service.projects().sinks().delete(
            sinkName=full_sink_name
        )
        request.execute()

        return True

    # ---- Metrics ----

    def list_metrics(self, **kwargs) -> List[LogMetric]:
        """List log-based metrics for the project.

        Args:
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of LogMetric instances.
        """
        logger.debug("Listing metrics for project %s", self.project_id)

        parent = f"projects/{self.project_id}"
        request = self.service.projects().metrics().list(
            parent=parent, **kwargs
        )
        response = request.execute()

        metrics = []
        for metric_data in response.get("metrics", []):
            metrics.append(LogMetric.from_api_response(metric_data))

        return metrics

    def get_metric(self, metric_name: str) -> LogMetric:
        """Get a specific log-based metric by name.

        Args:
            metric_name: The name of the metric to retrieve.

        Returns:
            A LogMetric instance.
        """
        full_metric_name = self._format_metric_path(metric_name)

        logger.debug("Getting metric %s", full_metric_name)

        try:
            request = self.service.projects().metrics().get(
                metricName=full_metric_name
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("metric", metric_name)
            raise

        return LogMetric.from_api_response(response)

    def create_metric(
        self,
        metric_name: str,
        filter_str: str,
        description: Optional[str] = None,
    ) -> LogMetric:
        """Create a new log-based metric.

        Args:
            metric_name: The name for the new metric.
            filter_str: The advanced logs filter expression.
            description: Optional description for the metric.

        Returns:
            The newly created LogMetric instance.
        """
        parent = f"projects/{self.project_id}"

        body: Dict[str, Any] = {
            "name": metric_name,
            "filter": filter_str,
        }
        if description is not None:
            body["description"] = description

        logger.debug(
            "Creating metric %s in project %s", metric_name, self.project_id
        )

        request = self.service.projects().metrics().create(
            parent=parent, body=body
        )
        response = request.execute()

        return LogMetric.from_api_response(response)

    def update_metric(
        self,
        metric_name: str,
        filter_str: Optional[str] = None,
        description: Optional[str] = None,
    ) -> LogMetric:
        """Update an existing log-based metric.

        Args:
            metric_name: The name of the metric to update.
            filter_str: Optional new advanced logs filter expression.
            description: Optional new description for the metric.

        Returns:
            The updated LogMetric instance.
        """
        full_metric_name = self._format_metric_path(metric_name)

        body: Dict[str, Any] = {}
        if filter_str is not None:
            body["filter"] = filter_str
        if description is not None:
            body["description"] = description

        logger.debug("Updating metric %s", full_metric_name)

        request = self.service.projects().metrics().update(
            metricName=full_metric_name, body=body
        )
        response = request.execute()

        return LogMetric.from_api_response(response)

    def delete_metric(self, metric_name: str) -> bool:
        """Delete a log-based metric.

        Args:
            metric_name: The name of the metric to delete.

        Returns:
            True if the deletion was successful.
        """
        full_metric_name = self._format_metric_path(metric_name)

        logger.debug("Deleting metric %s", full_metric_name)

        request = self.service.projects().metrics().delete(
            metricName=full_metric_name
        )
        request.execute()

        return True
