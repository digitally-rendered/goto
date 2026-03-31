"""Service implementation for Google Cloud Apigee."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.apigee import (
    ApigeeOrganization,
    ApigeeEnvironment,
    ApigeeAPIProxy,
)
from gcpoto.exceptions import (
    APIError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


class ApigeeService(GCPService[ApigeeOrganization]):
    """Service for interacting with Google Cloud Apigee."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Apigee service.

        Args:
            project_id: The GCP project ID to use for API calls.
            credentials_file: Optional path to a service account credentials
                file.
            **kwargs: Additional arguments to pass to the service constructor.
        """
        super().__init__(
            project_id=project_id,
            service_name="apigee",
            version="v1",
            credentials_file=credentials_file,
            resource_model=ApigeeOrganization,
            **kwargs,
        )

    # ------------------------------------------------------------------ #
    #  Organization operations
    # ------------------------------------------------------------------ #

    def get_organization(self, org_name: str) -> ApigeeOrganization:
        """Get a specific Apigee organization.

        Args:
            org_name: The name of the organization.

        Returns:
            An ApigeeOrganization instance.

        Raises:
            ResourceNotFoundError: If the organization does not exist.
            APIError: If the API call fails.
        """
        logger.info("Getting Apigee organization %s", org_name)

        name = f"organizations/{org_name}"

        request = self.service.organizations().get(name=name)
        response = self._execute(request, "ApigeeOrganization", org_name)
        return ApigeeOrganization.from_api_response(response)
    def list_environments(self, org_name: str) -> List[ApigeeEnvironment]:
        """List environments in an Apigee organization.

        Args:
            org_name: The name of the organization.

        Returns:
            A list of ApigeeEnvironment instances.
        """
        logger.info(
            "Listing environments for Apigee organization %s", org_name
        )

        parent = f"organizations/{org_name}"
        request = self.service.organizations().environments().list(
            parent=parent
        )
        response = self._execute(request)

        environments = []
        for env_name in response:
            env = self.get_environment(org_name, env_name)
            environments.append(env)

        logger.info("Found %s environments", len(environments))
        return environments

    def get_environment(
        self, org_name: str, env_name: str
    ) -> ApigeeEnvironment:
        """Get a specific Apigee environment.

        Args:
            org_name: The name of the organization.
            env_name: The name of the environment.

        Returns:
            An ApigeeEnvironment instance.

        Raises:
            ResourceNotFoundError: If the environment does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Getting Apigee environment %s in organization %s",
            env_name,
            org_name,
        )

        name = f"organizations/{org_name}/environments/{env_name}"

        request = self.service.organizations().environments().get(
            name=name
        )
        response = self._execute(request, "ApigeeEnvironment", env_name)
        return ApigeeEnvironment.from_api_response(response)
    def create_environment(
        self,
        org_name: str,
        env_name: str,
        description: Optional[str] = None,
    ) -> ApigeeEnvironment:
        """Create a new Apigee environment.

        Args:
            org_name: The name of the organization.
            env_name: The name for the new environment.
            description: Optional description for the environment.

        Returns:
            An ApigeeEnvironment instance for the newly created environment.

        Raises:
            ResourceAlreadyExistsError: If the environment already exists.
            APIError: If the API call fails.
        """
        logger.info(
            "Creating Apigee environment %s in organization %s",
            env_name,
            org_name,
        )

        parent = f"organizations/{org_name}"
        body: Dict[str, Any] = {"name": env_name}

        if description:
            body["description"] = description

        request = (
            self.service.organizations()
            .environments()
            .create(parent=parent, body=body)
        )
        response = self._execute(request)
        logger.info("Created Apigee environment %s", env_name)
        return ApigeeEnvironment.from_api_response(response)
    def delete_environment(self, org_name: str, env_name: str) -> bool:
        """Delete an Apigee environment.

        Args:
            org_name: The name of the organization.
            env_name: The name of the environment to delete.

        Returns:
            True if the deletion was successful.

        Raises:
            ResourceNotFoundError: If the environment does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Deleting Apigee environment %s in organization %s",
            env_name,
            org_name,
        )

        name = f"organizations/{org_name}/environments/{env_name}"

        self.service.organizations().environments().delete(
            name=name
        ).execute()
        logger.info("Deleted Apigee environment %s", env_name)
        return True
    def list_api_proxies(self, org_name: str) -> List[ApigeeAPIProxy]:
        """List API proxies in an Apigee organization.

        Args:
            org_name: The name of the organization.

        Returns:
            A list of ApigeeAPIProxy instances.
        """
        logger.info(
            "Listing API proxies for Apigee organization %s", org_name
        )

        parent = f"organizations/{org_name}"
        request = self.service.organizations().apis().list(parent=parent)
        response = self._execute(request)

        proxies = []
        for item in response.get("proxies", []):
            proxies.append(ApigeeAPIProxy.from_api_response(item))

        logger.info("Found %s API proxies", len(proxies))
        return proxies

    def get_api_proxy(
        self, org_name: str, proxy_name: str
    ) -> ApigeeAPIProxy:
        """Get a specific Apigee API proxy.

        Args:
            org_name: The name of the organization.
            proxy_name: The name of the API proxy.

        Returns:
            An ApigeeAPIProxy instance.

        Raises:
            ResourceNotFoundError: If the API proxy does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Getting Apigee API proxy %s in organization %s",
            proxy_name,
            org_name,
        )

        name = f"organizations/{org_name}/apis/{proxy_name}"

        request = self.service.organizations().apis().get(name=name)
        response = self._execute(request, "ApigeeAPIProxy", proxy_name)
        return ApigeeAPIProxy.from_api_response(response)
    def create_api_proxy(
        self,
        org_name: str,
        proxy_name: str,
        proxy_bundle: bytes,
    ) -> ApigeeAPIProxy:
        """Create a new Apigee API proxy.

        Args:
            org_name: The name of the organization.
            proxy_name: The name for the new API proxy.
            proxy_bundle: The API proxy bundle as bytes.

        Returns:
            An ApigeeAPIProxy instance for the newly created proxy.

        Raises:
            ResourceAlreadyExistsError: If the API proxy already exists.
            APIError: If the API call fails.
        """
        logger.info(
            "Creating Apigee API proxy %s in organization %s",
            proxy_name,
            org_name,
        )

        parent = f"organizations/{org_name}"
        body: Dict[str, Any] = {
            "name": proxy_name,
            "content": proxy_bundle,
        }

        request = (
            self.service.organizations()
            .apis()
            .create(parent=parent, name=proxy_name, body=body)
        )
        response = self._execute(request)
        logger.info("Created Apigee API proxy %s", proxy_name)
        return ApigeeAPIProxy.from_api_response(response)
    def delete_api_proxy(self, org_name: str, proxy_name: str) -> bool:
        """Delete an Apigee API proxy.

        Args:
            org_name: The name of the organization.
            proxy_name: The name of the API proxy to delete.

        Returns:
            True if the deletion was successful.

        Raises:
            ResourceNotFoundError: If the API proxy does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Deleting Apigee API proxy %s in organization %s",
            proxy_name,
            org_name,
        )

        name = f"organizations/{org_name}/apis/{proxy_name}"

        self.service.organizations().apis().delete(
            name=name
        ).execute()
        logger.info("Deleted Apigee API proxy %s", proxy_name)
        return True
    def deploy_api_proxy(
        self,
        org_name: str,
        env_name: str,
        proxy_name: str,
        revision: str,
    ) -> Dict[str, Any]:
        """Deploy an API proxy revision to an environment.

        Args:
            org_name: The name of the organization.
            env_name: The name of the environment.
            proxy_name: The name of the API proxy.
            revision: The revision number to deploy.

        Returns:
            The deployment response dictionary.

        Raises:
            ResourceNotFoundError: If the proxy or environment does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Deploying Apigee API proxy %s revision %s to environment %s",
            proxy_name,
            revision,
            env_name,
        )

        name = (
            f"organizations/{org_name}/environments/{env_name}"
            f"/apis/{proxy_name}/revisions/{revision}"
        )

        request = (
            self.service.organizations()
            .environments()
            .apis()
            .revisions()
            .deploy(name=name)
        )
        response = self._execute(request, "ApigeeAPIProxy", proxy_name)
        logger.info(
            "Deployed API proxy %s revision %s to %s",
            proxy_name,
            revision,
            env_name,
        )
        return response
    def undeploy_api_proxy(
        self,
        org_name: str,
        env_name: str,
        proxy_name: str,
        revision: str,
    ) -> Dict[str, Any]:
        """Undeploy an API proxy revision from an environment.

        Args:
            org_name: The name of the organization.
            env_name: The name of the environment.
            proxy_name: The name of the API proxy.
            revision: The revision number to undeploy.

        Returns:
            The undeployment response dictionary.

        Raises:
            ResourceNotFoundError: If the deployment does not exist.
            APIError: If the API call fails.
        """
        logger.info(
            "Undeploying Apigee API proxy %s revision %s from environment %s",
            proxy_name,
            revision,
            env_name,
        )

        name = (
            f"organizations/{org_name}/environments/{env_name}"
            f"/apis/{proxy_name}/revisions/{revision}"
        )

        request = (
            self.service.organizations()
            .environments()
            .apis()
            .revisions()
            .undeploy(name=name)
        )
        response = self._execute(request, "ApigeeAPIProxy", proxy_name)
        logger.info(
            "Undeployed API proxy %s revision %s from %s",
            proxy_name,
            revision,
            env_name,
        )
        return response