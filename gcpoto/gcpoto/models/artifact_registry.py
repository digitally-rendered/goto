"""Models for Google Cloud Artifact Registry resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.artifact_registry import get_schema


class Repository(GCPResource):
    """Model for a Google Cloud Artifact Registry Repository."""

    location: str = Field("", description="The GCP location of the repository")
    format_type: str = Field(
        "",
        description="The format of packages stored in the repository "
        "(DOCKER, MAVEN, NPM, APT, YUM, PYTHON, GO)",
    )
    description: Optional[str] = Field(
        None, description="The user-provided description of the repository"
    )
    size_bytes: Optional[int] = Field(
        None, description="The size, in bytes, of all artifact storage in this repository"
    )
    cleanup_policies: Optional[Dict[str, Any]] = Field(
        None, description="Cleanup policies for this repository"
    )
    mode: Optional[str] = Field(
        None,
        description="The mode of the repository "
        "(STANDARD_REPOSITORY, VIRTUAL_REPOSITORY, REMOTE_REPOSITORY)",
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

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("repository")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "Repository":
        """Create a Repository from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new Repository instance
        """
        full_name = response.get("name", "")
        parts = full_name.split("/") if full_name else []

        repo_name = parts[-1] if parts else ""
        location = parts[3] if len(parts) >= 4 else ""

        if not project_id and len(parts) >= 2:
            project_id = parts[1]

        instance = cls(
            id=full_name,
            name=repo_name,
            type="artifactregistry.repository",
            project=project_id,
            location=location,
            format_type=response.get("format", ""),
            description=response.get("description"),
            size_bytes=response.get("sizeBytes"),
            cleanup_policies=response.get("cleanupPolicies"),
            mode=response.get("mode"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class DockerImage(GCPResource):
    """Model for a Google Cloud Artifact Registry Docker Image."""

    repository: str = Field("", description="The parent repository name")
    location: str = Field("", description="The GCP location")
    uri: str = Field("", description="The URI of the docker image")
    image_size_bytes: Optional[int] = Field(
        None, description="The size of the docker image in bytes"
    )
    media_type: Optional[str] = Field(
        None, description="The media type of the docker image"
    )
    upload_time: Optional[datetime] = Field(
        None, description="The time when the docker image was uploaded"
    )
    build_time: Optional[datetime] = Field(
        None, description="The time when the docker image was built"
    )
    tags_list: Optional[List[str]] = Field(
        None, description="Tags associated with this docker image"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("docker_image")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "DockerImage":
        """Create a DockerImage from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new DockerImage instance
        """
        full_name = response.get("name", "")
        parts = full_name.split("/") if full_name else []

        # name format: projects/{project}/locations/{location}/repositories/{repo}/dockerImages/{image}
        image_name = parts[-1] if parts else ""
        location = parts[3] if len(parts) >= 4 else ""
        repository = parts[5] if len(parts) >= 6 else ""

        if not project_id and len(parts) >= 2:
            project_id = parts[1]

        return cls(
            id=full_name,
            name=image_name,
            type="artifactregistry.dockerImage",
            project=project_id,
            repository=repository,
            location=location,
            uri=response.get("uri", ""),
            image_size_bytes=response.get("imageSizeBytes"),
            media_type=response.get("mediaType"),
            upload_time=response.get("uploadTime"),
            build_time=response.get("buildTime"),
            tags_list=response.get("tags"),
        )


class Package(GCPResource):
    """Model for a Google Cloud Artifact Registry Package."""

    repository: str = Field("", description="The parent repository name")
    location: str = Field("", description="The GCP location")
    display_name: Optional[str] = Field(
        None, description="The display name of the package"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("package")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "Package":
        """Create a Package from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new Package instance
        """
        full_name = response.get("name", "")
        parts = full_name.split("/") if full_name else []

        # name format: projects/{project}/locations/{location}/repositories/{repo}/packages/{pkg}
        package_name = parts[-1] if parts else ""
        location = parts[3] if len(parts) >= 4 else ""
        repository = parts[5] if len(parts) >= 6 else ""

        if not project_id and len(parts) >= 2:
            project_id = parts[1]

        return cls(
            id=full_name,
            name=package_name,
            type="artifactregistry.package",
            project=project_id,
            repository=repository,
            location=location,
            display_name=response.get("displayName"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )


class PackageVersion(GCPResource):
    """Model for a Google Cloud Artifact Registry Package Version."""

    package_name: str = Field("", description="The parent package name")
    repository: str = Field("", description="The parent repository name")
    location: str = Field("", description="The GCP location")
    description: Optional[str] = Field(
        None, description="Optional description of the version"
    )
    related_tags: Optional[List[Dict[str, Any]]] = Field(
        None, description="Tags associated with this version"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("version")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "PackageVersion":
        """Create a PackageVersion from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new PackageVersion instance
        """
        full_name = response.get("name", "")
        parts = full_name.split("/") if full_name else []

        # name format: projects/{project}/locations/{location}/repositories/{repo}/packages/{pkg}/versions/{ver}
        version_name = parts[-1] if parts else ""
        location = parts[3] if len(parts) >= 4 else ""
        repository = parts[5] if len(parts) >= 6 else ""
        package_name = parts[7] if len(parts) >= 8 else ""

        if not project_id and len(parts) >= 2:
            project_id = parts[1]

        return cls(
            id=full_name,
            name=version_name,
            type="artifactregistry.version",
            project=project_id,
            package_name=package_name,
            repository=repository,
            location=location,
            description=response.get("description"),
            related_tags=response.get("relatedTags"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
