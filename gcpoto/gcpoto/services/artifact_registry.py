"""Service implementation for Google Cloud Artifact Registry."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.artifact_registry import (
    Repository,
    DockerImage,
    Package,
    PackageVersion,
)
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class ArtifactRegistryService(GCPService[Repository]):
    """Service for interacting with Google Cloud Artifact Registry."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Artifact Registry service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="artifactregistry",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Repository,
            **kwargs,
        )

    def _format_repository_path(
        self, location: str, repository_id: str
    ) -> str:
        """Format a full repository resource path.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID

        Returns:
            The fully-qualified repository resource path
        """
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/repositories/{repository_id}"
        )

    def _format_location_path(self, location: str) -> str:
        """Format a full location resource path.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            The fully-qualified location resource path
        """
        return f"projects/{self.project_id}/locations/{location}"

    # --- Repository methods ---

    def list_repositories(self, location: str) -> List[Repository]:
        """List repositories in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            A list of Repository instances
        """
        parent = self._format_location_path(location)
        logger.debug("Listing repositories in %s", parent)

        request = (
            self.service.projects()
            .locations()
            .repositories()
            .list(parent=parent)
        )

        repositories = []
        while request is not None:
            response = request.execute()
            for repo_data in response.get("repositories", []):
                repositories.append(
                    Repository.from_api_response(repo_data, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .repositories()
                .list_next(request, response)
            )

        logger.debug("Found %s repositories", len(repositories))
        return repositories

    def get_repository(
        self, location: str, repository_id: str
    ) -> Repository:
        """Get a specific repository.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID

        Returns:
            A Repository instance
        """
        name = self._format_repository_path(location, repository_id)
        logger.debug("Getting repository %s", name)

        try:
            request = (
                self.service.projects()
                .locations()
                .repositories()
                .get(name=name)
            )
            response = request.execute()
            return Repository.from_api_response(response, self.project_id)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "Repository", repository_id
                ) from e
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e)) from e

    def create_repository(
        self,
        location: str,
        repository_id: str,
        format_type: str,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Repository:
        """Create a new repository.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The ID for the new repository
            format_type: The package format (DOCKER, MAVEN, NPM, APT, YUM, PYTHON, GO)
            description: Optional description for the repository
            labels: Optional labels to apply to the repository

        Returns:
            The created Repository instance
        """
        parent = self._format_location_path(location)
        logger.debug(
            "Creating repository %s in %s with format %s",
            repository_id,
            parent,
            format_type,
        )

        body: Dict[str, Any] = {"format": format_type}

        if description is not None:
            body["description"] = description

        if labels is not None:
            body["labels"] = labels

        try:
            request = (
                self.service.projects()
                .locations()
                .repositories()
                .create(
                    parent=parent,
                    repositoryId=repository_id,
                    body=body,
                )
            )
            response = request.execute()
            return Repository.from_api_response(response, self.project_id)
        except HttpError as e:
            if e.resp.status == 409:
                raise ValueError(
                    f"Repository '{repository_id}' already exists"
                ) from e
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e)) from e

    def update_repository(
        self,
        location: str,
        repository_id: str,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Repository:
        """Update a repository's metadata.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID
            description: Optional new description
            labels: Optional new labels

        Returns:
            The updated Repository instance
        """
        name = self._format_repository_path(location, repository_id)
        logger.debug("Updating repository %s", name)

        body: Dict[str, Any] = {"name": name}
        update_mask_fields = []

        if description is not None:
            body["description"] = description
            update_mask_fields.append("description")

        if labels is not None:
            body["labels"] = labels
            update_mask_fields.append("labels")

        update_mask = ",".join(update_mask_fields)

        request = (
            self.service.projects()
            .locations()
            .repositories()
            .patch(name=name, body=body, updateMask=update_mask)
        )
        response = request.execute()
        return Repository.from_api_response(response, self.project_id)

    def delete_repository(
        self, location: str, repository_id: str
    ) -> bool:
        """Delete a repository.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID

        Returns:
            True if the deletion was successful
        """
        name = self._format_repository_path(location, repository_id)
        logger.debug("Deleting repository %s", name)

        try:
            self.service.projects().locations().repositories().delete(
                name=name
            ).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "Repository", repository_id
                ) from e
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e)) from e

    # --- Docker Image methods ---

    def list_docker_images(
        self, location: str, repository_id: str
    ) -> List[DockerImage]:
        """List docker images in a repository.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID

        Returns:
            A list of DockerImage instances
        """
        parent = self._format_repository_path(location, repository_id)
        logger.debug("Listing docker images in %s", parent)

        request = (
            self.service.projects()
            .locations()
            .repositories()
            .dockerImages()
            .list(parent=parent)
        )

        images = []
        while request is not None:
            response = request.execute()
            for image_data in response.get("dockerImages", []):
                images.append(
                    DockerImage.from_api_response(
                        image_data, self.project_id
                    )
                )
            request = (
                self.service.projects()
                .locations()
                .repositories()
                .dockerImages()
                .list_next(request, response)
            )

        logger.debug("Found %s docker images", len(images))
        return images

    def get_docker_image(
        self, location: str, repository_id: str, image_name: str
    ) -> DockerImage:
        """Get a specific docker image.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID
            image_name: The docker image name

        Returns:
            A DockerImage instance
        """
        name = (
            f"{self._format_repository_path(location, repository_id)}"
            f"/dockerImages/{image_name}"
        )
        logger.debug("Getting docker image %s", name)

        try:
            request = (
                self.service.projects()
                .locations()
                .repositories()
                .dockerImages()
                .get(name=name)
            )
            response = request.execute()
            return DockerImage.from_api_response(response, self.project_id)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "DockerImage", image_name
                ) from e
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e)) from e

    # --- Package methods ---

    def list_packages(
        self, location: str, repository_id: str
    ) -> List[Package]:
        """List packages in a repository.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID

        Returns:
            A list of Package instances
        """
        parent = self._format_repository_path(location, repository_id)
        logger.debug("Listing packages in %s", parent)

        request = (
            self.service.projects()
            .locations()
            .repositories()
            .packages()
            .list(parent=parent)
        )

        packages = []
        while request is not None:
            response = request.execute()
            for pkg_data in response.get("packages", []):
                packages.append(
                    Package.from_api_response(pkg_data, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .repositories()
                .packages()
                .list_next(request, response)
            )

        logger.debug("Found %s packages", len(packages))
        return packages

    def get_package(
        self, location: str, repository_id: str, package_name: str
    ) -> Package:
        """Get a specific package.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID
            package_name: The package name

        Returns:
            A Package instance
        """
        name = (
            f"{self._format_repository_path(location, repository_id)}"
            f"/packages/{package_name}"
        )
        logger.debug("Getting package %s", name)

        try:
            request = (
                self.service.projects()
                .locations()
                .repositories()
                .packages()
                .get(name=name)
            )
            response = request.execute()
            return Package.from_api_response(response, self.project_id)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "Package", package_name
                ) from e
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e)) from e

    def delete_package(
        self, location: str, repository_id: str, package_name: str
    ) -> bool:
        """Delete a package.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID
            package_name: The package name

        Returns:
            True if the deletion was successful
        """
        name = (
            f"{self._format_repository_path(location, repository_id)}"
            f"/packages/{package_name}"
        )
        logger.debug("Deleting package %s", name)

        try:
            self.service.projects().locations().repositories().packages().delete(
                name=name
            ).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "Package", package_name
                ) from e
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e)) from e

    # --- Version methods ---

    def list_versions(
        self, location: str, repository_id: str, package_name: str
    ) -> List[PackageVersion]:
        """List versions of a package.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID
            package_name: The package name

        Returns:
            A list of PackageVersion instances
        """
        parent = (
            f"{self._format_repository_path(location, repository_id)}"
            f"/packages/{package_name}"
        )
        logger.debug("Listing versions in %s", parent)

        request = (
            self.service.projects()
            .locations()
            .repositories()
            .packages()
            .versions()
            .list(parent=parent)
        )

        versions = []
        while request is not None:
            response = request.execute()
            for ver_data in response.get("versions", []):
                versions.append(
                    PackageVersion.from_api_response(
                        ver_data, self.project_id
                    )
                )
            request = (
                self.service.projects()
                .locations()
                .repositories()
                .packages()
                .versions()
                .list_next(request, response)
            )

        logger.debug("Found %s versions", len(versions))
        return versions

    def get_version(
        self,
        location: str,
        repository_id: str,
        package_name: str,
        version_id: str,
    ) -> PackageVersion:
        """Get a specific package version.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID
            package_name: The package name
            version_id: The version identifier

        Returns:
            A PackageVersion instance
        """
        name = (
            f"{self._format_repository_path(location, repository_id)}"
            f"/packages/{package_name}/versions/{version_id}"
        )
        logger.debug("Getting version %s", name)

        try:
            request = (
                self.service.projects()
                .locations()
                .repositories()
                .packages()
                .versions()
                .get(name=name)
            )
            response = request.execute()
            return PackageVersion.from_api_response(
                response, self.project_id
            )
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "PackageVersion", version_id
                ) from e
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e)) from e

    def delete_version(
        self,
        location: str,
        repository_id: str,
        package_name: str,
        version_id: str,
    ) -> bool:
        """Delete a package version.

        Args:
            location: The GCP location (e.g. 'us-central1')
            repository_id: The repository ID
            package_name: The package name
            version_id: The version identifier

        Returns:
            True if the deletion was successful
        """
        name = (
            f"{self._format_repository_path(location, repository_id)}"
            f"/packages/{package_name}/versions/{version_id}"
        )
        logger.debug("Deleting version %s", name)

        try:
            (
                self.service.projects()
                .locations()
                .repositories()
                .packages()
                .versions()
                .delete(name=name)
                .execute()
            )
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "PackageVersion", version_id
                ) from e
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e)) from e
