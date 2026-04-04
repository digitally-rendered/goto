"""Models for Google Cloud KMS resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.kms import get_schema


class KeyRing(GCPResource):
    """Model for a Google Cloud KMS Key Ring."""

    location: str = Field("", description="The location of the key ring")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("key_ring")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "KeyRing":
        """Create a KeyRing from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new KeyRing instance
        """
        full_name = response.get("name", "")
        # Format: projects/{project}/locations/{location}/keyRings/{keyRing}
        parts = full_name.split("/")
        key_ring_name = parts[-1] if parts else ""
        location = ""

        if len(parts) >= 4:
            if not project_id:
                project_id = parts[1]
            location = parts[3]

        return cls(
            id=full_name,
            name=key_ring_name,
            type="kms.keyRing",
            project=project_id,
            location=location,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )


class CryptoKey(GCPResource):
    """Model for a Google Cloud KMS Crypto Key."""

    key_ring: str = Field("", description="The key ring this crypto key belongs to")
    purpose: str = Field(
        "",
        description="The immutable purpose of this crypto key",
    )
    algorithm: Optional[str] = Field(
        None, description="The algorithm of the primary version"
    )
    protection_level: Optional[str] = Field(
        None, description="The protection level of the primary version"
    )
    rotation_period: Optional[str] = Field(
        None, description="The rotation period of the key"
    )
    next_rotation_time: Optional[datetime] = Field(
        None, description="The next scheduled rotation time"
    )
    primary_version: Optional[Dict[str, Any]] = Field(
        None, description="The primary version of this crypto key"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("crypto_key")}

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
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "CryptoKey":
        """Create a CryptoKey from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new CryptoKey instance
        """
        full_name = response.get("name", "")
        # Format: projects/{project}/locations/{loc}/keyRings/{kr}/cryptoKeys/{key}
        parts = full_name.split("/")
        key_name = parts[-1] if parts else ""
        key_ring = ""

        if len(parts) >= 6:
            if not project_id:
                project_id = parts[1]
            key_ring = parts[5]

        primary = response.get("primary")
        algorithm = None
        protection_level = None
        if primary:
            algorithm = primary.get("algorithm")
            protection_level = primary.get("protectionLevel")

        instance = cls(
            id=full_name,
            name=key_name,
            type="kms.cryptoKey",
            project=project_id,
            labels=response.get("labels"),
            key_ring=key_ring,
            purpose=response.get("purpose", ""),
            algorithm=algorithm,
            protection_level=protection_level,
            rotation_period=response.get("rotationPeriod"),
            next_rotation_time=response.get("nextRotationTime"),
            primary_version=primary,
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class CryptoKeyVersion(GCPResource):
    """Model for a Google Cloud KMS Crypto Key Version."""

    crypto_key: str = Field(
        "", description="The crypto key this version belongs to"
    )
    state: str = Field("", description="The current state of the version")
    algorithm: str = Field("", description="The algorithm of this version")
    protection_level: str = Field(
        "", description="The protection level of this version"
    )
    generate_time: Optional[datetime] = Field(
        None, description="The time at which this version's key material was generated"
    )
    destroy_time: Optional[datetime] = Field(
        None, description="The time this version is scheduled for destruction"
    )
    destroy_event_time: Optional[datetime] = Field(
        None, description="The time this version's key material was destroyed"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("crypto_key_version")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "CryptoKeyVersion":
        """Create a CryptoKeyVersion from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID (extracted from the name if not provided)

        Returns:
            A new CryptoKeyVersion instance
        """
        full_name = response.get("name", "")
        # Format: .../cryptoKeys/{key}/cryptoKeyVersions/{version}
        parts = full_name.split("/")
        version_name = parts[-1] if parts else ""
        crypto_key = ""

        if len(parts) >= 8:
            if not project_id:
                project_id = parts[1]
            crypto_key = parts[7]

        return cls(
            id=full_name,
            name=version_name,
            type="kms.cryptoKeyVersion",
            project=project_id,
            crypto_key=crypto_key,
            state=response.get("state", ""),
            algorithm=response.get("algorithm", ""),
            protection_level=response.get("protectionLevel", ""),
            generate_time=response.get("generateTime"),
            destroy_time=response.get("destroyTime"),
            destroy_event_time=response.get("destroyEventTime"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
