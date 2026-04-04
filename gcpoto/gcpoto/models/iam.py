"""Models for Google Cloud IAM resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.iam import get_schema


class ServiceAccount(GCPResource):
    """Model for a Google Cloud IAM Service Account."""

    email: str = Field("", description="The email address of the service account")
    unique_id: str = Field(
        "", description="The unique numeric ID for the service account"
    )
    display_name: str = Field(
        "", description="A user-specified display name for the service account"
    )
    description: str = Field(
        "", description="A user-specified description of the service account"
    )
    disabled: bool = Field(
        False, description="Whether the service account is disabled"
    )
    oauth2_client_id: Optional[str] = Field(
        None, description="The OAuth 2.0 client ID for the service account"
    )
    _tags: Optional[Dict[str, str]] = None

    model_config = ConfigDict(
        json_schema_extra={"schema": get_schema("service_account")}
    )

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "ServiceAccount":
        """Create a ServiceAccount from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ServiceAccount instance
        """
        full_name = response.get("name", "")
        email = response.get("email", "")
        project_id = response.get("projectId", "")

        # Extract project from name if not provided
        if not project_id and full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        instance = cls(
            id=response.get("uniqueId", ""),
            name=full_name,
            type="iam.serviceAccount",
            project=project_id,
            email=email,
            unique_id=response.get("uniqueId", ""),
            display_name=response.get("displayName", ""),
            description=response.get("description", ""),
            disabled=response.get("disabled", False),
            oauth2_client_id=response.get("oauth2ClientId"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class ServiceAccountKey(GCPResource):
    """Model for a Google Cloud IAM Service Account Key."""

    service_account_email: str = Field(
        "", description="The email of the service account this key belongs to"
    )
    key_algorithm: str = Field(
        "", description="The algorithm used for the key (e.g. KEY_ALG_RSA_2048)"
    )
    key_origin: str = Field(
        "", description="The origin of the key (e.g. GOOGLE_PROVIDED)"
    )
    key_type: str = Field(
        "", description="The type of the key (e.g. USER_MANAGED)"
    )
    valid_after_time: Optional[datetime] = Field(
        None, description="The time after which the key is valid"
    )
    valid_before_time: Optional[datetime] = Field(
        None, description="The time before which the key is valid"
    )
    private_key_data: Optional[str] = Field(
        None, description="The private key data (only returned on creation)"
    )

    model_config = ConfigDict(
        json_schema_extra={"schema": get_schema("service_account_key")}
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "ServiceAccountKey":
        """Create a ServiceAccountKey from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ServiceAccountKey instance
        """
        full_name = response.get("name", "")
        # name format: projects/{project}/serviceAccounts/{email}/keys/{key_id}
        parts = full_name.split("/")
        project_id = parts[1] if len(parts) >= 2 else ""
        service_account_email = parts[3] if len(parts) >= 4 else ""
        key_id = parts[-1] if parts else ""

        instance = cls(
            id=key_id,
            name=full_name,
            type="iam.serviceAccountKey",
            project=project_id,
            service_account_email=service_account_email,
            key_algorithm=response.get("keyAlgorithm", ""),
            key_origin=response.get("keyOrigin", ""),
            key_type=response.get("keyType", ""),
            valid_after_time=response.get("validAfterTime"),
            valid_before_time=response.get("validBeforeTime"),
            private_key_data=response.get("privateKeyData"),
        )

        return instance


class Role(GCPResource):
    """Model for a Google Cloud IAM Role."""

    title: str = Field("", description="A human-readable title for the role")
    description: str = Field("", description="A description of the role")
    included_permissions: List[str] = Field(
        default_factory=list,
        description="The permissions included in this role",
    )
    stage: str = Field(
        "GA",
        description="The launch stage of the role (ALPHA, BETA, GA, DEPRECATED)",
    )
    deleted: bool = Field(False, description="Whether the role has been deleted")
    etag: Optional[str] = Field(
        None, description="An etag for optimistic concurrency control"
    )

    model_config = ConfigDict(
        json_schema_extra={"schema": get_schema("role")}
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Role":
        """Create a Role from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Role instance
        """
        full_name = response.get("name", "")
        # name format: projects/{project}/roles/{role_id} or roles/{role_id}
        parts = full_name.split("/")
        project_id = ""
        if len(parts) >= 4 and parts[0] == "projects":
            project_id = parts[1]

        role_id = parts[-1] if parts else ""

        instance = cls(
            id=role_id,
            name=full_name,
            type="iam.role",
            project=project_id,
            title=response.get("title", ""),
            description=response.get("description", ""),
            included_permissions=response.get("includedPermissions", []),
            stage=response.get("stage", "GA"),
            deleted=response.get("deleted", False),
            etag=response.get("etag"),
        )

        return instance
