"""Service implementation for Google Cloud Interconnect."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.interconnect import Interconnect, InterconnectAttachment
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
)

logger = logging.getLogger(__name__)


class InterconnectService(GCPService[Interconnect]):
    """Service for interacting with Google Cloud Interconnect."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Interconnect service.

        Args:
            project_id: The GCP project ID to use for API calls.
            credentials_file: Optional path to a service account credentials
                file.
            **kwargs: Additional arguments to pass to the service constructor.
        """
        super().__init__(
            project_id=project_id,
            service_name="compute",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Interconnect,
            **kwargs,
        )

    # ------------------------------------------------------------------ #
    #  Interconnect operations
    # ------------------------------------------------------------------ #

    def list_interconnects(self) -> List[Interconnect]:
        """List interconnects in the project.

        Returns:
            A list of Interconnect instances.
        """
        logger.info(
            "Listing interconnects for project %s", self.project_id
        )

        request = self.service.interconnects().list(
            project=self.project_id
        )

        interconnects = []
        while request is not None:
            response = request.execute()
            for item in response.get("items", []):
                interconnects.append(
                    Interconnect.from_api_response(item)
                )
            request = self.service.interconnects().list_next(
                request, response
            )

        logger.info("Found %s interconnects", len(interconnects))
        return interconnects

    def get_interconnect(
        self, interconnect_name: str
    ) -> Interconnect:
        """Get a specific interconnect.

        Args:
            interconnect_name: The name of the interconnect.

        Returns:
            An Interconnect instance.

        Raises:
            ResourceNotFoundError: If the interconnect does not exist.
            APIError: If the API call fails.
        """
        logger.info("Getting interconnect %s", interconnect_name)

        try:
            request = self.service.interconnects().get(
                project=self.project_id,
                interconnect=interconnect_name,
            )
            response = request.execute()
            return Interconnect.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "Interconnect", interconnect_name
                )
            raise APIError(e.resp.status, str(e))

    def create_interconnect(
        self,
        interconnect_name: str,
        interconnect_type: str,
        link_type: str,
        requested_link_count: int,
        location: str,
    ) -> Interconnect:
        """Create a new interconnect.

        Args:
            interconnect_name: The name for the new interconnect.
            interconnect_type: The type of interconnect
                (``IT_PRIVATE`` or ``PARTNER``).
            link_type: The link type of the interconnect.
            requested_link_count: The number of physical links to request.
            location: The location of the interconnect facility.

        Returns:
            An Interconnect instance for the newly created interconnect.

        Raises:
            ResourceAlreadyExistsError: If the interconnect already exists.
            APIError: If the API call fails.
        """
        logger.info("Creating interconnect %s", interconnect_name)

        body: Dict[str, Any] = {
            "name": interconnect_name,
            "interconnectType": interconnect_type,
            "linkType": link_type,
            "requestedLinkCount": requested_link_count,
            "location": location,
        }

        try:
            request = self.service.interconnects().insert(
                project=self.project_id, body=body
            )
            response = request.execute()
            logger.info("Created interconnect %s", interconnect_name)
            return Interconnect.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"Interconnect '{interconnect_name}' already exists"
                )
            raise APIError(e.resp.status, str(e))

    def delete_interconnect(self, interconnect_name: str) -> bool:
        """Delete an interconnect.

        Args:
            interconnect_name: The name of the interconnect to delete.

        Returns:
            True if the deletion was successful.

        Raises:
            ResourceNotFoundError: If the interconnect does not exist.
            APIError: If the API call fails.
        """
        logger.info("Deleting interconnect %s", interconnect_name)

        try:
            self.service.interconnects().delete(
                project=self.project_id,
                interconnect=interconnect_name,
            ).execute()
            logger.info("Deleted interconnect %s", interconnect_name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "Interconnect", interconnect_name
                )
            raise APIError(e.resp.status, str(e))

    # ------------------------------------------------------------------ #
    #  Interconnect Attachment operations
    # ------------------------------------------------------------------ #

    def list_attachments(
        self, region: str
    ) -> List[InterconnectAttachment]:
        """List interconnect attachments in a region.

        Args:
            region: The GCP region (e.g. ``us-central1``).

        Returns:
            A list of InterconnectAttachment instances.
        """
        logger.info(
            "Listing interconnect attachments in %s for project %s",
            region,
            self.project_id,
        )

        request = self.service.interconnectAttachments().list(
            project=self.project_id, region=region
        )

        attachments = []
        while request is not None:
            response = request.execute()
            for item in response.get("items", []):
                attachments.append(
                    InterconnectAttachment.from_api_response(item)
                )
            request = (
                self.service.interconnectAttachments().list_next(
                    request, response
                )
            )

        logger.info("Found %s interconnect attachments", len(attachments))
        return attachments

    def get_attachment(
        self, region: str, attachment_name: str
    ) -> InterconnectAttachment:
        """Get a specific interconnect attachment.

        Args:
            region: The GCP region.
            attachment_name: The name of the attachment.

        Returns:
            An InterconnectAttachment instance.

        Raises:
            ResourceNotFoundError: If the attachment does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Getting interconnect attachment %s in %s",
            attachment_name,
            region,
        )

        try:
            request = self.service.interconnectAttachments().get(
                project=self.project_id,
                region=region,
                interconnectAttachment=attachment_name,
            )
            response = request.execute()
            return InterconnectAttachment.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "InterconnectAttachment", attachment_name
                )
            raise APIError(e.resp.status, str(e))

    def create_attachment(
        self,
        region: str,
        attachment_name: str,
        router: str,
        type_field: str,
        interconnect: Optional[str] = None,
        bandwidth: Optional[str] = None,
    ) -> InterconnectAttachment:
        """Create a new interconnect attachment.

        Args:
            region: The GCP region.
            attachment_name: The name for the new attachment.
            router: The Cloud Router to associate with the attachment.
            type_field: The type of attachment
                (``DEDICATED`` or ``PARTNER``).
            interconnect: Optional interconnect name for dedicated
                attachments.
            bandwidth: Optional bandwidth for the attachment.

        Returns:
            An InterconnectAttachment instance for the newly created
            attachment.

        Raises:
            ResourceAlreadyExistsError: If the attachment already exists.
            APIError: If the API call fails.
        """
        logger.info(
            "Creating interconnect attachment %s in %s",
            attachment_name,
            region,
        )

        body: Dict[str, Any] = {
            "name": attachment_name,
            "router": router,
            "type": type_field,
        }

        if interconnect:
            body["interconnect"] = interconnect
        if bandwidth:
            body["bandwidth"] = bandwidth

        try:
            request = self.service.interconnectAttachments().insert(
                project=self.project_id, region=region, body=body
            )
            response = request.execute()
            logger.info(
                "Created interconnect attachment %s", attachment_name
            )
            return InterconnectAttachment.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"InterconnectAttachment '{attachment_name}' "
                    f"already exists"
                )
            raise APIError(e.resp.status, str(e))

    def delete_attachment(
        self, region: str, attachment_name: str
    ) -> bool:
        """Delete an interconnect attachment.

        Args:
            region: The GCP region.
            attachment_name: The name of the attachment to delete.

        Returns:
            True if the deletion was successful.

        Raises:
            ResourceNotFoundError: If the attachment does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Deleting interconnect attachment %s in %s",
            attachment_name,
            region,
        )

        try:
            self.service.interconnectAttachments().delete(
                project=self.project_id,
                region=region,
                interconnectAttachment=attachment_name,
            ).execute()
            logger.info(
                "Deleted interconnect attachment %s", attachment_name
            )
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "InterconnectAttachment", attachment_name
                )
            raise APIError(e.resp.status, str(e))

    # ------------------------------------------------------------------ #
    #  Interconnect Location operations
    # ------------------------------------------------------------------ #

    def list_locations(self) -> List[Dict[str, Any]]:
        """List available interconnect locations.

        Returns:
            A list of interconnect location dictionaries.
        """
        logger.info(
            "Listing interconnect locations for project %s",
            self.project_id,
        )

        request = self.service.interconnectLocations().list(
            project=self.project_id
        )

        locations = []
        while request is not None:
            response = request.execute()
            locations.extend(response.get("items", []))
            request = self.service.interconnectLocations().list_next(
                request, response
            )

        logger.info("Found %s interconnect locations", len(locations))
        return locations
