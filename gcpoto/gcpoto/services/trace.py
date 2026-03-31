"""Service implementation for Google Cloud Trace."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.trace import Trace, TraceSpan
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class TraceService(GCPService[Trace]):
    """Service for interacting with Google Cloud Trace."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Trace service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="cloudtrace",
            version="v2",
            credentials_file=credentials_file,
            resource_model=Trace,
            **kwargs,
        )

    def list_traces(
        self,
        filter_str: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        **kwargs,
    ) -> List[TraceSpan]:
        """List trace spans for the project.

        Args:
            filter_str: Optional filter expression for traces.
            start_time: Optional start of the time interval (RFC3339 string).
            end_time: Optional end of the time interval (RFC3339 string).
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of TraceSpan instances.
        """
        logger.debug("Listing traces for project %s", self.project_id)

        parent = f"projects/{self.project_id}"
        params: Dict[str, Any] = {"parent": parent}
        if filter_str:
            params["filter"] = filter_str
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        params.update(kwargs)

        spans = []
        request = self.service.projects().traces().list(**params)
        while request is not None:
            response = request.execute()
            for item in response.get("spans", []):
                spans.append(TraceSpan.from_api_response(item))
            request = (
                self.service.projects()
                .traces()
                .list_next(request, response)
            )

        return spans

    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """Get all spans for a specific trace.

        Args:
            trace_id: The trace ID to retrieve.

        Returns:
            A list of TraceSpan instances belonging to the trace.
        """
        logger.debug("Getting trace %s for project %s", trace_id, self.project_id)

        parent = f"projects/{self.project_id}"
        params: Dict[str, Any] = {
            "parent": parent,
            "filter": f'+traceId:"{trace_id}"',
        }

        try:
            request = self.service.projects().traces().list(**params)
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("trace", trace_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise

        spans = []
        for item in response.get("spans", []):
            spans.append(TraceSpan.from_api_response(item))

        return spans

    def batch_write_spans(self, spans: List[Dict[str, Any]]) -> bool:
        """Write a batch of spans to the project.

        Args:
            spans: A list of span dictionaries to write.

        Returns:
            True if the write was successful.
        """
        logger.debug(
            "Batch writing %d spans to project %s",
            len(spans),
            self.project_id,
        )

        parent = f"projects/{self.project_id}"
        body: Dict[str, Any] = {"spans": spans}

        request = self.service.projects().traces().batchWrite(
            name=parent, body=body
        )
        request.execute()

        return True
