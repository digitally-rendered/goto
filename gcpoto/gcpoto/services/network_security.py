"""Service implementation for Google Cloud Network Security."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.network_security import ServerTLSPolicy, AuthorizationPolicy
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class NetworkSecurityService(GCPService[ServerTLSPolicy]):
    """Service for interacting with Google Cloud Network Security."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Network Security service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="networksecurity",
            version="v1",
            credentials_file=credentials_file,
            resource_model=ServerTLSPolicy,
            **kwargs,
        )

    def list_server_tls_policies(
        self, location: str
    ) -> List[ServerTLSPolicy]:
        """List Server TLS Policies in a location.

        Args:
            location: The location to list policies in

        Returns:
            A list of ServerTLSPolicy instances
        """
        logger.info(
            "Listing server TLS policies in location %s for project %s",
            location,
            self.project_id,
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        request = self.service.projects().locations().serverTlsPolicies().list(
            parent=parent
        )

        policies = []
        while request is not None:
            response = request.execute()
            for policy_data in response.get("serverTlsPolicies", []):
                policies.append(
                    ServerTLSPolicy.from_api_response(policy_data)
                )
            request = (
                self.service.projects()
                .locations()
                .serverTlsPolicies()
                .list_next(request, response)
            )

        logger.info("Found %s server TLS policies", len(policies))
        return policies

    def get_server_tls_policy(
        self, location: str, policy_name: str
    ) -> ServerTLSPolicy:
        """Get a specific Server TLS Policy.

        Args:
            location: The location of the policy
            policy_name: The name of the policy

        Returns:
            A ServerTLSPolicy instance

        Raises:
            ResourceNotFoundError: If the policy does not exist
        """
        logger.info(
            "Getting server TLS policy %s in location %s",
            policy_name,
            location,
        )

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/serverTlsPolicies/{policy_name}"
        )

        try:
            request = (
                self.service.projects()
                .locations()
                .serverTlsPolicies()
                .get(name=name)
            )
            response = request.execute()
            return ServerTLSPolicy.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "ServerTLSPolicy", policy_name
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_server_tls_policy(
        self,
        location: str,
        policy_name: str,
        allow_open: bool = False,
        server_certificate: Optional[Dict[str, Any]] = None,
        mtls_policy: Optional[Dict[str, Any]] = None,
    ) -> ServerTLSPolicy:
        """Create a Server TLS Policy.

        Args:
            location: The location to create the policy in
            policy_name: The name for the policy
            allow_open: Whether to allow open connections
            server_certificate: Optional server certificate configuration
            mtls_policy: Optional mutual TLS policy configuration

        Returns:
            The created ServerTLSPolicy instance

        Raises:
            APIError: If the API call fails
        """
        logger.info(
            "Creating server TLS policy %s in location %s",
            policy_name,
            location,
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        body = {
            "name": policy_name,
            "allowOpen": allow_open,
        }
        if server_certificate:
            body["serverCertificate"] = server_certificate
        if mtls_policy:
            body["mtlsPolicy"] = mtls_policy

        try:
            request = (
                self.service.projects()
                .locations()
                .serverTlsPolicies()
                .create(
                    parent=parent,
                    serverTlsPolicyId=policy_name,
                    body=body,
                )
            )
            response = request.execute()
            logger.info("Created server TLS policy %s", policy_name)
            return ServerTLSPolicy.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def delete_server_tls_policy(
        self, location: str, policy_name: str
    ) -> bool:
        """Delete a Server TLS Policy.

        Args:
            location: The location of the policy
            policy_name: The name of the policy to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the policy does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Deleting server TLS policy %s in location %s",
            policy_name,
            location,
        )

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/serverTlsPolicies/{policy_name}"
        )

        try:
            self.service.projects().locations().serverTlsPolicies().delete(
                name=name
            ).execute()
            logger.info("Deleted server TLS policy %s", policy_name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "ServerTLSPolicy", policy_name
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def list_authorization_policies(
        self, location: str
    ) -> List[AuthorizationPolicy]:
        """List Authorization Policies in a location.

        Args:
            location: The location to list policies in

        Returns:
            A list of AuthorizationPolicy instances
        """
        logger.info(
            "Listing authorization policies in location %s for project %s",
            location,
            self.project_id,
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        request = (
            self.service.projects()
            .locations()
            .authorizationPolicies()
            .list(parent=parent)
        )

        policies = []
        while request is not None:
            response = request.execute()
            for policy_data in response.get("authorizationPolicies", []):
                policies.append(
                    AuthorizationPolicy.from_api_response(policy_data)
                )
            request = (
                self.service.projects()
                .locations()
                .authorizationPolicies()
                .list_next(request, response)
            )

        logger.info("Found %s authorization policies", len(policies))
        return policies

    def get_authorization_policy(
        self, location: str, policy_name: str
    ) -> AuthorizationPolicy:
        """Get a specific Authorization Policy.

        Args:
            location: The location of the policy
            policy_name: The name of the policy

        Returns:
            An AuthorizationPolicy instance

        Raises:
            ResourceNotFoundError: If the policy does not exist
        """
        logger.info(
            "Getting authorization policy %s in location %s",
            policy_name,
            location,
        )

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/authorizationPolicies/{policy_name}"
        )

        try:
            request = (
                self.service.projects()
                .locations()
                .authorizationPolicies()
                .get(name=name)
            )
            response = request.execute()
            return AuthorizationPolicy.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "AuthorizationPolicy", policy_name
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_authorization_policy(
        self,
        location: str,
        policy_name: str,
        action: str,
        rules: Optional[List[Dict[str, Any]]] = None,
    ) -> AuthorizationPolicy:
        """Create an Authorization Policy.

        Args:
            location: The location to create the policy in
            policy_name: The name for the policy
            action: The action to take (ALLOW or DENY)
            rules: Optional list of authorization rules

        Returns:
            The created AuthorizationPolicy instance

        Raises:
            APIError: If the API call fails
        """
        logger.info(
            "Creating authorization policy %s in location %s",
            policy_name,
            location,
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        body = {
            "name": policy_name,
            "action": action,
        }
        if rules:
            body["rules"] = rules

        try:
            request = (
                self.service.projects()
                .locations()
                .authorizationPolicies()
                .create(
                    parent=parent,
                    authorizationPolicyId=policy_name,
                    body=body,
                )
            )
            response = request.execute()
            logger.info("Created authorization policy %s", policy_name)
            return AuthorizationPolicy.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def delete_authorization_policy(
        self, location: str, policy_name: str
    ) -> bool:
        """Delete an Authorization Policy.

        Args:
            location: The location of the policy
            policy_name: The name of the policy to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the policy does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Deleting authorization policy %s in location %s",
            policy_name,
            location,
        )

        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/authorizationPolicies/{policy_name}"
        )

        try:
            self.service.projects().locations().authorizationPolicies().delete(
                name=name
            ).execute()
            logger.info("Deleted authorization policy %s", policy_name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "AuthorizationPolicy", policy_name
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))
