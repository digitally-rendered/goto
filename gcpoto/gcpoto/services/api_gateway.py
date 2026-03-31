"""Service implementation for Google Cloud API Gateway."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.api_gateway import APIGateway, APIConfig
from gcpoto.exceptions import (
    APIError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


class APIGatewayService(GCPService[APIGateway]):
    """Service for interacting with Google Cloud API Gateway."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the API Gateway service.

        Args:
            project_id: The GCP project ID to use for API calls.
            credentials_file: Optional path to a service account credentials
                file.
            **kwargs: Additional arguments to pass to the service constructor.
        """
        super().__init__(
            project_id=project_id,
            service_name="apigateway",
            version="v1",
            credentials_file=credentials_file,
            resource_model=APIGateway,
            **kwargs,
        )

    # ------------------------------------------------------------------ #
    #  Gateway operations
    # ------------------------------------------------------------------ #

    def list_gateways(self, location: str) -> List[APIGateway]:
        """List API Gateways in a given location.

        Args:
            location: The GCP location (e.g. ``us-central1``).

        Returns:
            A list of APIGateway instances.
        """
        logger.info(
            "Listing API Gateways in %s for project %s",
            location,
            self.project_id,
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        request = self.service.projects().locations().gateways().list(
            parent=parent
        )

        gateways = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("gateways", []):
                gateways.append(APIGateway.from_api_response(item))
            request = (
                self.service.projects()
                .locations()
                .gateways()
                .list_next(request, response)
            )

        logger.info("Found %s API Gateways", len(gateways))
        return gateways

    def get_gateway(self, location: str, gateway_id: str) -> APIGateway:
        """Get a specific API Gateway.

        Args:
            location: The GCP location.
            gateway_id: The ID of the gateway.

        Returns:
            An APIGateway instance.

        Raises:
            ResourceNotFoundError: If the gateway does not exist.
            APIError: If the API call fails.
        """
        logger.info("Getting API Gateway %s in %s", gateway_id, location)

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/gateways/{gateway_id}"
        )

        request = (
            self.service.projects().locations().gateways().get(name=name)
        )
        response = self._execute(request, "APIGateway", gateway_id)
        return APIGateway.from_api_response(response)
    def create_gateway(
        self,
        location: str,
        gateway_id: str,
        api_config: str,
        display_name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> APIGateway:
        """Create a new API Gateway.

        Args:
            location: The GCP location.
            gateway_id: The ID for the new gateway.
            api_config: The full resource name of the API config to use.
            display_name: Optional display name for the gateway.
            labels: Optional labels to apply to the gateway.

        Returns:
            An APIGateway instance for the newly created gateway.

        Raises:
            ResourceAlreadyExistsError: If the gateway already exists.
            APIError: If the API call fails.
        """
        logger.info(
            "Creating API Gateway %s in %s", gateway_id, location
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        body: Dict[str, Any] = {
            "apiConfig": api_config,
        }

        if display_name:
            body["displayName"] = display_name
        if labels:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .gateways()
            .create(parent=parent, gatewayId=gateway_id, body=body)
        )
        response = self._execute(request)
        logger.info("Created API Gateway %s", gateway_id)
        return APIGateway.from_api_response(response)
    def update_gateway(
        self,
        location: str,
        gateway_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> APIGateway:
        """Update an existing API Gateway.

        Args:
            location: The GCP location.
            gateway_id: The ID of the gateway to update.
            update_mask: Comma-separated list of fields to update
                (e.g. ``"displayName,labels"``).
            update_fields: A dictionary of fields and values to update.

        Returns:
            An APIGateway instance for the updated gateway.

        Raises:
            ResourceNotFoundError: If the gateway does not exist.
            APIError: If the API call fails.
        """
        logger.info("Updating API Gateway %s in %s", gateway_id, location)

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/gateways/{gateway_id}"
        )

        request = (
            self.service.projects()
            .locations()
            .gateways()
            .patch(name=name, updateMask=update_mask, body=update_fields)
        )
        response = self._execute(request, "APIGateway", gateway_id)
        logger.info("Updated API Gateway %s", gateway_id)
        return APIGateway.from_api_response(response)
    def delete_gateway(self, location: str, gateway_id: str) -> bool:
        """Delete an API Gateway.

        Args:
            location: The GCP location.
            gateway_id: The ID of the gateway to delete.

        Returns:
            True if the deletion was successful.

        Raises:
            ResourceNotFoundError: If the gateway does not exist.
            APIError: If the API call fails.
        """
        logger.info("Deleting API Gateway %s in %s", gateway_id, location)

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/gateways/{gateway_id}"
        )

        self.service.projects().locations().gateways().delete(
            name=name
        ).execute()
        logger.info("Deleted API Gateway %s", gateway_id)
        return True
    def list_apis(self, location: Optional[str] = None) -> List[APIGateway]:
        """List APIs in the project.

        Args:
            location: Optional GCP location filter. If ``None``, uses the
                global location (``-``).

        Returns:
            A list of APIGateway instances representing APIs.
        """
        loc = location or "global"
        logger.info(
            "Listing APIs in %s for project %s", loc, self.project_id
        )

        parent = f"projects/{self.project_id}/locations/{loc}"
        request = self.service.projects().locations().apis().list(
            parent=parent
        )

        apis = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("apis", []):
                apis.append(APIGateway.from_api_response(item))
            request = (
                self.service.projects()
                .locations()
                .apis()
                .list_next(request, response)
            )

        logger.info("Found %s APIs", len(apis))
        return apis

    def get_api(self, api_id: str) -> APIGateway:
        """Get a specific API.

        Args:
            api_id: The ID of the API.

        Returns:
            An APIGateway instance representing the API.

        Raises:
            ResourceNotFoundError: If the API does not exist.
            APIError: If the API call fails.
        """
        logger.info("Getting API %s", api_id)

        name = f"projects/{self.project_id}/locations/global/apis/{api_id}"

        request = (
            self.service.projects().locations().apis().get(name=name)
        )
        response = self._execute(request, "API", api_id)
        return APIGateway.from_api_response(response)
    def create_api(
        self,
        api_id: str,
        display_name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> APIGateway:
        """Create a new API.

        Args:
            api_id: The ID for the new API.
            display_name: Optional display name for the API.
            labels: Optional labels to apply to the API.

        Returns:
            An APIGateway instance for the newly created API.

        Raises:
            ResourceAlreadyExistsError: If the API already exists.
            APIError: If the API call fails.
        """
        logger.info("Creating API %s", api_id)

        parent = f"projects/{self.project_id}/locations/global"
        body: Dict[str, Any] = {}

        if display_name:
            body["displayName"] = display_name
        if labels:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .apis()
            .create(parent=parent, apiId=api_id, body=body)
        )
        response = self._execute(request)
        logger.info("Created API %s", api_id)
        return APIGateway.from_api_response(response)
    def delete_api(self, api_id: str) -> bool:
        """Delete an API.

        Args:
            api_id: The ID of the API to delete.

        Returns:
            True if the deletion was successful.

        Raises:
            ResourceNotFoundError: If the API does not exist.
            APIError: If the API call fails.
        """
        logger.info("Deleting API %s", api_id)

        name = f"projects/{self.project_id}/locations/global/apis/{api_id}"

        self.service.projects().locations().apis().delete(
            name=name
        ).execute()
        logger.info("Deleted API %s", api_id)
        return True
    def list_api_configs(self, api_id: str) -> List[APIConfig]:
        """List API configs for an API.

        Args:
            api_id: The ID of the API.

        Returns:
            A list of APIConfig instances.
        """
        logger.info("Listing API configs for API %s", api_id)

        parent = (
            f"projects/{self.project_id}/locations/global/apis/{api_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .apis()
            .configs()
            .list(parent=parent)
        )

        configs = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("apiConfigs", []):
                configs.append(APIConfig.from_api_response(item))
            request = (
                self.service.projects()
                .locations()
                .apis()
                .configs()
                .list_next(request, response)
            )

        logger.info("Found %s API configs for API %s", len(configs), api_id)
        return configs

    def get_api_config(self, api_id: str, config_id: str) -> APIConfig:
        """Get a specific API config.

        Args:
            api_id: The ID of the API.
            config_id: The ID of the API config.

        Returns:
            An APIConfig instance.

        Raises:
            ResourceNotFoundError: If the API config does not exist.
            APIError: If the API call fails.
        """
        logger.info("Getting API config %s for API %s", config_id, api_id)

        name = (
            f"projects/{self.project_id}/locations/global"
            f"/apis/{api_id}/configs/{config_id}"
        )

        request = (
            self.service.projects()
            .locations()
            .apis()
            .configs()
            .get(name=name)
        )
        response = self._execute(request, "APIConfig", config_id)
        return APIConfig.from_api_response(response)
    def create_api_config(
        self,
        api_id: str,
        config_id: str,
        openapi_documents: Optional[List[Dict]] = None,
        grpc_services: Optional[List[Dict]] = None,
        display_name: Optional[str] = None,
    ) -> APIConfig:
        """Create a new API config.

        Args:
            api_id: The ID of the API.
            config_id: The ID for the new API config.
            openapi_documents: Optional list of OpenAPI specification
                documents.
            grpc_services: Optional list of gRPC service definitions.
            display_name: Optional display name for the API config.

        Returns:
            An APIConfig instance for the newly created config.

        Raises:
            ResourceAlreadyExistsError: If the config already exists.
            APIError: If the API call fails.
        """
        logger.info(
            "Creating API config %s for API %s", config_id, api_id
        )

        parent = (
            f"projects/{self.project_id}/locations/global/apis/{api_id}"
        )
        body: Dict[str, Any] = {}

        if openapi_documents:
            body["openapiDocuments"] = openapi_documents
        if grpc_services:
            body["grpcServices"] = grpc_services
        if display_name:
            body["displayName"] = display_name

        request = (
            self.service.projects()
            .locations()
            .apis()
            .configs()
            .create(
                parent=parent, apiConfigId=config_id, body=body
            )
        )
        response = self._execute(request)
        logger.info("Created API config %s for API %s", config_id, api_id)
        return APIConfig.from_api_response(response)
    def delete_api_config(self, api_id: str, config_id: str) -> bool:
        """Delete an API config.

        Args:
            api_id: The ID of the API.
            config_id: The ID of the API config to delete.

        Returns:
            True if the deletion was successful.

        Raises:
            ResourceNotFoundError: If the API config does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Deleting API config %s for API %s", config_id, api_id
        )

        name = (
            f"projects/{self.project_id}/locations/global"
            f"/apis/{api_id}/configs/{config_id}"
        )

        self.service.projects().locations().apis().configs().delete(
            name=name
        ).execute()
        logger.info("Deleted API config %s for API %s", config_id, api_id)
        return True