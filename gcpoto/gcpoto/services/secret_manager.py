"""Service implementation for Google Cloud Secret Manager."""

import base64
import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.secret_manager import Secret, SecretVersion

from gcpoto.utils import format_secret_path, format_secret_version_path

logger = logging.getLogger(__name__)

class SecretManagerService(GCPService[Secret]):
    """Service for interacting with Google Cloud Secret Manager."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Secret Manager service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="secretmanager",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Secret,
            **kwargs,
        )

    def list_secrets(self, **kwargs) -> List[Secret]:
        """List secrets in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of Secret instances
        """
        parent = f"projects/{self.project_id}"
        request = self.service.projects().secrets().list(
            parent=parent, **kwargs
        )

        secrets = []
        while request is not None:
            response = self._execute(request)
            for secret_data in response.get("secrets", []):
                secrets.append(
                    Secret.from_api_response(secret_data, self.project_id)
                )
            request = (
                self.service.projects().secrets().list_next(request, response)
            )

        return secrets

    def get_secret(self, secret_id: str) -> Secret:
        """Get a specific secret by ID.

        Args:
            secret_id: The secret ID or full resource name

        Returns:
            A Secret instance
        """
        name = format_secret_path(self.project_id, secret_id)
        request = self.service.projects().secrets().get(name=name)
        response = self._execute(request)
        return Secret.from_api_response(response, self.project_id)

    def create_secret(
        self,
        secret_id: str,
        replication: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Secret:
        """Create a new secret.

        Args:
            secret_id: The ID for the new secret
            replication: Optional replication policy; defaults to automatic
            labels: Optional labels to apply to the secret

        Returns:
            The created Secret instance
        """
        parent = f"projects/{self.project_id}"

        body: Dict[str, Any] = {
            "replication": replication or {"automatic": {}},
        }

        if labels:
            body["labels"] = labels

        request = (
            self.service.projects()
            .secrets()
            .create(parent=parent, secretId=secret_id, body=body)
        )
        response = self._execute(request)
        return Secret.from_api_response(response, self.project_id)
    def delete_secret(self, secret_id: str) -> bool:
        """Delete a secret.

        Args:
            secret_id: The secret ID or full resource name

        Returns:
            True if the deletion was successful
        """
        name = format_secret_path(self.project_id, secret_id)
        request = self.service.projects().secrets().delete(name=name)
        self._execute(request)
        return True

    def update_secret(
        self,
        secret_id: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> Secret:
        """Update a secret's metadata.

        Args:
            secret_id: The secret ID or full resource name
            labels: Optional labels to set on the secret

        Returns:
            The updated Secret instance
        """
        name = format_secret_path(self.project_id, secret_id)

        body: Dict[str, Any] = {"name": name}
        update_mask_fields = []

        if labels is not None:
            body["labels"] = labels
            update_mask_fields.append("labels")

        update_mask = ",".join(update_mask_fields)

        request = (
            self.service.projects()
            .secrets()
            .patch(name=name, body=body, updateMask=update_mask)
        )
        response = self._execute(request)
        return Secret.from_api_response(response, self.project_id)

    def add_secret_version(
        self, secret_id: str, payload: bytes
    ) -> SecretVersion:
        """Add a new version to a secret with the given payload.

        Args:
            secret_id: The secret ID or full resource name
            payload: The secret payload bytes

        Returns:
            The created SecretVersion instance
        """
        parent = format_secret_path(self.project_id, secret_id)
        encoded_payload = base64.b64encode(payload).decode("utf-8")

        body = {"payload": {"data": encoded_payload}}

        request = (
            self.service.projects()
            .secrets()
            .addVersion(parent=parent, body=body)
        )
        response = self._execute(request)
        return SecretVersion.from_api_response(response, self.project_id)

    def access_secret_version(
        self, secret_id: str, version_id: str = "latest"
    ) -> bytes:
        """Access the payload of a secret version.

        Args:
            secret_id: The secret ID or full resource name
            version_id: The version to access (default: "latest")

        Returns:
            The secret payload as bytes
        """
        name = format_secret_version_path(
            self.project_id, secret_id, version_id
        )

        request = (
            self.service.projects().secrets().versions().access(name=name)
        )
        response = self._execute(request)

        encoded_data = response.get("payload", {}).get("data", "")
        return base64.b64decode(encoded_data)

    def list_secret_versions(
        self, secret_id: str, **kwargs
    ) -> List[SecretVersion]:
        """List versions of a secret.

        Args:
            secret_id: The secret ID or full resource name
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of SecretVersion instances
        """
        parent = format_secret_path(self.project_id, secret_id)

        request = (
            self.service.projects()
            .secrets()
            .versions()
            .list(parent=parent, **kwargs)
        )

        versions = []
        while request is not None:
            response = self._execute(request)
            for version_data in response.get("versions", []):
                versions.append(
                    SecretVersion.from_api_response(
                        version_data, self.project_id
                    )
                )
            request = (
                self.service.projects()
                .secrets()
                .versions()
                .list_next(request, response)
            )

        return versions

    def get_secret_version(
        self, secret_id: str, version_id: str
    ) -> SecretVersion:
        """Get a specific secret version.

        Args:
            secret_id: The secret ID or full resource name
            version_id: The version identifier

        Returns:
            A SecretVersion instance
        """
        name = format_secret_version_path(
            self.project_id, secret_id, version_id
        )

        request = (
            self.service.projects().secrets().versions().get(name=name)
        )
        response = self._execute(request)
        return SecretVersion.from_api_response(response, self.project_id)

    def disable_secret_version(
        self, secret_id: str, version_id: str
    ) -> SecretVersion:
        """Disable a secret version.

        Args:
            secret_id: The secret ID or full resource name
            version_id: The version identifier

        Returns:
            The updated SecretVersion instance
        """
        name = format_secret_version_path(
            self.project_id, secret_id, version_id
        )

        request = (
            self.service.projects()
            .secrets()
            .versions()
            .disable(name=name, body={})
        )
        response = self._execute(request)
        return SecretVersion.from_api_response(response, self.project_id)

    def enable_secret_version(
        self, secret_id: str, version_id: str
    ) -> SecretVersion:
        """Enable a secret version.

        Args:
            secret_id: The secret ID or full resource name
            version_id: The version identifier

        Returns:
            The updated SecretVersion instance
        """
        name = format_secret_version_path(
            self.project_id, secret_id, version_id
        )

        request = (
            self.service.projects()
            .secrets()
            .versions()
            .enable(name=name, body={})
        )
        response = self._execute(request)
        return SecretVersion.from_api_response(response, self.project_id)

    def destroy_secret_version(
        self, secret_id: str, version_id: str
    ) -> SecretVersion:
        """Destroy a secret version.

        Args:
            secret_id: The secret ID or full resource name
            version_id: The version identifier

        Returns:
            The updated SecretVersion instance
        """
        name = format_secret_version_path(
            self.project_id, secret_id, version_id
        )

        request = (
            self.service.projects()
            .secrets()
            .versions()
            .destroy(name=name, body={})
        )
        response = self._execute(request)
        return SecretVersion.from_api_response(response, self.project_id)
