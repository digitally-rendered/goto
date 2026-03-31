"""Service implementation for Google Cloud Error Reporting."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.error_reporting import ErrorGroup, ErrorEvent
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class ErrorReportingService(GCPService[ErrorGroup]):
    """Service for interacting with Google Cloud Error Reporting."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Error Reporting service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="clouderrorreporting",
            version="v1beta1",
            credentials_file=credentials_file,
            resource_model=ErrorGroup,
            **kwargs,
        )

    # ---- Group Stats ----

    def list_group_stats(
        self,
        time_range: Optional[str] = None,
        filter_str: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """List error group statistics for the project.

        Args:
            time_range: Optional time range period
                (e.g., "PERIOD_1_HOUR", "PERIOD_6_HOURS", "PERIOD_1_DAY").
            filter_str: Optional filter expression.
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of error group statistics dictionaries.
        """
        logger.debug(
            "Listing error group stats for project %s", self.project_id
        )

        parent = f"projects/{self.project_id}"
        params: Dict[str, Any] = {"projectName": parent}
        if time_range:
            params["timeRange_period"] = time_range
        if filter_str:
            params["filter"] = filter_str
        params.update(kwargs)

        stats = []
        request = self.service.projects().groupStats().list(**params)
        while request is not None:
            response = request.execute()
            for item in response.get("errorGroupStats", []):
                stats.append(item)
            request = (
                self.service.projects()
                .groupStats()
                .list_next(request, response)
            )

        return stats

    # ---- Events ----

    def list_events(
        self,
        group_id: str,
        time_range: Optional[str] = None,
        **kwargs,
    ) -> List[ErrorEvent]:
        """List error events for a specific error group.

        Args:
            group_id: The error group ID to list events for.
            time_range: Optional time range period.
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of ErrorEvent instances.
        """
        logger.debug(
            "Listing error events for group %s in project %s",
            group_id,
            self.project_id,
        )

        parent = f"projects/{self.project_id}"
        params: Dict[str, Any] = {
            "projectName": parent,
            "groupId": group_id,
        }
        if time_range:
            params["timeRange_period"] = time_range
        params.update(kwargs)

        events = []
        request = self.service.projects().events().list(**params)
        while request is not None:
            response = request.execute()
            for item in response.get("errorEvents", []):
                events.append(ErrorEvent.from_api_response(item))
            request = (
                self.service.projects()
                .events()
                .list_next(request, response)
            )

        return events

    def report_event(
        self,
        service_name: str,
        version: str,
        message: str,
        user: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Report a new error event.

        Args:
            service_name: The service name where the error occurred.
            version: The service version.
            message: The error message (including stack trace if available).
            user: Optional user affected by the error.

        Returns:
            The API response dictionary.
        """
        logger.debug(
            "Reporting error event for service %s in project %s",
            service_name,
            self.project_id,
        )

        parent = f"projects/{self.project_id}"
        body: Dict[str, Any] = {
            "serviceContext": {
                "service": service_name,
                "version": version,
            },
            "message": message,
        }
        if user:
            body["context"] = {"user": user}

        request = self.service.projects().events().report(
            projectName=parent, body=body
        )
        response = request.execute()

        return response

    # ---- Groups ----

    def get_group(self, group_id: str) -> ErrorGroup:
        """Get a specific error group.

        Args:
            group_id: The error group ID or full resource name.

        Returns:
            An ErrorGroup instance.
        """
        if "/" not in group_id:
            name = f"projects/{self.project_id}/groups/{group_id}"
        else:
            name = group_id

        logger.debug("Getting error group %s", name)

        try:
            request = self.service.projects().groups().get(groupName=name)
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("errorGroup", group_id)
            raise

        return ErrorGroup.from_api_response(response)

    def update_group(
        self,
        group_id: str,
        resolution_status: Optional[str] = None,
        **kwargs,
    ) -> ErrorGroup:
        """Update an error group.

        Args:
            group_id: The error group ID or full resource name.
            resolution_status: Optional new resolution status
                (OPEN, ACKNOWLEDGED, RESOLVED, MUTED).
            **kwargs: Additional fields to update.

        Returns:
            The updated ErrorGroup instance.
        """
        if "/" not in group_id:
            name = f"projects/{self.project_id}/groups/{group_id}"
        else:
            name = group_id

        logger.debug("Updating error group %s", name)

        body: Dict[str, Any] = {"name": name}
        if resolution_status is not None:
            body["resolutionStatus"] = resolution_status
        body.update(kwargs)

        request = self.service.projects().groups().update(
            name=name, body=body
        )
        response = request.execute()

        return ErrorGroup.from_api_response(response)

    # ---- Delete Events ----

    def delete_events(self) -> bool:
        """Delete all error events for the project.

        Returns:
            True if the deletion was successful.
        """
        logger.debug(
            "Deleting all error events for project %s", self.project_id
        )

        parent = f"projects/{self.project_id}"
        request = self.service.projects().deleteEvents(
            projectName=parent
        )
        request.execute()

        return True
