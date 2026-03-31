"""Service implementation for Google Cloud CDN / Backend Services."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.cdn import BackendService, UrlMap, HealthCheck
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
)

logger = logging.getLogger(__name__)


class CDNService(GCPService[BackendService]):
    """Service for interacting with Google Cloud CDN and Backend Services."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud CDN service.

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
            resource_model=BackendService,
            **kwargs,
        )

    # ---- Backend Services ----

    def list_backend_services(self, **kwargs) -> List[BackendService]:
        """List backend services in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of BackendService instances
        """
        logger.info(
            "Listing backend services for project %s", self.project_id
        )

        request = self.service.backendServices().list(
            project=self.project_id, **kwargs
        )

        services = []
        while request is not None:
            response = request.execute()
            for item in response.get("items", []):
                services.append(BackendService.from_api_response(item))
            request = self.service.backendServices().list_next(
                request, response
            )

        logger.info("Found %s backend services", len(services))
        return services

    def get_backend_service(self, name: str) -> BackendService:
        """Get a specific backend service by name.

        Args:
            name: The name of the backend service to retrieve

        Returns:
            A BackendService instance

        Raises:
            ResourceNotFoundError: If the backend service does not exist
            APIError: If the API call fails
        """
        logger.info("Getting backend service %s", name)

        try:
            request = self.service.backendServices().get(
                project=self.project_id, backendService=name
            )
            response = request.execute()
            return BackendService.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("BackendService", name)
            raise APIError(e.resp.status, str(e))

    def create_backend_service(
        self,
        name: str,
        backends: List[Dict],
        health_checks: List[str],
        protocol: str = "HTTP",
        enable_cdn: bool = False,
        cdn_policy: Optional[Dict] = None,
    ) -> BackendService:
        """Create a new backend service.

        Args:
            name: The name of the backend service to create
            backends: List of backend configurations
            health_checks: List of health check URLs
            protocol: The protocol to use (HTTP, HTTPS, HTTP2, TCP, SSL, GRPC)
            enable_cdn: Whether to enable Cloud CDN
            cdn_policy: Optional CDN policy configuration

        Returns:
            A BackendService instance for the newly created service

        Raises:
            ResourceAlreadyExistsError: If the backend service already exists
            APIError: If the API call fails
        """
        logger.info("Creating backend service %s", name)

        body = {
            "name": name,
            "backends": backends,
            "healthChecks": health_checks,
            "protocol": protocol,
            "enableCDN": enable_cdn,
        }
        if cdn_policy is not None:
            body["cdnPolicy"] = cdn_policy

        try:
            request = self.service.backendServices().insert(
                project=self.project_id, body=body
            )
            request.execute()
            logger.info("Created backend service %s", name)
            return self.get_backend_service(name)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"BackendService '{name}' already exists"
                )
            raise APIError(e.resp.status, str(e))

    def update_backend_service(
        self, name: str, update_fields: Dict[str, Any]
    ) -> BackendService:
        """Update an existing backend service.

        Args:
            name: The name of the backend service to update
            update_fields: Dictionary of fields to update

        Returns:
            A BackendService instance for the updated service

        Raises:
            ResourceNotFoundError: If the backend service does not exist
            APIError: If the API call fails
        """
        logger.info("Updating backend service %s", name)

        try:
            request = self.service.backendServices().patch(
                project=self.project_id, backendService=name, body=update_fields
            )
            request.execute()
            logger.info("Updated backend service %s", name)
            return self.get_backend_service(name)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("BackendService", name)
            raise APIError(e.resp.status, str(e))

    def delete_backend_service(self, name: str) -> bool:
        """Delete a backend service.

        Args:
            name: The name of the backend service to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the backend service does not exist
            APIError: If the API call fails
        """
        logger.info("Deleting backend service %s", name)

        try:
            self.service.backendServices().delete(
                project=self.project_id, backendService=name
            ).execute()
            logger.info("Deleted backend service %s", name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("BackendService", name)
            raise APIError(e.resp.status, str(e))

    # ---- URL Maps ----

    def list_url_maps(self, **kwargs) -> List[UrlMap]:
        """List URL maps in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of UrlMap instances
        """
        logger.info("Listing URL maps for project %s", self.project_id)

        request = self.service.urlMaps().list(
            project=self.project_id, **kwargs
        )

        url_maps = []
        while request is not None:
            response = request.execute()
            for item in response.get("items", []):
                url_maps.append(UrlMap.from_api_response(item))
            request = self.service.urlMaps().list_next(request, response)

        logger.info("Found %s URL maps", len(url_maps))
        return url_maps

    def get_url_map(self, name: str) -> UrlMap:
        """Get a specific URL map by name.

        Args:
            name: The name of the URL map to retrieve

        Returns:
            A UrlMap instance

        Raises:
            ResourceNotFoundError: If the URL map does not exist
            APIError: If the API call fails
        """
        logger.info("Getting URL map %s", name)

        try:
            request = self.service.urlMaps().get(
                project=self.project_id, urlMap=name
            )
            response = request.execute()
            return UrlMap.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("UrlMap", name)
            raise APIError(e.resp.status, str(e))

    def create_url_map(
        self,
        name: str,
        default_service: str,
        host_rules: Optional[List[Dict]] = None,
        path_matchers: Optional[List[Dict]] = None,
    ) -> UrlMap:
        """Create a new URL map.

        Args:
            name: The name of the URL map to create
            default_service: The full URL of the default backend service
            host_rules: Optional host rules for routing
            path_matchers: Optional path matchers for routing

        Returns:
            A UrlMap instance for the newly created URL map

        Raises:
            ResourceAlreadyExistsError: If the URL map already exists
            APIError: If the API call fails
        """
        logger.info("Creating URL map %s", name)

        body = {
            "name": name,
            "defaultService": default_service,
        }
        if host_rules is not None:
            body["hostRules"] = host_rules
        if path_matchers is not None:
            body["pathMatchers"] = path_matchers

        try:
            request = self.service.urlMaps().insert(
                project=self.project_id, body=body
            )
            request.execute()
            logger.info("Created URL map %s", name)
            return self.get_url_map(name)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"UrlMap '{name}' already exists"
                )
            raise APIError(e.resp.status, str(e))

    def delete_url_map(self, name: str) -> bool:
        """Delete a URL map.

        Args:
            name: The name of the URL map to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the URL map does not exist
            APIError: If the API call fails
        """
        logger.info("Deleting URL map %s", name)

        try:
            self.service.urlMaps().delete(
                project=self.project_id, urlMap=name
            ).execute()
            logger.info("Deleted URL map %s", name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("UrlMap", name)
            raise APIError(e.resp.status, str(e))

    # ---- Health Checks ----

    def list_health_checks(self, **kwargs) -> List[HealthCheck]:
        """List health checks in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of HealthCheck instances
        """
        logger.info("Listing health checks for project %s", self.project_id)

        request = self.service.healthChecks().list(
            project=self.project_id, **kwargs
        )

        health_checks = []
        while request is not None:
            response = request.execute()
            for item in response.get("items", []):
                health_checks.append(HealthCheck.from_api_response(item))
            request = self.service.healthChecks().list_next(request, response)

        logger.info("Found %s health checks", len(health_checks))
        return health_checks

    def get_health_check(self, name: str) -> HealthCheck:
        """Get a specific health check by name.

        Args:
            name: The name of the health check to retrieve

        Returns:
            A HealthCheck instance

        Raises:
            ResourceNotFoundError: If the health check does not exist
            APIError: If the API call fails
        """
        logger.info("Getting health check %s", name)

        try:
            request = self.service.healthChecks().get(
                project=self.project_id, healthCheck=name
            )
            response = request.execute()
            return HealthCheck.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("HealthCheck", name)
            raise APIError(e.resp.status, str(e))

    def create_health_check(
        self,
        name: str,
        check_type: str,
        port: Optional[int] = None,
        request_path: Optional[str] = None,
        check_interval_sec: Optional[int] = None,
        timeout_sec: Optional[int] = None,
    ) -> HealthCheck:
        """Create a new health check.

        Args:
            name: The name of the health check to create
            check_type: The type of health check (HTTP, HTTPS, TCP, SSL, HTTP2)
            port: Optional port number for the health check
            request_path: Optional request path for HTTP/HTTPS health checks
            check_interval_sec: Optional interval between checks in seconds
            timeout_sec: Optional timeout for each check in seconds

        Returns:
            A HealthCheck instance for the newly created health check

        Raises:
            ResourceAlreadyExistsError: If the health check already exists
            APIError: If the API call fails
        """
        logger.info("Creating health check %s (type %s)", name, check_type)

        body = {
            "name": name,
            "type": check_type.upper(),
        }

        if check_interval_sec is not None:
            body["checkIntervalSec"] = check_interval_sec
        if timeout_sec is not None:
            body["timeoutSec"] = timeout_sec

        # Build the type-specific health check configuration
        type_config = {}
        if port is not None:
            type_config["port"] = port
        if request_path is not None:
            type_config["requestPath"] = request_path

        type_key_map = {
            "HTTP": "httpHealthCheck",
            "HTTPS": "httpsHealthCheck",
            "TCP": "tcpHealthCheck",
            "SSL": "sslHealthCheck",
            "HTTP2": "http2HealthCheck",
        }
        config_key = type_key_map.get(check_type.upper())
        if config_key and type_config:
            body[config_key] = type_config

        try:
            request = self.service.healthChecks().insert(
                project=self.project_id, body=body
            )
            request.execute()
            logger.info("Created health check %s", name)
            return self.get_health_check(name)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"HealthCheck '{name}' already exists"
                )
            raise APIError(e.resp.status, str(e))

    def delete_health_check(self, name: str) -> bool:
        """Delete a health check.

        Args:
            name: The name of the health check to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the health check does not exist
            APIError: If the API call fails
        """
        logger.info("Deleting health check %s", name)

        try:
            self.service.healthChecks().delete(
                project=self.project_id, healthCheck=name
            ).execute()
            logger.info("Deleted health check %s", name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("HealthCheck", name)
            raise APIError(e.resp.status, str(e))

    # ---- Cache Invalidation ----

    def invalidate_cache(
        self,
        url_map_name: str,
        path: str,
        host: Optional[str] = None,
    ) -> bool:
        """Invalidate cached content for a URL map.

        Args:
            url_map_name: The name of the URL map to invalidate cache for
            path: The path pattern to invalidate (e.g. "/images/*")
            host: Optional host to restrict the invalidation to

        Returns:
            True if the invalidation was initiated successfully

        Raises:
            ResourceNotFoundError: If the URL map does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Invalidating cache for URL map %s, path %s",
            url_map_name,
            path,
        )

        body = {"path": path}
        if host is not None:
            body["host"] = host

        try:
            request = self.service.urlMaps().invalidateCache(
                project=self.project_id,
                urlMap=url_map_name,
                body=body,
            )
            request.execute()
            logger.info(
                "Cache invalidation initiated for URL map %s, path %s",
                url_map_name,
                path,
            )
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("UrlMap", url_map_name)
            raise APIError(e.resp.status, str(e))
