"""Service implementation for Google Cloud VPC / Networking."""

import logging
from typing import List, Optional, Dict, Any

from gcpoto.services.base import GCPService
from gcpoto.models.networking import VPCNetwork, Subnet, FirewallRule, StaticAddress

logger = logging.getLogger(__name__)

class NetworkingService(GCPService[VPCNetwork]):
    """Service for interacting with Google Cloud VPC / Networking resources.

    This service wraps the Compute Engine API for networking resources
    including VPC networks, subnets, firewall rules, and static addresses.
    """

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the networking service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="compute",
            version="v1",
            credentials_file=credentials_file,
            resource_model=VPCNetwork,
        )

    # ---- VPC Networks ----

    def list_networks(self, **kwargs) -> List[VPCNetwork]:
        """List VPC networks in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of VPCNetwork instances
        """
        logger.debug("Listing VPC networks for project %s", self.project_id)
        request = self.service.networks().list(
            project=self.project_id, **kwargs
        )
        response = self._execute(request)
        return [
            VPCNetwork.from_api_response(item)
            for item in response.get("items", [])
        ]

    def get_network(self, network_name: str) -> VPCNetwork:
        """Get a specific VPC network by name.

        Args:
            network_name: The name of the network

        Returns:
            A VPCNetwork instance
        """
        logger.debug(
            "Getting VPC network %s for project %s",
            network_name,
            self.project_id,
        )
        request = self.service.networks().get(
            project=self.project_id, network=network_name
        )
        response = self._execute(request)
        return VPCNetwork.from_api_response(response)

    def create_network(
        self,
        network_name: str,
        auto_create_subnetworks: bool = True,
        routing_mode: str = "REGIONAL",
        description: Optional[str] = None,
    ) -> VPCNetwork:
        """Create a new VPC network.

        Args:
            network_name: The name of the network to create
            auto_create_subnetworks: Whether to auto-create subnets
            routing_mode: The routing mode (REGIONAL or GLOBAL)
            description: Optional description

        Returns:
            The created VPCNetwork instance
        """
        logger.info(
            "Creating VPC network %s in project %s",
            network_name,
            self.project_id,
        )
        body: Dict[str, Any] = {
            "name": network_name,
            "autoCreateSubnetworks": auto_create_subnetworks,
            "routingConfig": {"routingMode": routing_mode},
        }
        if description is not None:
            body["description"] = description

        request = self.service.networks().insert(
            project=self.project_id, body=body
        )
        response = self._execute(request)
        return VPCNetwork.from_api_response(response)

    def delete_network(self, network_name: str) -> bool:
        """Delete a VPC network.

        Args:
            network_name: The name of the network to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting VPC network %s from project %s",
            network_name,
            self.project_id,
        )
        request = self.service.networks().delete(
            project=self.project_id, network=network_name
        )
        self._execute(request)
        return True

    # ---- Subnets ----

    def list_subnets(self, region: Optional[str] = None, **kwargs) -> List[Subnet]:
        """List subnets in the project.

        If region is specified, lists subnets in that region only.
        Otherwise, lists subnets across all regions (aggregated).

        Args:
            region: Optional region to filter subnets
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of Subnet instances
        """
        logger.debug(
            "Listing subnets for project %s (region=%s)",
            self.project_id,
            region,
        )
        if region:
            request = self.service.subnetworks().list(
                project=self.project_id, region=region, **kwargs
            )
            response = self._execute(request)
            return [
                Subnet.from_api_response(item)
                for item in response.get("items", [])
            ]
        else:
            request = self.service.subnetworks().aggregatedList(
                project=self.project_id, **kwargs
            )
            response = self._execute(request)
            subnets = []
            for region_data in response.get("items", {}).values():
                for item in region_data.get("subnetworks", []):
                    subnets.append(Subnet.from_api_response(item))
            return subnets

    def get_subnet(self, region: str, subnet_name: str) -> Subnet:
        """Get a specific subnet by name and region.

        Args:
            region: The region of the subnet
            subnet_name: The name of the subnet

        Returns:
            A Subnet instance
        """
        logger.debug(
            "Getting subnet %s in region %s for project %s",
            subnet_name,
            region,
            self.project_id,
        )
        request = self.service.subnetworks().get(
            project=self.project_id, region=region, subnetwork=subnet_name
        )
        response = self._execute(request)
        return Subnet.from_api_response(response)

    def create_subnet(
        self,
        region: str,
        subnet_name: str,
        network: str,
        ip_cidr_range: str,
        secondary_ip_ranges: Optional[List[Dict]] = None,
    ) -> Subnet:
        """Create a new subnet.

        Args:
            region: The region to create the subnet in
            subnet_name: The name of the subnet
            network: The URL or name of the network
            ip_cidr_range: The IPv4 CIDR range for the subnet
            secondary_ip_ranges: Optional secondary IP ranges

        Returns:
            The created Subnet instance
        """
        logger.info(
            "Creating subnet %s in region %s for project %s",
            subnet_name,
            region,
            self.project_id,
        )
        body: Dict[str, Any] = {
            "name": subnet_name,
            "network": network,
            "ipCidrRange": ip_cidr_range,
        }
        if secondary_ip_ranges is not None:
            body["secondaryIpRanges"] = secondary_ip_ranges

        request = self.service.subnetworks().insert(
            project=self.project_id, region=region, body=body
        )
        response = self._execute(request)
        return Subnet.from_api_response(response)

    def delete_subnet(self, region: str, subnet_name: str) -> bool:
        """Delete a subnet.

        Args:
            region: The region of the subnet
            subnet_name: The name of the subnet to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting subnet %s in region %s from project %s",
            subnet_name,
            region,
            self.project_id,
        )
        request = self.service.subnetworks().delete(
            project=self.project_id, region=region, subnetwork=subnet_name
        )
        self._execute(request)
        return True

    # ---- Firewall Rules ----

    def list_firewall_rules(self, **kwargs) -> List[FirewallRule]:
        """List firewall rules in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of FirewallRule instances
        """
        logger.debug(
            "Listing firewall rules for project %s", self.project_id
        )
        request = self.service.firewalls().list(
            project=self.project_id, **kwargs
        )
        response = self._execute(request)
        return [
            FirewallRule.from_api_response(item)
            for item in response.get("items", [])
        ]

    def get_firewall_rule(self, firewall_name: str) -> FirewallRule:
        """Get a specific firewall rule by name.

        Args:
            firewall_name: The name of the firewall rule

        Returns:
            A FirewallRule instance
        """
        logger.debug(
            "Getting firewall rule %s for project %s",
            firewall_name,
            self.project_id,
        )
        request = self.service.firewalls().get(
            project=self.project_id, firewall=firewall_name
        )
        response = self._execute(request)
        return FirewallRule.from_api_response(response)

    def create_firewall_rule(
        self,
        firewall_name: str,
        network: str,
        direction: str,
        priority: int,
        allowed: Optional[List[Dict]] = None,
        denied: Optional[List[Dict]] = None,
        source_ranges: Optional[List[str]] = None,
        target_tags: Optional[List[str]] = None,
    ) -> FirewallRule:
        """Create a new firewall rule.

        Args:
            firewall_name: The name of the firewall rule
            network: The URL or name of the network
            direction: Direction of traffic (INGRESS or EGRESS)
            priority: Priority of the rule (0-65535)
            allowed: List of allowed protocols and ports
            denied: List of denied protocols and ports
            source_ranges: Source IP CIDR ranges
            target_tags: Target instance tags

        Returns:
            The created FirewallRule instance
        """
        logger.info(
            "Creating firewall rule %s in project %s",
            firewall_name,
            self.project_id,
        )
        body: Dict[str, Any] = {
            "name": firewall_name,
            "network": network,
            "direction": direction,
            "priority": priority,
        }
        if allowed is not None:
            body["allowed"] = allowed
        if denied is not None:
            body["denied"] = denied
        if source_ranges is not None:
            body["sourceRanges"] = source_ranges
        if target_tags is not None:
            body["targetTags"] = target_tags

        request = self.service.firewalls().insert(
            project=self.project_id, body=body
        )
        response = self._execute(request)
        return FirewallRule.from_api_response(response)

    def update_firewall_rule(
        self, firewall_name: str, **kwargs
    ) -> FirewallRule:
        """Update an existing firewall rule.

        Args:
            firewall_name: The name of the firewall rule to update
            **kwargs: Fields to update (allowed, denied, source_ranges,
                target_tags, priority, disabled, etc.)

        Returns:
            The updated FirewallRule instance
        """
        logger.info(
            "Updating firewall rule %s in project %s",
            firewall_name,
            self.project_id,
        )
        body: Dict[str, Any] = {}
        field_mapping = {
            "allowed": "allowed",
            "denied": "denied",
            "source_ranges": "sourceRanges",
            "destination_ranges": "destinationRanges",
            "source_tags": "sourceTags",
            "target_tags": "targetTags",
            "priority": "priority",
            "disabled": "disabled",
            "direction": "direction",
            "description": "description",
        }
        for python_key, api_key in field_mapping.items():
            if python_key in kwargs:
                body[api_key] = kwargs[python_key]

        request = self.service.firewalls().patch(
            project=self.project_id, firewall=firewall_name, body=body
        )
        response = self._execute(request)
        return FirewallRule.from_api_response(response)

    def delete_firewall_rule(self, firewall_name: str) -> bool:
        """Delete a firewall rule.

        Args:
            firewall_name: The name of the firewall rule to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting firewall rule %s from project %s",
            firewall_name,
            self.project_id,
        )
        request = self.service.firewalls().delete(
            project=self.project_id, firewall=firewall_name
        )
        self._execute(request)
        return True

    # ---- Static Addresses ----

    def list_addresses(self, region: str, **kwargs) -> List[StaticAddress]:
        """List static addresses in a region.

        Args:
            region: The region to list addresses from
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of StaticAddress instances
        """
        logger.debug(
            "Listing addresses in region %s for project %s",
            region,
            self.project_id,
        )
        request = self.service.addresses().list(
            project=self.project_id, region=region, **kwargs
        )
        response = self._execute(request)
        return [
            StaticAddress.from_api_response(item)
            for item in response.get("items", [])
        ]

    def reserve_address(
        self,
        region: str,
        address_name: str,
        address_type: str = "EXTERNAL",
    ) -> StaticAddress:
        """Reserve a new static address.

        Args:
            region: The region to reserve the address in
            address_name: The name of the address
            address_type: The type of address (INTERNAL or EXTERNAL)

        Returns:
            The reserved StaticAddress instance
        """
        logger.info(
            "Reserving %s address %s in region %s for project %s",
            address_type,
            address_name,
            region,
            self.project_id,
        )
        body: Dict[str, Any] = {
            "name": address_name,
            "addressType": address_type,
        }

        request = self.service.addresses().insert(
            project=self.project_id, region=region, body=body
        )
        response = self._execute(request)
        return StaticAddress.from_api_response(response)

    def release_address(self, region: str, address_name: str) -> bool:
        """Release (delete) a static address.

        Args:
            region: The region of the address
            address_name: The name of the address to release

        Returns:
            True if the release was successful
        """
        logger.info(
            "Releasing address %s in region %s from project %s",
            address_name,
            region,
            self.project_id,
        )
        request = self.service.addresses().delete(
            project=self.project_id, region=region, address=address_name
        )
        self._execute(request)
        return True
