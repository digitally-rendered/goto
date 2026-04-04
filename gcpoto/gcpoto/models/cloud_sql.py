"""Models for Google Cloud SQL resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class SQLInstance(GCPResource):
    """Model for a Google Cloud SQL instance."""

    database_version: str = Field("", description="The database engine version")
    region: str = Field("", description="The GCP region of the instance")
    tier: str = Field("", description="The machine tier (e.g. db-n1-standard-1)")
    state: str = Field("", description="The current state of the instance")
    ip_addresses: List[Dict] = Field(
        default_factory=list,
        description="IP addresses assigned to the instance",
    )
    settings: Dict = Field(
        default_factory=dict,
        description="Instance settings",
    )
    connection_name: Optional[str] = Field(
        None, description="Connection name for the instance"
    )
    gce_zone: Optional[str] = Field(
        None, description="The GCE zone the instance is in"
    )
    _tags: Optional[Dict[str, str]] = None

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
    def from_api_response(cls, response: Dict[str, Any]) -> "SQLInstance":
        """Create an SQLInstance from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new SQLInstance instance
        """
        settings = response.get("settings", {})
        labels = settings.get("userLabels")

        instance = cls(
            id=response.get("name", ""),
            name=response.get("name", ""),
            type="sqladmin.instance",
            project=response.get("project", ""),
            database_version=response.get("databaseVersion", ""),
            region=response.get("region", ""),
            tier=settings.get("tier", ""),
            state=response.get("state", ""),
            ip_addresses=response.get("ipAddresses", []),
            settings=settings,
            connection_name=response.get("connectionName"),
            gce_zone=response.get("gceZone"),
            labels=labels,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if labels:
            instance._tags = labels
        return instance


class SQLDatabase(GCPResource):
    """Model for a Google Cloud SQL database."""

    instance_name: str = Field("", description="The Cloud SQL instance name")
    charset: str = Field("", description="The character set for the database")
    collation: str = Field("", description="The collation for the database")
    self_link: Optional[str] = Field(None, description="The URI of this resource")

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "SQLDatabase":
        """Create an SQLDatabase from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new SQLDatabase instance
        """
        return cls(
            id=response.get("name", ""),
            name=response.get("name", ""),
            type="sqladmin.database",
            project=response.get("project", ""),
            instance_name=response.get("instance", ""),
            charset=response.get("charset", ""),
            collation=response.get("collation", ""),
            self_link=response.get("selfLink"),
        )


class SQLUser(GCPResource):
    """Model for a Google Cloud SQL user."""

    instance_name: str = Field("", description="The Cloud SQL instance name")
    host: str = Field("", description="The host from which the user can connect")
    password_set: bool = Field(
        False, description="Whether the user has a password set"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "SQLUser":
        """Create an SQLUser from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new SQLUser instance
        """
        name = response.get("name", "")
        host = response.get("host", "")
        return cls(
            id=f"{name}@{host}",
            name=name,
            type="sqladmin.user",
            project=response.get("project", ""),
            instance_name=response.get("instance", ""),
            host=host,
            password_set=response.get("passwordSet", False),
        )


class SQLBackupRun(GCPResource):
    """Model for a Google Cloud SQL backup run."""

    instance_name: str = Field("", description="The Cloud SQL instance name")
    status: str = Field("", description="The status of the backup run")
    start_time: Optional[datetime] = Field(
        None, description="The start time of the backup run"
    )
    end_time: Optional[datetime] = Field(
        None, description="The end time of the backup run"
    )
    backup_kind: str = Field(
        "", description="The kind of backup (SNAPSHOT or PHYSICAL)"
    )
    disk_encryption_status: Optional[Dict] = Field(
        None, description="Disk encryption status for the backup"
    )
    location: Optional[str] = Field(
        None, description="The location of the backup"
    )

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "SQLBackupRun":
        """Create an SQLBackupRun from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new SQLBackupRun instance
        """
        return cls(
            id=str(response.get("id", "")),
            name=str(response.get("id", "")),
            type="sqladmin.backupRun",
            project=response.get("project", ""),
            instance_name=response.get("instance", ""),
            status=response.get("status", ""),
            start_time=response.get("startTime"),
            end_time=response.get("endTime"),
            backup_kind=response.get("backupKind", ""),
            disk_encryption_status=response.get("diskEncryptionStatus"),
            location=response.get("location"),
        )
