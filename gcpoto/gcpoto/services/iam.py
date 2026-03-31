"""Service implementation for Google Cloud IAM."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.iam import ServiceAccount, ServiceAccountKey, Role
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


def format_service_account_path(project_id: str, email_or_uid: str) -> str:
    """Return full projects/{project}/serviceAccounts/{email} path.

    Args:
        project_id: The GCP project ID.
        email_or_uid: Either a service account email, unique ID,
            or a full resource path.

    Returns:
        The fully-qualified service account resource path.
    """
    if "/" not in email_or_uid:
        return f"projects/{project_id}/serviceAccounts/{email_or_uid}"
    return email_or_uid


class IAMService(GCPService[ServiceAccount]):
    """Service for interacting with Google Cloud IAM."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the IAM service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="iam",
            version="v1",
            credentials_file=credentials_file,
            resource_model=ServiceAccount,
            **kwargs,
        )

    # ── Service Account methods ──────────────────────────────────────

    def list_service_accounts(self, **kwargs) -> List[ServiceAccount]:
        """List service accounts in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of ServiceAccount instances
        """
        request = (
            self.service.projects()
            .serviceAccounts()
            .list(name=f"projects/{self.project_id}", **kwargs)
        )

        accounts = []
        while request is not None:
            response = request.execute()
            for account_data in response.get("accounts", []):
                accounts.append(ServiceAccount.from_api_response(account_data))

            request = (
                self.service.projects()
                .serviceAccounts()
                .list_next(request, response)
            )

        logger.info(
            "Listed %s service accounts in project %s",
            len(accounts),
            self.project_id,
        )
        return accounts

    def get_service_account(self, email_or_uid: str) -> ServiceAccount:
        """Get a specific service account by email or unique ID.

        Args:
            email_or_uid: The email address or unique ID of the service account

        Returns:
            A ServiceAccount instance

        Raises:
            ResourceNotFoundError: If the service account is not found
        """
        full_name = format_service_account_path(self.project_id, email_or_uid)

        try:
            request = (
                self.service.projects()
                .serviceAccounts()
                .get(name=full_name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "ServiceAccount", email_or_uid
                ) from e
            raise

        logger.info("Retrieved service account %s", email_or_uid)
        return ServiceAccount.from_api_response(response)

    def create_service_account(
        self,
        account_id: str,
        display_name: str = "",
        description: str = "",
    ) -> ServiceAccount:
        """Create a new service account.

        Args:
            account_id: The account ID for the new service account
                (used to form the email address)
            display_name: A user-specified display name
            description: A user-specified description

        Returns:
            The newly created ServiceAccount instance
        """
        body: Dict[str, Any] = {
            "accountId": account_id,
            "serviceAccount": {},
        }

        if display_name:
            body["serviceAccount"]["displayName"] = display_name
        if description:
            body["serviceAccount"]["description"] = description

        request = (
            self.service.projects()
            .serviceAccounts()
            .create(name=f"projects/{self.project_id}", body=body)
        )
        response = request.execute()

        logger.info(
            "Created service account %s in project %s",
            account_id,
            self.project_id,
        )
        return ServiceAccount.from_api_response(response)

    def update_service_account(
        self,
        email: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ServiceAccount:
        """Update an existing service account.

        Args:
            email: The email address of the service account to update
            display_name: Optional new display name
            description: Optional new description

        Returns:
            The updated ServiceAccount instance
        """
        full_name = format_service_account_path(self.project_id, email)

        body: Dict[str, Any] = {"name": full_name}
        if display_name is not None:
            body["displayName"] = display_name
        if description is not None:
            body["description"] = description

        request = (
            self.service.projects()
            .serviceAccounts()
            .update(name=full_name, body=body)
        )
        response = request.execute()

        logger.info("Updated service account %s", email)
        return ServiceAccount.from_api_response(response)

    def delete_service_account(self, email: str) -> bool:
        """Delete a service account.

        Args:
            email: The email address of the service account to delete

        Returns:
            True if the deletion was successful
        """
        full_name = format_service_account_path(self.project_id, email)

        request = (
            self.service.projects()
            .serviceAccounts()
            .delete(name=full_name)
        )
        request.execute()

        logger.info("Deleted service account %s", email)
        return True

    def enable_service_account(self, email: str) -> None:
        """Enable a service account.

        Args:
            email: The email address of the service account to enable
        """
        full_name = format_service_account_path(self.project_id, email)

        request = (
            self.service.projects()
            .serviceAccounts()
            .enable(name=full_name, body={})
        )
        request.execute()

        logger.info("Enabled service account %s", email)

    def disable_service_account(self, email: str) -> None:
        """Disable a service account.

        Args:
            email: The email address of the service account to disable
        """
        full_name = format_service_account_path(self.project_id, email)

        request = (
            self.service.projects()
            .serviceAccounts()
            .disable(name=full_name, body={})
        )
        request.execute()

        logger.info("Disabled service account %s", email)

    # ── Service Account Key methods ──────────────────────────────────

    def list_service_account_keys(
        self,
        email: str,
        key_types: Optional[List[str]] = None,
    ) -> List[ServiceAccountKey]:
        """List keys for a service account.

        Args:
            email: The email address of the service account
            key_types: Optional list of key types to filter by
                (e.g. ["USER_MANAGED", "SYSTEM_MANAGED"])

        Returns:
            A list of ServiceAccountKey instances
        """
        full_name = format_service_account_path(self.project_id, email)

        kwargs: Dict[str, Any] = {"name": full_name}
        if key_types:
            kwargs["keyTypes"] = key_types

        request = (
            self.service.projects()
            .serviceAccounts()
            .keys()
            .list(**kwargs)
        )
        response = request.execute()

        keys = [
            ServiceAccountKey.from_api_response(key_data)
            for key_data in response.get("keys", [])
        ]

        logger.info(
            "Listed %s keys for service account %s",
            len(keys),
            email,
        )
        return keys

    def create_service_account_key(
        self,
        email: str,
        key_algorithm: str = "KEY_ALG_RSA_2048",
    ) -> ServiceAccountKey:
        """Create a new key for a service account.

        Args:
            email: The email address of the service account
            key_algorithm: The algorithm for the key
                (default: KEY_ALG_RSA_2048)

        Returns:
            The newly created ServiceAccountKey instance
        """
        full_name = format_service_account_path(self.project_id, email)

        body = {"keyAlgorithm": key_algorithm}

        request = (
            self.service.projects()
            .serviceAccounts()
            .keys()
            .create(name=full_name, body=body)
        )
        response = request.execute()

        logger.info("Created key for service account %s", email)
        return ServiceAccountKey.from_api_response(response)

    def delete_service_account_key(
        self,
        email: str,
        key_id: str,
    ) -> bool:
        """Delete a key for a service account.

        Args:
            email: The email address of the service account
            key_id: The ID of the key to delete

        Returns:
            True if the deletion was successful
        """
        full_name = format_service_account_path(self.project_id, email)
        key_name = f"{full_name}/keys/{key_id}"

        request = (
            self.service.projects()
            .serviceAccounts()
            .keys()
            .delete(name=key_name)
        )
        request.execute()

        logger.info(
            "Deleted key %s for service account %s", key_id, email
        )
        return True

    # ── Role methods ─────────────────────────────────────────────────

    def list_roles(
        self,
        parent: Optional[str] = None,
        show_deleted: bool = False,
    ) -> List[Role]:
        """List IAM roles.

        Args:
            parent: Optional parent resource. If None, lists project roles.
                Use "projects/{project}" for project roles or omit for
                predefined roles.
            show_deleted: Whether to include deleted roles

        Returns:
            A list of Role instances
        """
        if parent is None:
            parent = f"projects/{self.project_id}"

        request = (
            self.service.projects()
            .roles()
            .list(parent=parent, showDeleted=show_deleted)
        )

        roles = []
        while request is not None:
            response = request.execute()
            for role_data in response.get("roles", []):
                roles.append(Role.from_api_response(role_data))

            request = (
                self.service.projects()
                .roles()
                .list_next(request, response)
            )

        logger.info("Listed %s roles for %s", len(roles), parent)
        return roles

    def get_role(self, role_name: str) -> Role:
        """Get a specific IAM role.

        Args:
            role_name: The full resource name of the role
                (e.g. "projects/{project}/roles/{role_id}"
                or "roles/{role_id}" for predefined roles)

        Returns:
            A Role instance

        Raises:
            ResourceNotFoundError: If the role is not found
        """
        try:
            request = (
                self.service.projects()
                .roles()
                .get(name=role_name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("Role", role_name) from e
            raise

        logger.info("Retrieved role %s", role_name)
        return Role.from_api_response(response)

    def create_role(
        self,
        role_id: str,
        title: str = "",
        permissions: Optional[List[str]] = None,
        description: str = "",
        stage: str = "GA",
    ) -> Role:
        """Create a new custom IAM role.

        Args:
            role_id: The role ID to use for the new role
            title: A human-readable title for the role
            permissions: The permissions to include in the role
            description: A description of the role
            stage: The launch stage (ALPHA, BETA, GA, DEPRECATED)

        Returns:
            The newly created Role instance
        """
        body: Dict[str, Any] = {
            "roleId": role_id,
            "role": {
                "title": title,
                "description": description,
                "includedPermissions": permissions or [],
                "stage": stage,
            },
        }

        request = (
            self.service.projects()
            .roles()
            .create(parent=f"projects/{self.project_id}", body=body)
        )
        response = request.execute()

        logger.info(
            "Created role %s in project %s", role_id, self.project_id
        )
        return Role.from_api_response(response)

    def update_role(
        self,
        role_name: str,
        title: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        description: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> Role:
        """Update an existing custom IAM role.

        Args:
            role_name: The full resource name of the role
            title: Optional new title
            permissions: Optional new list of permissions
            description: Optional new description
            stage: Optional new launch stage

        Returns:
            The updated Role instance
        """
        body: Dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if permissions is not None:
            body["includedPermissions"] = permissions
        if description is not None:
            body["description"] = description
        if stage is not None:
            body["stage"] = stage

        request = (
            self.service.projects()
            .roles()
            .patch(name=role_name, body=body)
        )
        response = request.execute()

        logger.info("Updated role %s", role_name)
        return Role.from_api_response(response)

    def delete_role(self, role_name: str) -> Role:
        """Delete a custom IAM role.

        Deleting a role sets the deleted field to True but does not
        immediately remove it.

        Args:
            role_name: The full resource name of the role

        Returns:
            The deleted Role instance (with deleted=True)
        """
        request = (
            self.service.projects()
            .roles()
            .delete(name=role_name)
        )
        response = request.execute()

        logger.info("Deleted role %s", role_name)
        return Role.from_api_response(response)
