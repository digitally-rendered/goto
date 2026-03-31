"""Service implementation for Google Cloud Endpoints (Service Management)."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.endpoints import ManagedService, ServiceConfig
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class EndpointsService(GCPService[ManagedService]):
    """Service for interacting with Google Cloud Endpoints (Service Management)."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Endpoints service.

        Args:
            project_id: The GCP project ID to use for API calls.
            credentials_file: Optional path to a service account credentials
                file.
            **kwargs: Additional arguments to pass to the service constructor.
        """
        super().__init__(
            project_id=project_id,
            service_name="servicemanagement",
            version="v1",
            credentials_file=credentials_file,
            resource_model=ManagedService,
            **kwargs,
        )

    # ------------------------------------------------------------------ #
    #  Managed Service operations
    # ------------------------------------------------------------------ #

    def list_services(self) -> List[ManagedService]:
        """List managed services for the project.

        Returns:
            A list of ManagedService instances.
        """
        logger.info(
            "Listing managed services for project %s", self.project_id
        )

        request = self.service.services().list(
            producerProjectId=self.project_id
        )

        services = []
        while request is not None:
            response = request.execute()
            for item in response.get("services", []):
                services.append(ManagedService.from_api_response(item))
            request = self.service.services().list_next(request, response)

        logger.info("Found %s managed services", len(services))
        return services

    def get_service(self, service_name: str) -> ManagedService:
        """Get a specific managed service.

        Args:
            service_name: The name of the managed service.

        Returns:
            A ManagedService instance.

        Raises:
            ResourceNotFoundError: If the service does not exist.
            APIError: If the API call fails.
        """
        logger.info("Getting managed service %s", service_name)

        try:
            request = self.service.services().get(
                serviceName=service_name
            )
            response = request.execute()
            return ManagedService.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ManagedService", service_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_service(
        self,
        service_name: str,
        producer_project_id: Optional[str] = None,
    ) -> ManagedService:
        """Create a new managed service.

        Args:
            service_name: The name of the managed service to create.
            producer_project_id: Optional producer project ID. Defaults to
                the project ID of this service instance.

        Returns:
            A ManagedService instance for the newly created service.

        Raises:
            ResourceAlreadyExistsError: If the service already exists.
            APIError: If the API call fails.
        """
        logger.info("Creating managed service %s", service_name)

        body: Dict[str, Any] = {
            "serviceName": service_name,
            "producerProjectId": producer_project_id or self.project_id,
        }

        try:
            request = self.service.services().create(body=body)
            response = request.execute()
            logger.info("Created managed service %s", service_name)
            return ManagedService.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"ManagedService '{service_name}' already exists"
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def delete_service(self, service_name: str) -> bool:
        """Delete a managed service.

        Args:
            service_name: The name of the managed service to delete.

        Returns:
            True if the deletion was successful.

        Raises:
            ResourceNotFoundError: If the service does not exist.
            APIError: If the API call fails.
        """
        logger.info("Deleting managed service %s", service_name)

        try:
            self.service.services().delete(
                serviceName=service_name
            ).execute()
            logger.info("Deleted managed service %s", service_name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ManagedService", service_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    # ------------------------------------------------------------------ #
    #  Service Config operations
    # ------------------------------------------------------------------ #

    def list_service_configs(
        self, service_name: str
    ) -> List[ServiceConfig]:
        """List service configs for a managed service.

        Args:
            service_name: The name of the managed service.

        Returns:
            A list of ServiceConfig instances.
        """
        logger.info(
            "Listing service configs for service %s", service_name
        )

        request = self.service.services().configs().list(
            serviceName=service_name
        )

        configs = []
        while request is not None:
            response = request.execute()
            for item in response.get("serviceConfigs", []):
                configs.append(ServiceConfig.from_api_response(item))
            request = (
                self.service.services()
                .configs()
                .list_next(request, response)
            )

        logger.info(
            "Found %s service configs for %s", len(configs), service_name
        )
        return configs

    def get_service_config(
        self, service_name: str, config_id: str
    ) -> ServiceConfig:
        """Get a specific service config.

        Args:
            service_name: The name of the managed service.
            config_id: The ID of the service config.

        Returns:
            A ServiceConfig instance.

        Raises:
            ResourceNotFoundError: If the service config does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Getting service config %s for service %s",
            config_id,
            service_name,
        )

        try:
            request = self.service.services().configs().get(
                serviceName=service_name, configId=config_id
            )
            response = request.execute()
            return ServiceConfig.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ServiceConfig", config_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def submit_config_source(
        self, service_name: str, config_source: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit a service config source for validation and creation.

        Args:
            service_name: The name of the managed service.
            config_source: The config source to submit.

        Returns:
            The operation response dictionary.

        Raises:
            ResourceNotFoundError: If the service does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Submitting config source for service %s", service_name
        )

        body: Dict[str, Any] = {
            "configSource": config_source,
        }

        try:
            request = self.service.services().configs().submit(
                serviceName=service_name, body=body
            )
            response = request.execute()
            logger.info(
                "Submitted config source for service %s", service_name
            )
            return response
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ManagedService", service_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    # ------------------------------------------------------------------ #
    #  Service Rollout operations
    # ------------------------------------------------------------------ #

    def list_service_rollouts(
        self, service_name: str
    ) -> List[Dict[str, Any]]:
        """List service rollouts for a managed service.

        Args:
            service_name: The name of the managed service.

        Returns:
            A list of rollout response dictionaries.
        """
        logger.info(
            "Listing service rollouts for service %s", service_name
        )

        request = self.service.services().rollouts().list(
            serviceName=service_name
        )

        rollouts = []
        while request is not None:
            response = request.execute()
            for item in response.get("rollouts", []):
                rollouts.append(item)
            request = (
                self.service.services()
                .rollouts()
                .list_next(request, response)
            )

        logger.info(
            "Found %s rollouts for %s", len(rollouts), service_name
        )
        return rollouts

    def create_service_rollout(
        self, service_name: str, rollout_body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new service rollout.

        Args:
            service_name: The name of the managed service.
            rollout_body: The rollout configuration body.

        Returns:
            The operation response dictionary.

        Raises:
            ResourceNotFoundError: If the service does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Creating service rollout for service %s", service_name
        )

        try:
            request = self.service.services().rollouts().create(
                serviceName=service_name, body=rollout_body
            )
            response = request.execute()
            logger.info(
                "Created service rollout for service %s", service_name
            )
            return response
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ManagedService", service_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))
