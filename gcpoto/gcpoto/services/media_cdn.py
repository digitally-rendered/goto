"""Service implementation for Google Cloud Media CDN."""

import logging
from typing import List, Optional, Dict, Any

from gcpoto.services.base import GCPService
from gcpoto.models.media_cdn import EdgeCacheService, EdgeCacheOrigin
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class MediaCDNService(GCPService[EdgeCacheService]):
    """Service for interacting with Google Cloud Media CDN."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the Media CDN service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="networkservices",
            version="v1",
            credentials_file=credentials_file,
            resource_model=EdgeCacheService,
        )

    # --- Edge Cache Service methods ---

    def list_edge_cache_services(
        self, location: str
    ) -> List[EdgeCacheService]:
        """List Edge Cache Services in the project.

        Args:
            location: The location to list services in

        Returns:
            A list of EdgeCacheService instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug("Listing Media CDN edge cache services in %s", parent)

        request = (
            self.service.projects()
            .locations()
            .edgeCacheServices()
            .list(parent=parent)
        )
        response = request.execute()
        services = [
            EdgeCacheService.from_api_response(item)
            for item in response.get("edgeCacheServices", [])
        ]
        logger.info(
            "Found %s edge cache service(s) in %s", len(services), parent
        )
        return services

    def get_edge_cache_service(
        self, location: str, service_name: str
    ) -> EdgeCacheService:
        """Get a specific Edge Cache Service by name.

        Args:
            location: The location of the service
            service_name: The name of the service

        Returns:
            An EdgeCacheService instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/edgeCacheServices/{service_name}"
        )
        logger.debug("Getting Media CDN edge cache service %s", name)

        request = (
            self.service.projects()
            .locations()
            .edgeCacheServices()
            .get(name=name)
        )
        response = request.execute()
        return EdgeCacheService.from_api_response(response)

    def create_edge_cache_service(
        self,
        location: str,
        service_name: str,
        routing: Dict[str, Any],
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new Edge Cache Service.

        Args:
            location: The location for the service
            service_name: The name for the new service
            routing: Routing configuration
            labels: Resource labels to apply

        Returns:
            The operation response dictionary
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.info(
            "Creating Media CDN edge cache service %s in %s",
            service_name,
            parent,
        )

        body: Dict[str, Any] = {
            "routing": routing,
        }

        if labels:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .edgeCacheServices()
            .create(
                parent=parent,
                edgeCacheServiceId=service_name,
                body=body,
            )
        )
        response = request.execute()
        logger.info(
            "Edge cache service creation initiated for %s", service_name
        )
        return response

    def update_edge_cache_service(
        self,
        location: str,
        service_name: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an Edge Cache Service.

        Args:
            location: The location of the service
            service_name: The name of the service
            update_mask: The field mask specifying which fields to update
            update_fields: The fields to update

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/edgeCacheServices/{service_name}"
        )
        logger.info("Updating Media CDN edge cache service %s", name)

        request = (
            self.service.projects()
            .locations()
            .edgeCacheServices()
            .patch(name=name, updateMask=update_mask, body=update_fields)
        )
        response = request.execute()
        logger.info(
            "Edge cache service update initiated for %s", service_name
        )
        return response

    def delete_edge_cache_service(
        self, location: str, service_name: str
    ) -> Dict[str, Any]:
        """Delete an Edge Cache Service.

        Args:
            location: The location of the service
            service_name: The name of the service to delete

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/edgeCacheServices/{service_name}"
        )
        logger.info("Deleting Media CDN edge cache service %s", name)

        request = (
            self.service.projects()
            .locations()
            .edgeCacheServices()
            .delete(name=name)
        )
        response = request.execute()
        logger.info(
            "Edge cache service deletion initiated for %s", service_name
        )
        return response

    # --- Edge Cache Origin methods ---

    def list_edge_cache_origins(
        self, location: str
    ) -> List[EdgeCacheOrigin]:
        """List Edge Cache Origins in the project.

        Args:
            location: The location to list origins in

        Returns:
            A list of EdgeCacheOrigin instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug("Listing Media CDN edge cache origins in %s", parent)

        request = (
            self.service.projects()
            .locations()
            .edgeCacheOrigins()
            .list(parent=parent)
        )
        response = request.execute()
        origins = [
            EdgeCacheOrigin.from_api_response(item)
            for item in response.get("edgeCacheOrigins", [])
        ]
        logger.info(
            "Found %s edge cache origin(s) in %s", len(origins), parent
        )
        return origins

    def get_edge_cache_origin(
        self, location: str, origin_name: str
    ) -> EdgeCacheOrigin:
        """Get a specific Edge Cache Origin by name.

        Args:
            location: The location of the origin
            origin_name: The name of the origin

        Returns:
            An EdgeCacheOrigin instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/edgeCacheOrigins/{origin_name}"
        )
        logger.debug("Getting Media CDN edge cache origin %s", name)

        request = (
            self.service.projects()
            .locations()
            .edgeCacheOrigins()
            .get(name=name)
        )
        response = request.execute()
        return EdgeCacheOrigin.from_api_response(response)

    def create_edge_cache_origin(
        self,
        location: str,
        origin_name: str,
        origin_address: str,
        protocol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new Edge Cache Origin.

        Args:
            location: The location for the origin
            origin_name: The name for the new origin
            origin_address: The origin address (IP or hostname)
            protocol: Optional protocol (HTTP, HTTPS, HTTP2)

        Returns:
            The operation response dictionary
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.info(
            "Creating Media CDN edge cache origin %s in %s",
            origin_name,
            parent,
        )

        body: Dict[str, Any] = {
            "originAddress": origin_address,
        }

        if protocol:
            body["protocol"] = protocol

        request = (
            self.service.projects()
            .locations()
            .edgeCacheOrigins()
            .create(
                parent=parent,
                edgeCacheOriginId=origin_name,
                body=body,
            )
        )
        response = request.execute()
        logger.info(
            "Edge cache origin creation initiated for %s", origin_name
        )
        return response

    def update_edge_cache_origin(
        self,
        location: str,
        origin_name: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an Edge Cache Origin.

        Args:
            location: The location of the origin
            origin_name: The name of the origin
            update_mask: The field mask specifying which fields to update
            update_fields: The fields to update

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/edgeCacheOrigins/{origin_name}"
        )
        logger.info("Updating Media CDN edge cache origin %s", name)

        request = (
            self.service.projects()
            .locations()
            .edgeCacheOrigins()
            .patch(name=name, updateMask=update_mask, body=update_fields)
        )
        response = request.execute()
        logger.info(
            "Edge cache origin update initiated for %s", origin_name
        )
        return response

    def delete_edge_cache_origin(
        self, location: str, origin_name: str
    ) -> Dict[str, Any]:
        """Delete an Edge Cache Origin.

        Args:
            location: The location of the origin
            origin_name: The name of the origin to delete

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/edgeCacheOrigins/{origin_name}"
        )
        logger.info("Deleting Media CDN edge cache origin %s", name)

        request = (
            self.service.projects()
            .locations()
            .edgeCacheOrigins()
            .delete(name=name)
        )
        response = request.execute()
        logger.info(
            "Edge cache origin deletion initiated for %s", origin_name
        )
        return response
