"""Service implementation for Google Cloud VPN."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.vpn import VPNGateway, VPNTunnel
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
)

logger = logging.getLogger(__name__)


class VPNService(GCPService[VPNGateway]):
    """Service for interacting with Google Cloud VPN."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud VPN service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="compute",
            version="v1",
            credentials_file=credentials_file,
            resource_model=VPNGateway,
            **kwargs,
        )

    def list_vpn_gateways(self, region: str) -> List[VPNGateway]:
        """List VPN gateways in a region.

        Args:
            region: The region to list VPN gateways in

        Returns:
            A list of VPNGateway instances
        """
        logger.info(
            "Listing VPN gateways in region %s for project %s",
            region,
            self.project_id,
        )

        request = self.service.vpnGateways().list(
            project=self.project_id, region=region
        )

        gateways = []
        while request is not None:
            response = request.execute()
            for gw_data in response.get("items", []):
                gateways.append(VPNGateway.from_api_response(gw_data))
            request = self.service.vpnGateways().list_next(request, response)

        logger.info("Found %s VPN gateways", len(gateways))
        return gateways

    def get_vpn_gateway(
        self, region: str, gateway_name: str
    ) -> VPNGateway:
        """Get a specific VPN gateway.

        Args:
            region: The region of the VPN gateway
            gateway_name: The name of the VPN gateway

        Returns:
            A VPNGateway instance

        Raises:
            ResourceNotFoundError: If the gateway does not exist
        """
        logger.info(
            "Getting VPN gateway %s in region %s", gateway_name, region
        )

        try:
            request = self.service.vpnGateways().get(
                project=self.project_id, region=region, vpnGateway=gateway_name
            )
            response = request.execute()
            return VPNGateway.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("VPNGateway", gateway_name)
            raise APIError(e.resp.status, str(e))

    def create_vpn_gateway(
        self, region: str, gateway_name: str, network: str
    ) -> VPNGateway:
        """Create a VPN gateway.

        Args:
            region: The region to create the VPN gateway in
            gateway_name: The name for the VPN gateway
            network: The network URL for the VPN gateway

        Returns:
            The created VPNGateway instance

        Raises:
            ResourceAlreadyExistsError: If the gateway already exists
            APIError: If the API call fails
        """
        logger.info(
            "Creating VPN gateway %s in region %s", gateway_name, region
        )

        body = {
            "name": gateway_name,
            "network": network,
        }

        try:
            request = self.service.vpnGateways().insert(
                project=self.project_id, region=region, body=body
            )
            response = request.execute()
            logger.info("Created VPN gateway %s", gateway_name)
            return VPNGateway.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"VPNGateway '{gateway_name}' already exists"
                )
            raise APIError(e.resp.status, str(e))

    def delete_vpn_gateway(self, region: str, gateway_name: str) -> bool:
        """Delete a VPN gateway.

        Args:
            region: The region of the VPN gateway
            gateway_name: The name of the VPN gateway to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the gateway does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Deleting VPN gateway %s in region %s", gateway_name, region
        )

        try:
            self.service.vpnGateways().delete(
                project=self.project_id, region=region, vpnGateway=gateway_name
            ).execute()
            logger.info("Deleted VPN gateway %s", gateway_name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("VPNGateway", gateway_name)
            raise APIError(e.resp.status, str(e))

    def list_vpn_tunnels(self, region: str) -> List[VPNTunnel]:
        """List VPN tunnels in a region.

        Args:
            region: The region to list VPN tunnels in

        Returns:
            A list of VPNTunnel instances
        """
        logger.info(
            "Listing VPN tunnels in region %s for project %s",
            region,
            self.project_id,
        )

        request = self.service.vpnTunnels().list(
            project=self.project_id, region=region
        )

        tunnels = []
        while request is not None:
            response = request.execute()
            for tunnel_data in response.get("items", []):
                tunnels.append(VPNTunnel.from_api_response(tunnel_data))
            request = self.service.vpnTunnels().list_next(request, response)

        logger.info("Found %s VPN tunnels", len(tunnels))
        return tunnels

    def get_vpn_tunnel(self, region: str, tunnel_name: str) -> VPNTunnel:
        """Get a specific VPN tunnel.

        Args:
            region: The region of the VPN tunnel
            tunnel_name: The name of the VPN tunnel

        Returns:
            A VPNTunnel instance

        Raises:
            ResourceNotFoundError: If the tunnel does not exist
        """
        logger.info(
            "Getting VPN tunnel %s in region %s", tunnel_name, region
        )

        try:
            request = self.service.vpnTunnels().get(
                project=self.project_id, region=region, vpnTunnel=tunnel_name
            )
            response = request.execute()
            return VPNTunnel.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("VPNTunnel", tunnel_name)
            raise APIError(e.resp.status, str(e))

    def create_vpn_tunnel(
        self,
        region: str,
        tunnel_name: str,
        vpn_gateway: str,
        peer_ip: str,
        shared_secret: str,
        ike_version: int = 2,
    ) -> VPNTunnel:
        """Create a VPN tunnel.

        Args:
            region: The region to create the VPN tunnel in
            tunnel_name: The name for the VPN tunnel
            vpn_gateway: The VPN gateway URL
            peer_ip: The peer IP address
            shared_secret: The shared secret for IKE
            ike_version: The IKE protocol version (default: 2)

        Returns:
            The created VPNTunnel instance

        Raises:
            ResourceAlreadyExistsError: If the tunnel already exists
            APIError: If the API call fails
        """
        logger.info(
            "Creating VPN tunnel %s in region %s", tunnel_name, region
        )

        body = {
            "name": tunnel_name,
            "vpnGateway": vpn_gateway,
            "peerIp": peer_ip,
            "sharedSecret": shared_secret,
            "ikeVersion": ike_version,
        }

        try:
            request = self.service.vpnTunnels().insert(
                project=self.project_id, region=region, body=body
            )
            response = request.execute()
            logger.info("Created VPN tunnel %s", tunnel_name)
            return VPNTunnel.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"VPNTunnel '{tunnel_name}' already exists"
                )
            raise APIError(e.resp.status, str(e))

    def delete_vpn_tunnel(self, region: str, tunnel_name: str) -> bool:
        """Delete a VPN tunnel.

        Args:
            region: The region of the VPN tunnel
            tunnel_name: The name of the VPN tunnel to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the tunnel does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Deleting VPN tunnel %s in region %s", tunnel_name, region
        )

        try:
            self.service.vpnTunnels().delete(
                project=self.project_id, region=region, vpnTunnel=tunnel_name
            ).execute()
            logger.info("Deleted VPN tunnel %s", tunnel_name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("VPNTunnel", tunnel_name)
            raise APIError(e.resp.status, str(e))
