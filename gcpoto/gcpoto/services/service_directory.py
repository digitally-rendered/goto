"""Service implementation for Google Cloud Service Directory."""

import logging
from typing import List, Optional, Dict, Any

from gcpoto.services.base import GCPService
from gcpoto.models.service_directory import Namespace, ServiceEntry, Endpoint
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class ServiceDirectoryService(GCPService[Namespace]):
    """Service for interacting with Google Cloud Service Directory."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the Service Directory service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="servicedirectory",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Namespace,
        )

    def _namespace_path(self, location: str, namespace_id: str) -> str:
        """Format a full namespace resource path.

        Args:
            location: The GCP location
            namespace_id: The namespace ID

        Returns:
            The fully-qualified namespace path
        """
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/namespaces/{namespace_id}"
        )

    def _service_path(
        self, location: str, namespace_id: str, service_id: str
    ) -> str:
        """Format a full service resource path.

        Args:
            location: The GCP location
            namespace_id: The namespace ID
            service_id: The service ID

        Returns:
            The fully-qualified service path
        """
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/namespaces/{namespace_id}/services/{service_id}"
        )

    def _endpoint_path(
        self,
        location: str,
        namespace_id: str,
        service_id: str,
        endpoint_id: str,
    ) -> str:
        """Format a full endpoint resource path.

        Args:
            location: The GCP location
            namespace_id: The namespace ID
            service_id: The service ID
            endpoint_id: The endpoint ID

        Returns:
            The fully-qualified endpoint path
        """
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/namespaces/{namespace_id}/services/{service_id}"
            f"/endpoints/{endpoint_id}"
        )

    # --- Namespace methods ---

    def list_namespaces(self, location: str) -> List[Namespace]:
        """List namespaces in a location.

        Args:
            location: The GCP location (e.g. us-central1)

        Returns:
            A list of Namespace instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug("Listing Service Directory namespaces in %s", parent)
        all_namespaces = []
        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .list(parent=parent)
        )
        while request is not None:
            response = request.execute()
            namespaces = response.get("namespaces", [])
            all_namespaces.extend(
                Namespace.from_api_response(item) for item in namespaces
            )
            request = (
                self.service.projects()
                .locations()
                .namespaces()
                .list_next(request, response)
            )
        return all_namespaces

    def get_namespace(
        self, location: str, namespace_id: str
    ) -> Namespace:
        """Get a specific namespace by ID.

        Args:
            location: The GCP location
            namespace_id: The namespace ID

        Returns:
            A Namespace instance
        """
        name = self._namespace_path(location, namespace_id)
        logger.debug("Getting Service Directory namespace %s", name)
        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .get(name=name)
        )
        response = request.execute()
        return Namespace.from_api_response(response)

    def create_namespace(
        self,
        location: str,
        namespace_id: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> Namespace:
        """Create a new namespace.

        Args:
            location: The GCP location
            namespace_id: The ID for the new namespace
            labels: Labels to apply to the namespace

        Returns:
            The created Namespace
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.info(
            "Creating Service Directory namespace %s in %s",
            namespace_id,
            parent,
        )

        body = {}

        if labels:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .create(parent=parent, namespaceId=namespace_id, body=body)
        )
        response = request.execute()
        return Namespace.from_api_response(response)

    def delete_namespace(
        self, location: str, namespace_id: str
    ) -> bool:
        """Delete a namespace.

        Args:
            location: The GCP location
            namespace_id: The namespace ID

        Returns:
            True if the deletion was successful
        """
        name = self._namespace_path(location, namespace_id)
        logger.info("Deleting Service Directory namespace %s", name)
        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .delete(name=name)
        )
        request.execute()
        return True

    # --- Service methods ---

    def list_services(
        self, location: str, namespace_id: str
    ) -> List[ServiceEntry]:
        """List services in a namespace.

        Args:
            location: The GCP location
            namespace_id: The namespace ID

        Returns:
            A list of ServiceEntry instances
        """
        parent = self._namespace_path(location, namespace_id)
        logger.debug(
            "Listing services in Service Directory namespace %s", parent
        )
        all_services = []
        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .services()
            .list(parent=parent)
        )
        while request is not None:
            response = request.execute()
            services = response.get("services", [])
            all_services.extend(
                ServiceEntry.from_api_response(item) for item in services
            )
            request = (
                self.service.projects()
                .locations()
                .namespaces()
                .services()
                .list_next(request, response)
            )
        return all_services

    def get_service(
        self, location: str, namespace_id: str, service_id: str
    ) -> ServiceEntry:
        """Get a specific service by ID.

        Args:
            location: The GCP location
            namespace_id: The namespace ID
            service_id: The service ID

        Returns:
            A ServiceEntry instance
        """
        name = self._service_path(location, namespace_id, service_id)
        logger.debug("Getting Service Directory service %s", name)
        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .services()
            .get(name=name)
        )
        response = request.execute()
        return ServiceEntry.from_api_response(response)

    def create_service(
        self,
        location: str,
        namespace_id: str,
        service_id: str,
        metadata: Optional[Dict] = None,
    ) -> ServiceEntry:
        """Create a new service in a namespace.

        Args:
            location: The GCP location
            namespace_id: The namespace ID
            service_id: The ID for the new service
            metadata: Metadata for the service

        Returns:
            The created ServiceEntry
        """
        parent = self._namespace_path(location, namespace_id)
        logger.info(
            "Creating Service Directory service %s in namespace %s",
            service_id,
            parent,
        )

        body = {}

        if metadata is not None:
            body["metadata"] = metadata

        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .services()
            .create(parent=parent, serviceId=service_id, body=body)
        )
        response = request.execute()
        return ServiceEntry.from_api_response(response)

    def delete_service(
        self, location: str, namespace_id: str, service_id: str
    ) -> bool:
        """Delete a service from a namespace.

        Args:
            location: The GCP location
            namespace_id: The namespace ID
            service_id: The service ID

        Returns:
            True if the deletion was successful
        """
        name = self._service_path(location, namespace_id, service_id)
        logger.info("Deleting Service Directory service %s", name)
        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .services()
            .delete(name=name)
        )
        request.execute()
        return True

    # --- Endpoint methods ---

    def list_endpoints(
        self, location: str, namespace_id: str, service_id: str
    ) -> List[Endpoint]:
        """List endpoints in a service.

        Args:
            location: The GCP location
            namespace_id: The namespace ID
            service_id: The service ID

        Returns:
            A list of Endpoint instances
        """
        parent = self._service_path(location, namespace_id, service_id)
        logger.debug(
            "Listing endpoints in Service Directory service %s", parent
        )
        all_endpoints = []
        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .services()
            .endpoints()
            .list(parent=parent)
        )
        while request is not None:
            response = request.execute()
            endpoints = response.get("endpoints", [])
            all_endpoints.extend(
                Endpoint.from_api_response(item) for item in endpoints
            )
            request = (
                self.service.projects()
                .locations()
                .namespaces()
                .services()
                .endpoints()
                .list_next(request, response)
            )
        return all_endpoints

    def get_endpoint(
        self,
        location: str,
        namespace_id: str,
        service_id: str,
        endpoint_id: str,
    ) -> Endpoint:
        """Get a specific endpoint by ID.

        Args:
            location: The GCP location
            namespace_id: The namespace ID
            service_id: The service ID
            endpoint_id: The endpoint ID

        Returns:
            An Endpoint instance
        """
        name = self._endpoint_path(
            location, namespace_id, service_id, endpoint_id
        )
        logger.debug("Getting Service Directory endpoint %s", name)
        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .services()
            .endpoints()
            .get(name=name)
        )
        response = request.execute()
        return Endpoint.from_api_response(response)

    def create_endpoint(
        self,
        location: str,
        namespace_id: str,
        service_id: str,
        endpoint_id: str,
        address: Optional[str] = None,
        port: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> Endpoint:
        """Create a new endpoint in a service.

        Args:
            location: The GCP location
            namespace_id: The namespace ID
            service_id: The service ID
            endpoint_id: The ID for the new endpoint
            address: The IP address for the endpoint
            port: The port number for the endpoint
            metadata: Metadata for the endpoint

        Returns:
            The created Endpoint
        """
        parent = self._service_path(location, namespace_id, service_id)
        logger.info(
            "Creating Service Directory endpoint %s in service %s",
            endpoint_id,
            parent,
        )

        body = {}

        if address is not None:
            body["address"] = address

        if port is not None:
            body["port"] = port

        if metadata is not None:
            body["metadata"] = metadata

        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .services()
            .endpoints()
            .create(parent=parent, endpointId=endpoint_id, body=body)
        )
        response = request.execute()
        return Endpoint.from_api_response(response)

    def delete_endpoint(
        self,
        location: str,
        namespace_id: str,
        service_id: str,
        endpoint_id: str,
    ) -> bool:
        """Delete an endpoint from a service.

        Args:
            location: The GCP location
            namespace_id: The namespace ID
            service_id: The service ID
            endpoint_id: The endpoint ID

        Returns:
            True if the deletion was successful
        """
        name = self._endpoint_path(
            location, namespace_id, service_id, endpoint_id
        )
        logger.info("Deleting Service Directory endpoint %s", name)
        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .services()
            .endpoints()
            .delete(name=name)
        )
        request.execute()
        return True

    # --- Resolve method ---

    def resolve_service(
        self, location: str, namespace_id: str, service_id: str
    ) -> ServiceEntry:
        """Resolve a service to get its endpoints.

        Args:
            location: The GCP location
            namespace_id: The namespace ID
            service_id: The service ID

        Returns:
            A ServiceEntry with resolved endpoints
        """
        name = self._service_path(location, namespace_id, service_id)
        logger.debug("Resolving Service Directory service %s", name)
        request = (
            self.service.projects()
            .locations()
            .namespaces()
            .services()
            .resolve(name=name)
        )
        response = request.execute()
        return ServiceEntry.from_api_response(response.get("service", {}))
