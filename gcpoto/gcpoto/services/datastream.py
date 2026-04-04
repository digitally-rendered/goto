"""Service implementation for Google Cloud Datastream."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.datastream import ConnectionProfile, Stream

logger = logging.getLogger(__name__)

class DatastreamService(GCPService[ConnectionProfile]):
    """Service for interacting with Google Cloud Datastream."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Datastream service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="datastream",
            version="v1",
            credentials_file=credentials_file,
            resource_model=ConnectionProfile,
            **kwargs,
        )

    def list_connection_profiles(
        self, location: str
    ) -> List[ConnectionProfile]:
        """List connection profiles in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            A list of ConnectionProfile instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        request = (
            self.service.projects()
            .locations()
            .connectionProfiles()
            .list(parent=parent)
        )

        profiles = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("connectionProfiles", []):
                profiles.append(
                    ConnectionProfile.from_api_response(
                        item, self.project_id
                    )
                )
            request = (
                self.service.projects()
                .locations()
                .connectionProfiles()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s connection profiles in %s", len(profiles), location
        )
        return profiles

    def get_connection_profile(
        self, location: str, profile_id: str
    ) -> ConnectionProfile:
        """Get a specific connection profile.

        Args:
            location: The GCP location (e.g. 'us-central1')
            profile_id: The ID of the connection profile

        Returns:
            A ConnectionProfile instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/connectionProfiles/{profile_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .connectionProfiles()
            .get(name=name)
        )
        response = self._execute(request, "connection_profile", profile_id)
        logger.debug("Retrieved connection profile %s", profile_id)
        return ConnectionProfile.from_api_response(
            response, self.project_id
        )

    def create_connection_profile(
        self,
        location: str,
        profile_id: str,
        display_name: str,
        profile_config: Dict[str, Any],
        labels: Optional[Dict[str, str]] = None,
    ) -> ConnectionProfile:
        """Create a new connection profile.

        Args:
            location: The GCP location (e.g. 'us-central1')
            profile_id: The ID for the new connection profile
            display_name: Display name for the connection profile
            profile_config: The profile-specific configuration
                (e.g. {"oracleProfile": {...}} or {"mysqlProfile": {...}})
            labels: Optional labels for the connection profile

        Returns:
            The created ConnectionProfile instance
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        body: Dict[str, Any] = {"displayName": display_name}
        body.update(profile_config)

        if labels is not None:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .connectionProfiles()
            .create(
                parent=parent,
                connectionProfileId=profile_id,
                body=body,
            )
        )
        response = self._execute(request)
        logger.debug(
            "Created connection profile %s in %s", profile_id, location
        )
        return ConnectionProfile.from_api_response(
            response, self.project_id
        )

    def delete_connection_profile(
        self, location: str, profile_id: str
    ) -> bool:
        """Delete a connection profile.

        Args:
            location: The GCP location (e.g. 'us-central1')
            profile_id: The ID of the connection profile to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/connectionProfiles/{profile_id}"
        )
        request = self.service.projects().locations().connectionProfiles().delete(
            name=name
        )
        self._execute(request)
        logger.debug("Deleted connection profile %s", profile_id)
        return True

    def list_streams(self, location: str) -> List[Stream]:
        """List streams in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            A list of Stream instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        request = (
            self.service.projects()
            .locations()
            .streams()
            .list(parent=parent)
        )

        streams = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("streams", []):
                streams.append(
                    Stream.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .streams()
                .list_next(request, response)
            )

        logger.debug("Listed %s streams in %s", len(streams), location)
        return streams

    def get_stream(self, location: str, stream_id: str) -> Stream:
        """Get a specific stream.

        Args:
            location: The GCP location (e.g. 'us-central1')
            stream_id: The ID of the stream

        Returns:
            A Stream instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/streams/{stream_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .streams()
            .get(name=name)
        )
        response = self._execute(request, "stream", stream_id)
        logger.debug("Retrieved stream %s", stream_id)
        return Stream.from_api_response(response, self.project_id)

    def create_stream(
        self,
        location: str,
        stream_id: str,
        display_name: str,
        source_config: Dict[str, Any],
        destination_config: Dict[str, Any],
        backfill_all: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Stream:
        """Create a new stream.

        Args:
            location: The GCP location (e.g. 'us-central1')
            stream_id: The ID for the new stream
            display_name: Display name for the stream
            source_config: Source connection configuration
            destination_config: Destination connection configuration
            backfill_all: Optional backfill all objects configuration
            labels: Optional labels for the stream

        Returns:
            The created Stream instance
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        body: Dict[str, Any] = {
            "displayName": display_name,
            "sourceConfig": source_config,
            "destinationConfig": destination_config,
        }

        if backfill_all is not None:
            body["backfillAll"] = backfill_all

        if labels is not None:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .streams()
            .create(
                parent=parent,
                streamId=stream_id,
                body=body,
            )
        )
        response = self._execute(request)
        logger.debug("Created stream %s in %s", stream_id, location)
        return Stream.from_api_response(response, self.project_id)

    def update_stream(
        self,
        location: str,
        stream_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> Stream:
        """Update a stream.

        Args:
            location: The GCP location (e.g. 'us-central1')
            stream_id: The ID of the stream to update
            update_mask: Comma-separated list of fields to update
            update_fields: The fields to update

        Returns:
            The updated Stream instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/streams/{stream_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .streams()
            .patch(
                name=name,
                updateMask=update_mask,
                body=update_fields,
            )
        )
        response = self._execute(request, "stream", stream_id)
        logger.debug("Updated stream %s", stream_id)
        return Stream.from_api_response(response, self.project_id)

    def delete_stream(self, location: str, stream_id: str) -> bool:
        """Delete a stream.

        Args:
            location: The GCP location (e.g. 'us-central1')
            stream_id: The ID of the stream to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/streams/{stream_id}"
        )
        request = self.service.projects().locations().streams().delete(
            name=name
        )
        self._execute(request)
        logger.debug("Deleted stream %s", stream_id)
        return True

    def start_stream(self, location: str, stream_id: str) -> Stream:
        """Start a stream (set state to RUNNING).

        Args:
            location: The GCP location (e.g. 'us-central1')
            stream_id: The ID of the stream to start

        Returns:
            The updated Stream instance
        """
        logger.debug("Starting stream %s in %s", stream_id, location)
        return self.update_stream(
            location, stream_id, "state", {"state": "RUNNING"}
        )

    def stop_stream(self, location: str, stream_id: str) -> Stream:
        """Stop a stream (set state to PAUSED).

        Args:
            location: The GCP location (e.g. 'us-central1')
            stream_id: The ID of the stream to stop

        Returns:
            The updated Stream instance
        """
        logger.debug("Stopping stream %s in %s", stream_id, location)
        return self.update_stream(
            location, stream_id, "state", {"state": "PAUSED"}
        )
