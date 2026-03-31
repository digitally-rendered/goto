"""Service implementation for Google Cloud NAT."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.cloud_nat import NATConfig
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class CloudNATService(GCPService[NATConfig]):
    """Service for interacting with Google Cloud NAT (via Compute Routers API)."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud NAT service.

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
            resource_model=NATConfig,
            **kwargs,
        )

    def list_routers(self, region: str) -> List[Dict[str, Any]]:
        """List Cloud Routers in a region.

        Args:
            region: The region to list routers in

        Returns:
            A list of router dictionaries
        """
        logger.info(
            "Listing Cloud Routers in region %s for project %s",
            region,
            self.project_id,
        )

        request = self.service.routers().list(
            project=self.project_id, region=region
        )

        routers = []
        while request is not None:
            response = request.execute()
            for router_data in response.get("items", []):
                routers.append(router_data)
            request = self.service.routers().list_next(request, response)

        logger.info("Found %s Cloud Routers", len(routers))
        return routers

    def get_router(self, region: str, router_name: str) -> Dict[str, Any]:
        """Get a specific Cloud Router.

        Args:
            region: The region of the router
            router_name: The name of the router

        Returns:
            A router dictionary

        Raises:
            ResourceNotFoundError: If the router does not exist
        """
        logger.info("Getting Cloud Router %s in region %s", router_name, region)

        try:
            request = self.service.routers().get(
                project=self.project_id, region=region, router=router_name
            )
            return request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("Router", router_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_nat(
        self,
        region: str,
        router_name: str,
        nat_name: str,
        nat_ip_allocate_option: str = "AUTO_ONLY",
        source_subnetwork_ip_ranges_to_nat: str = "ALL_SUBNETWORKS_ALL_IP_RANGES",
    ) -> NATConfig:
        """Create a NAT configuration on a Cloud Router.

        Args:
            region: The region of the router
            router_name: The name of the router
            nat_name: The name for the NAT configuration
            nat_ip_allocate_option: NAT IP allocation option
            source_subnetwork_ip_ranges_to_nat: Subnetwork IP ranges to NAT

        Returns:
            The created NATConfig instance

        Raises:
            ResourceNotFoundError: If the router does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Creating NAT %s on router %s in region %s",
            nat_name,
            router_name,
            region,
        )

        try:
            router = self.get_router(region, router_name)

            nats = router.get("nats", [])
            nat_config = {
                "name": nat_name,
                "natIpAllocateOption": nat_ip_allocate_option,
                "sourceSubnetworkIpRangesToNat": source_subnetwork_ip_ranges_to_nat,
            }
            nats.append(nat_config)
            router["nats"] = nats

            request = self.service.routers().patch(
                project=self.project_id,
                region=region,
                router=router_name,
                body=router,
            )
            request.execute()

            nat_config["project"] = self.project_id
            nat_config["region"] = region
            nat_config["routerName"] = router_name
            logger.info("Created NAT %s on router %s", nat_name, router_name)
            return NATConfig.from_api_response(nat_config)
        except ResourceNotFoundError:
            raise
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def update_nat(
        self,
        region: str,
        router_name: str,
        nat_name: str,
        update_fields: Dict[str, Any],
    ) -> NATConfig:
        """Update a NAT configuration on a Cloud Router.

        Args:
            region: The region of the router
            router_name: The name of the router
            nat_name: The name of the NAT configuration to update
            update_fields: Dictionary of fields to update

        Returns:
            The updated NATConfig instance

        Raises:
            ResourceNotFoundError: If the router or NAT does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Updating NAT %s on router %s in region %s",
            nat_name,
            router_name,
            region,
        )

        try:
            router = self.get_router(region, router_name)

            nats = router.get("nats", [])
            nat_found = False
            for nat in nats:
                if nat.get("name") == nat_name:
                    nat.update(update_fields)
                    nat_found = True
                    break

            if not nat_found:
                raise ResourceNotFoundError("NATConfig", nat_name)

            router["nats"] = nats

            request = self.service.routers().patch(
                project=self.project_id,
                region=region,
                router=router_name,
                body=router,
            )
            request.execute()

            for nat in nats:
                if nat.get("name") == nat_name:
                    nat["project"] = self.project_id
                    nat["region"] = region
                    nat["routerName"] = router_name
                    logger.info(
                        "Updated NAT %s on router %s", nat_name, router_name
                    )
                    return NATConfig.from_api_response(nat)
        except ResourceNotFoundError:
            raise
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def delete_nat(
        self, region: str, router_name: str, nat_name: str
    ) -> bool:
        """Delete a NAT configuration from a Cloud Router.

        Args:
            region: The region of the router
            router_name: The name of the router
            nat_name: The name of the NAT configuration to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the router or NAT does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Deleting NAT %s from router %s in region %s",
            nat_name,
            router_name,
            region,
        )

        try:
            router = self.get_router(region, router_name)

            nats = router.get("nats", [])
            original_len = len(nats)
            nats = [n for n in nats if n.get("name") != nat_name]

            if len(nats) == original_len:
                raise ResourceNotFoundError("NATConfig", nat_name)

            router["nats"] = nats

            request = self.service.routers().patch(
                project=self.project_id,
                region=region,
                router=router_name,
                body=router,
            )
            request.execute()
            logger.info(
                "Deleted NAT %s from router %s", nat_name, router_name
            )
            return True
        except ResourceNotFoundError:
            raise
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def get_nat_mapping_info(
        self, region: str, router_name: str
    ) -> List[Dict[str, Any]]:
        """Get NAT mapping information for a Cloud Router.

        Args:
            region: The region of the router
            router_name: The name of the router

        Returns:
            A list of NAT mapping info dictionaries

        Raises:
            ResourceNotFoundError: If the router does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Getting NAT mapping info for router %s in region %s",
            router_name,
            region,
        )

        try:
            request = self.service.routers().getNatMappingInfo(
                project=self.project_id, region=region, router=router_name
            )

            mappings = []
            while request is not None:
                response = request.execute()
                for mapping in response.get("result", []):
                    mappings.append(mapping)
                request = self.service.routers().getNatMappingInfo_next(
                    request, response
                )

            logger.info("Found %s NAT mappings", len(mappings))
            return mappings
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("Router", router_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))
