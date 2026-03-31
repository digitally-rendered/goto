"""Service implementation for Google Cloud Eventarc."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.eventarc import EventarcTrigger
from gcpoto.exceptions import ResourceAlreadyExistsError, ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class EventarcService(GCPService[EventarcTrigger]):
    """Service for interacting with Google Cloud Eventarc."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Eventarc service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="eventarc",
            version="v1",
            credentials_file=credentials_file,
            resource_model=EventarcTrigger,
            **kwargs,
        )

    def _format_trigger_path(self, location: str, trigger_name: str) -> str:
        """Format a fully qualified trigger path.

        Args:
            location: The GCP location (e.g. 'us-central1')
            trigger_name: The trigger name or full path

        Returns:
            The fully qualified trigger resource path
        """
        if "/" in trigger_name:
            return trigger_name
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/triggers/{trigger_name}"
        )

    def _format_location_path(self, location: str) -> str:
        """Format a fully qualified location path.

        Args:
            location: The GCP location (e.g. 'us-central1' or '-' for all)

        Returns:
            The fully qualified location resource path
        """
        return f"projects/{self.project_id}/locations/{location}"

    def list_triggers(self, location: str = "-", **kwargs) -> List[EventarcTrigger]:
        """List Eventarc triggers in a location.

        Args:
            location: The GCP location (e.g. 'us-central1', '-' for all)
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of EventarcTrigger instances
        """
        parent = self._format_location_path(location)

        request = (
            self.service.projects()
            .locations()
            .triggers()
            .list(parent=parent, **kwargs)
        )

        triggers = []
        while request is not None:
            response = request.execute()
            for trigger_data in response.get("triggers", []):
                triggers.append(
                    EventarcTrigger.from_api_response(
                        trigger_data, self.project_id
                    )
                )

            request = (
                self.service.projects()
                .locations()
                .triggers()
                .list_next(request, response)
            )

        logger.debug("Listed %s triggers in %s", len(triggers), location)
        return triggers

    def get_trigger(
        self, location: str, trigger_name: str
    ) -> EventarcTrigger:
        """Get a specific Eventarc trigger.

        Args:
            location: The GCP location (e.g. 'us-central1')
            trigger_name: The name of the trigger to retrieve

        Returns:
            An EventarcTrigger instance
        """
        name = self._format_trigger_path(location, trigger_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .triggers()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("trigger", trigger_name)
            raise

        logger.debug("Retrieved trigger %s", trigger_name)
        return EventarcTrigger.from_api_response(response, self.project_id)

    def create_trigger(
        self,
        location: str,
        trigger_name: str,
        event_filters: List[Dict[str, Any]],
        destination: Dict[str, Any],
        service_account: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> EventarcTrigger:
        """Create a new Eventarc trigger.

        Args:
            location: The GCP location (e.g. 'us-central1')
            trigger_name: The name of the trigger to create
            event_filters: List of event filter configurations
            destination: Destination configuration for matched events
            service_account: Optional IAM service account email
            labels: Optional labels to apply to the trigger

        Returns:
            An EventarcTrigger instance for the newly created trigger
        """
        parent = self._format_location_path(location)
        trigger_path = self._format_trigger_path(location, trigger_name)

        body: Dict[str, Any] = {
            "name": trigger_path,
            "eventFilters": event_filters,
            "destination": destination,
        }

        if service_account is not None:
            body["serviceAccount"] = service_account

        if labels is not None:
            body["labels"] = labels

        try:
            request = (
                self.service.projects()
                .locations()
                .triggers()
                .create(parent=parent, body=body, triggerId=trigger_name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"Trigger '{trigger_name}' already exists"
                )
            raise

        logger.debug("Created trigger %s in %s", trigger_name, location)
        return EventarcTrigger.from_api_response(response, self.project_id)

    def update_trigger(
        self,
        location: str,
        trigger_name: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> EventarcTrigger:
        """Update an existing Eventarc trigger.

        Args:
            location: The GCP location (e.g. 'us-central1')
            trigger_name: The name of the trigger to update
            update_mask: Comma-separated list of fields to update
            update_fields: Dictionary of fields to update

        Returns:
            The updated EventarcTrigger instance
        """
        name = self._format_trigger_path(location, trigger_name)

        body: Dict[str, Any] = {"name": name}
        body.update(update_fields)

        try:
            request = (
                self.service.projects()
                .locations()
                .triggers()
                .patch(name=name, body=body, updateMask=update_mask)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("trigger", trigger_name)
            raise

        logger.debug("Updated trigger %s in %s", trigger_name, location)
        return EventarcTrigger.from_api_response(response, self.project_id)

    def delete_trigger(self, location: str, trigger_name: str) -> bool:
        """Delete an Eventarc trigger.

        Args:
            location: The GCP location (e.g. 'us-central1')
            trigger_name: The name of the trigger to delete

        Returns:
            True if the deletion was successful
        """
        name = self._format_trigger_path(location, trigger_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .triggers()
                .delete(name=name)
            )
            request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("trigger", trigger_name)
            raise

        logger.debug("Deleted trigger %s in %s", trigger_name, location)
        return True
