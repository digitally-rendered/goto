"""Service implementation for Google Cloud Network Connectivity Center."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.network_connectivity import Hub, Spoke
from gcpoto.exceptions import (
    APIError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


class NetworkConnectivityService(GCPService[Hub]):
    """Service for interacting with Google Cloud Network Connectivity Center."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Network Connectivity Center service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="networkconnectivity",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Hub,
            **kwargs,
        )

    # --- Hub methods ---

    def list_hubs(self) -> List[Hub]:
        """List Network Connectivity Hubs.

        Returns:
            A list of Hub instances
        """
        logger.info(
            "Listing network connectivity hubs for project %s",
            self.project_id,
        )

        parent = f"projects/{self.project_id}/locations/global"
        request = self.service.projects().locations().global_().hubs().list(
            parent=parent
        )

        hubs = []
        while request is not None:
            response = self._execute(request)
            for hub_data in response.get("hubs", []):
                hubs.append(Hub.from_api_response(hub_data))
            request = (
                self.service.projects()
                .locations()
                .global_()
                .hubs()
                .list_next(request, response)
            )

        logger.info("Found %s hubs", len(hubs))
        return hubs

    def get_hub(self, hub_name: str) -> Hub:
        """Get a specific Network Connectivity Hub.

        Args:
            hub_name: The name of the hub

        Returns:
            A Hub instance

        Raises:
            ResourceNotFoundError: If the hub does not exist
        """
        logger.info("Getting hub %s", hub_name)

        name = (
            f"projects/{self.project_id}/locations/global/hubs/{hub_name}"
        )

        request = (
            self.service.projects()
            .locations()
            .global_()
            .hubs()
            .get(name=name)
        )
        response = self._execute(request, "Hub", hub_name)
        return Hub.from_api_response(response)
    def create_hub(
        self,
        hub_name: str,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Hub:
        """Create a Network Connectivity Hub.

        Args:
            hub_name: The name for the hub
            description: Optional description for the hub
            labels: Optional labels for the hub

        Returns:
            The created Hub instance

        Raises:
            APIError: If the API call fails
        """
        logger.info("Creating hub %s", hub_name)

        parent = f"projects/{self.project_id}/locations/global"
        body = {"name": hub_name}
        if description:
            body["description"] = description
        if labels:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .global_()
            .hubs()
            .create(parent=parent, hubId=hub_name, body=body)
        )
        response = self._execute(request)
        logger.info("Created hub %s", hub_name)
        return Hub.from_api_response(response)
    def update_hub(
        self,
        hub_name: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> Hub:
        """Update a Network Connectivity Hub.

        Args:
            hub_name: The name of the hub to update
            update_mask: Comma-separated list of fields to update
            update_fields: Dictionary of fields to update

        Returns:
            The updated Hub instance

        Raises:
            ResourceNotFoundError: If the hub does not exist
            APIError: If the API call fails
        """
        logger.info("Updating hub %s", hub_name)

        name = (
            f"projects/{self.project_id}/locations/global/hubs/{hub_name}"
        )

        request = (
            self.service.projects()
            .locations()
            .global_()
            .hubs()
            .patch(name=name, updateMask=update_mask, body=update_fields)
        )
        response = self._execute(request, "Hub", hub_name)
        logger.info("Updated hub %s", hub_name)
        return Hub.from_api_response(response)
    def delete_hub(self, hub_name: str) -> bool:
        """Delete a Network Connectivity Hub.

        Args:
            hub_name: The name of the hub to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the hub does not exist
            APIError: If the API call fails
        """
        logger.info("Deleting hub %s", hub_name)

        name = (
            f"projects/{self.project_id}/locations/global/hubs/{hub_name}"
        )

        request = self.service.projects().locations().global_().hubs().delete(
            name=name
        )
        self._execute(request)
        logger.info("Deleted hub %s", hub_name)
        return True
    def list_spokes(self, location: str) -> List[Spoke]:
        """List Network Connectivity Spokes in a location.

        Args:
            location: The location to list spokes in

        Returns:
            A list of Spoke instances
        """
        logger.info(
            "Listing spokes in location %s for project %s",
            location,
            self.project_id,
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        request = self.service.projects().locations().spokes().list(
            parent=parent
        )

        spokes = []
        while request is not None:
            response = self._execute(request)
            for spoke_data in response.get("spokes", []):
                spokes.append(Spoke.from_api_response(spoke_data))
            request = (
                self.service.projects()
                .locations()
                .spokes()
                .list_next(request, response)
            )

        logger.info("Found %s spokes", len(spokes))
        return spokes

    def get_spoke(self, location: str, spoke_name: str) -> Spoke:
        """Get a specific Network Connectivity Spoke.

        Args:
            location: The location of the spoke
            spoke_name: The name of the spoke

        Returns:
            A Spoke instance

        Raises:
            ResourceNotFoundError: If the spoke does not exist
        """
        logger.info(
            "Getting spoke %s in location %s", spoke_name, location
        )

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/spokes/{spoke_name}"
        )

        request = (
            self.service.projects()
            .locations()
            .spokes()
            .get(name=name)
        )
        response = self._execute(request, "Spoke", spoke_name)
        return Spoke.from_api_response(response)
    def create_spoke(
        self,
        location: str,
        spoke_name: str,
        hub: str,
        linked_vpn_tunnels: Optional[Dict[str, Any]] = None,
        linked_interconnect_attachments: Optional[Dict[str, Any]] = None,
    ) -> Spoke:
        """Create a Network Connectivity Spoke.

        Args:
            location: The location to create the spoke in
            spoke_name: The name for the spoke
            hub: The hub to attach the spoke to
            linked_vpn_tunnels: Optional VPN tunnels to link
            linked_interconnect_attachments: Optional interconnect attachments

        Returns:
            The created Spoke instance

        Raises:
            APIError: If the API call fails
        """
        logger.info(
            "Creating spoke %s in location %s", spoke_name, location
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        body = {
            "name": spoke_name,
            "hub": hub,
        }
        if linked_vpn_tunnels:
            body["linkedVpnTunnels"] = linked_vpn_tunnels
        if linked_interconnect_attachments:
            body["linkedInterconnectAttachments"] = (
                linked_interconnect_attachments
            )

        request = (
            self.service.projects()
            .locations()
            .spokes()
            .create(
                parent=parent, spokeId=spoke_name, body=body
            )
        )
        response = self._execute(request)
        logger.info("Created spoke %s", spoke_name)
        return Spoke.from_api_response(response)
    def update_spoke(
        self,
        location: str,
        spoke_name: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> Spoke:
        """Update a Network Connectivity Spoke.

        Args:
            location: The location of the spoke
            spoke_name: The name of the spoke to update
            update_mask: Comma-separated list of fields to update
            update_fields: Dictionary of fields to update

        Returns:
            The updated Spoke instance

        Raises:
            ResourceNotFoundError: If the spoke does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Updating spoke %s in location %s", spoke_name, location
        )

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/spokes/{spoke_name}"
        )

        request = (
            self.service.projects()
            .locations()
            .spokes()
            .patch(
                name=name,
                updateMask=update_mask,
                body=update_fields,
            )
        )
        response = self._execute(request, "Spoke", spoke_name)
        logger.info("Updated spoke %s", spoke_name)
        return Spoke.from_api_response(response)
    def delete_spoke(self, location: str, spoke_name: str) -> bool:
        """Delete a Network Connectivity Spoke.

        Args:
            location: The location of the spoke
            spoke_name: The name of the spoke to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the spoke does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Deleting spoke %s in location %s", spoke_name, location
        )

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/spokes/{spoke_name}"
        )

        request = self.service.projects().locations().spokes().delete(
            name=name
        )
        self._execute(request)
        logger.info("Deleted spoke %s", spoke_name)
        return True