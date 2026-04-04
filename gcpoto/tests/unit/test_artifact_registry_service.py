"""Tests for Artifact Registry service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.artifact_registry import ArtifactRegistryService
from gcpoto.models.artifact_registry import (
    Repository,
    DockerImage,
    Package,
    PackageVersion,
)
from gcpoto.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError, APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().locations().repositories() chain
        mock_repos = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.repositories.return_value = (
            mock_repos
        )

        # Set up dockerImages() chain
        mock_docker = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.repositories.return_value.dockerImages.return_value = (
            mock_docker
        )

        # Set up packages() chain
        mock_packages = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.repositories.return_value.packages.return_value = (
            mock_packages
        )

        # Set up versions() chain
        mock_versions = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.versions.return_value = (
            mock_versions
        )

        yield mock_service


@pytest.fixture
def sample_repository_response():
    """Sample Artifact Registry repository API response."""
    return {
        "name": "projects/test-project/locations/us-central1/repositories/my-repo",
        "format": "DOCKER",
        "description": "A test Docker repository",
        "labels": {"env": "test", "team": "platform"},
        "createTime": "2025-06-15T10:30:00Z",
        "updateTime": "2025-06-16T08:00:00Z",
        "sizeBytes": 1048576,
        "mode": "STANDARD_REPOSITORY",
    }


@pytest.fixture
def sample_docker_image_response():
    """Sample Artifact Registry docker image API response."""
    return {
        "name": "projects/test-project/locations/us-central1/repositories/my-repo/dockerImages/my-image@sha256:abc123",
        "uri": "us-central1-docker.pkg.dev/test-project/my-repo/my-image@sha256:abc123",
        "tags": ["latest", "v1.0"],
        "imageSizeBytes": 52428800,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "uploadTime": "2025-06-15T12:00:00Z",
        "buildTime": "2025-06-15T11:30:00Z",
    }


@pytest.fixture
def sample_package_response():
    """Sample Artifact Registry package API response."""
    return {
        "name": "projects/test-project/locations/us-central1/repositories/my-repo/packages/my-package",
        "displayName": "My Package",
        "createTime": "2025-06-15T10:30:00Z",
        "updateTime": "2025-06-16T08:00:00Z",
    }


@pytest.fixture
def sample_version_response():
    """Sample Artifact Registry package version API response."""
    return {
        "name": "projects/test-project/locations/us-central1/repositories/my-repo/packages/my-package/versions/1.0.0",
        "description": "Initial release",
        "createTime": "2025-06-15T10:30:00Z",
        "updateTime": "2025-06-16T08:00:00Z",
        "relatedTags": [
            {
                "name": "projects/test-project/locations/us-central1/repositories/my-repo/packages/my-package/tags/latest",
                "version": "projects/test-project/locations/us-central1/repositories/my-repo/packages/my-package/versions/1.0.0",
            }
        ],
    }


# --- Model tests ---


class TestRepositoryModel:
    def test_from_api_response(self, sample_repository_response):
        repo = Repository.from_api_response(
            sample_repository_response, "test-project"
        )
        assert repo.name == "my-repo"
        assert repo.project == "test-project"
        assert repo.type == "artifactregistry.repository"
        assert repo.location == "us-central1"
        assert repo.format_type == "DOCKER"
        assert repo.description == "A test Docker repository"
        assert repo.size_bytes == 1048576
        assert repo.mode == "STANDARD_REPOSITORY"
        assert repo.labels == {"env": "test", "team": "platform"}

    def test_from_api_response_extracts_project(
        self, sample_repository_response
    ):
        repo = Repository.from_api_response(sample_repository_response)
        assert repo.project == "test-project"

    def test_from_api_response_minimal(self):
        repo = Repository.from_api_response(
            {
                "name": "projects/p/locations/us-east1/repositories/r",
                "format": "NPM",
            },
            "p",
        )
        assert repo.name == "r"
        assert repo.format_type == "NPM"
        assert repo.description is None
        assert repo.size_bytes is None
        assert repo.cleanup_policies is None
        assert repo.mode is None

    def test_get_tag_from_tags(self, sample_repository_response):
        repo = Repository.from_api_response(
            sample_repository_response, "test-project"
        )
        assert repo.get_tag("env") == "test"
        assert repo.get_tag("team") == "platform"

    def test_get_tag_default(self, sample_repository_response):
        repo = Repository.from_api_response(
            sample_repository_response, "test-project"
        )
        assert repo.get_tag("missing") == ""
        assert repo.get_tag("missing", "fallback") == "fallback"


class TestDockerImageModel:
    def test_from_api_response(self, sample_docker_image_response):
        image = DockerImage.from_api_response(
            sample_docker_image_response, "test-project"
        )
        assert image.name == "my-image@sha256:abc123"
        assert image.project == "test-project"
        assert image.type == "artifactregistry.dockerImage"
        assert image.repository == "my-repo"
        assert image.location == "us-central1"
        assert (
            image.uri
            == "us-central1-docker.pkg.dev/test-project/my-repo/my-image@sha256:abc123"
        )
        assert image.tags_list == ["latest", "v1.0"]
        assert image.image_size_bytes == 52428800
        assert image.media_type == "application/vnd.docker.distribution.manifest.v2+json"

    def test_from_api_response_extracts_project(
        self, sample_docker_image_response
    ):
        image = DockerImage.from_api_response(sample_docker_image_response)
        assert image.project == "test-project"

    def test_from_api_response_minimal(self):
        image = DockerImage.from_api_response(
            {
                "name": "projects/p/locations/loc/repositories/r/dockerImages/img",
                "uri": "loc-docker.pkg.dev/p/r/img",
            },
            "p",
        )
        assert image.name == "img"
        assert image.uri == "loc-docker.pkg.dev/p/r/img"
        assert image.image_size_bytes is None
        assert image.tags_list is None


class TestPackageModel:
    def test_from_api_response(self, sample_package_response):
        pkg = Package.from_api_response(
            sample_package_response, "test-project"
        )
        assert pkg.name == "my-package"
        assert pkg.project == "test-project"
        assert pkg.type == "artifactregistry.package"
        assert pkg.repository == "my-repo"
        assert pkg.location == "us-central1"
        assert pkg.display_name == "My Package"

    def test_from_api_response_extracts_project(
        self, sample_package_response
    ):
        pkg = Package.from_api_response(sample_package_response)
        assert pkg.project == "test-project"


class TestPackageVersionModel:
    def test_from_api_response(self, sample_version_response):
        ver = PackageVersion.from_api_response(
            sample_version_response, "test-project"
        )
        assert ver.name == "1.0.0"
        assert ver.project == "test-project"
        assert ver.type == "artifactregistry.version"
        assert ver.repository == "my-repo"
        assert ver.location == "us-central1"
        assert ver.package_name == "my-package"
        assert ver.description == "Initial release"
        assert len(ver.related_tags) == 1

    def test_from_api_response_extracts_project(
        self, sample_version_response
    ):
        ver = PackageVersion.from_api_response(sample_version_response)
        assert ver.project == "test-project"

    def test_from_api_response_minimal(self):
        ver = PackageVersion.from_api_response(
            {
                "name": "projects/p/locations/loc/repositories/r/packages/pkg/versions/v1",
            },
            "p",
        )
        assert ver.name == "v1"
        assert ver.description is None
        assert ver.related_tags is None


# --- Service init tests ---


class TestArtifactRegistryServiceInit:
    def test_init(self, mock_google_client):
        from googleapiclient.discovery import build

        service = ArtifactRegistryService(project_id="test-project")
        assert service.project_id == "test-project"
        build.assert_called_once_with(
            "artifactregistry", "v1", credentials=None
        )


# --- Repository service tests ---


class TestListRepositories:
    def test_list_repositories(
        self, mock_google_client, sample_repository_response
    ):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "repositories": [
                sample_repository_response,
                sample_repository_response,
            ]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ArtifactRegistryService(project_id="test-project")
        repos = service.list_repositories("us-central1")

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )
        assert len(repos) == 2
        assert isinstance(repos[0], Repository)
        assert repos[0].name == "my-repo"

    def test_list_repositories_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ArtifactRegistryService(project_id="test-project")
        repos = service.list_repositories("us-central1")
        assert repos == []

    def test_list_repositories_pagination(
        self, mock_google_client, sample_repository_response
    ):
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.list
        )
        mock_list.return_value = mock_request_page1

        mock_request_page1.execute.return_value = {
            "repositories": [sample_repository_response]
        }
        mock_request_page2.execute.return_value = {
            "repositories": [sample_repository_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.list_next
        )
        mock_list_next.side_effect = [mock_request_page2, None]

        service = ArtifactRegistryService(project_id="test-project")
        repos = service.list_repositories("us-central1")
        assert len(repos) == 2


class TestGetRepository:
    def test_get_repository(
        self, mock_google_client, sample_repository_response
    ):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_repository_response

        service = ArtifactRegistryService(project_id="test-project")
        repo = service.get_repository("us-central1", "my-repo")

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/repositories/my-repo"
        )
        assert isinstance(repo, Repository)
        assert repo.name == "my-repo"
        assert repo.format_type == "DOCKER"

    def test_get_repository_not_found(self, mock_google_client):
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.get
        )
        mock_get.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = ArtifactRegistryService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.get_repository("us-central1", "missing-repo")


class TestCreateRepository:
    def test_create_repository(
        self, mock_google_client, sample_repository_response
    ):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_repository_response

        service = ArtifactRegistryService(project_id="test-project")
        repo = service.create_repository(
            "us-central1", "my-repo", "DOCKER"
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1",
            repositoryId="my-repo",
            body={"format": "DOCKER"},
        )
        assert isinstance(repo, Repository)
        assert repo.name == "my-repo"

    def test_create_repository_with_description_and_labels(
        self, mock_google_client, sample_repository_response
    ):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_repository_response

        service = ArtifactRegistryService(project_id="test-project")
        service.create_repository(
            "us-central1",
            "my-repo",
            "DOCKER",
            description="A test repo",
            labels={"env": "test"},
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1",
            repositoryId="my-repo",
            body={
                "format": "DOCKER",
                "description": "A test repo",
                "labels": {"env": "test"},
            },
        )

    def test_create_repository_conflict(self, mock_google_client):
        mock_create = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.create
        )
        mock_create.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        service = ArtifactRegistryService(project_id="test-project")
        with pytest.raises(ResourceAlreadyExistsError):
            service.create_repository(
                "us-central1", "my-repo", "DOCKER"
            )


class TestUpdateRepository:
    def test_update_repository_description(
        self, mock_google_client, sample_repository_response
    ):
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_repository_response

        service = ArtifactRegistryService(project_id="test-project")
        repo = service.update_repository(
            "us-central1", "my-repo", description="Updated description"
        )

        mock_patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/repositories/my-repo",
            body={
                "name": "projects/test-project/locations/us-central1/repositories/my-repo",
                "description": "Updated description",
            },
            updateMask="description",
        )
        assert isinstance(repo, Repository)

    def test_update_repository_labels(
        self, mock_google_client, sample_repository_response
    ):
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_repository_response

        service = ArtifactRegistryService(project_id="test-project")
        service.update_repository(
            "us-central1", "my-repo", labels={"env": "prod"}
        )

        mock_patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/repositories/my-repo",
            body={
                "name": "projects/test-project/locations/us-central1/repositories/my-repo",
                "labels": {"env": "prod"},
            },
            updateMask="labels",
        )

    def test_update_repository_description_and_labels(
        self, mock_google_client, sample_repository_response
    ):
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_repository_response

        service = ArtifactRegistryService(project_id="test-project")
        service.update_repository(
            "us-central1",
            "my-repo",
            description="New desc",
            labels={"env": "staging"},
        )

        mock_patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/repositories/my-repo",
            body={
                "name": "projects/test-project/locations/us-central1/repositories/my-repo",
                "description": "New desc",
                "labels": {"env": "staging"},
            },
            updateMask="description,labels",
        )


class TestDeleteRepository:
    def test_delete_repository(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = ArtifactRegistryService(project_id="test-project")
        result = service.delete_repository("us-central1", "my-repo")

        mock_delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/repositories/my-repo"
        )
        assert result is True

    def test_delete_repository_not_found(self, mock_google_client):
        mock_delete = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.delete
        )
        mock_delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = ArtifactRegistryService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.delete_repository("us-central1", "missing-repo")


# --- Docker Image service tests ---


class TestListDockerImages:
    def test_list_docker_images(
        self, mock_google_client, sample_docker_image_response
    ):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.dockerImages.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "dockerImages": [
                sample_docker_image_response,
                sample_docker_image_response,
            ]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.dockerImages.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ArtifactRegistryService(project_id="test-project")
        images = service.list_docker_images("us-central1", "my-repo")

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1/repositories/my-repo"
        )
        assert len(images) == 2
        assert isinstance(images[0], DockerImage)
        assert images[0].tags_list == ["latest", "v1.0"]

    def test_list_docker_images_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.dockerImages.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.dockerImages.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ArtifactRegistryService(project_id="test-project")
        images = service.list_docker_images("us-central1", "my-repo")
        assert images == []


class TestGetDockerImage:
    def test_get_docker_image(
        self, mock_google_client, sample_docker_image_response
    ):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.dockerImages.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_docker_image_response

        service = ArtifactRegistryService(project_id="test-project")
        image = service.get_docker_image(
            "us-central1", "my-repo", "my-image@sha256:abc123"
        )

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/repositories/my-repo/dockerImages/my-image@sha256:abc123"
        )
        assert isinstance(image, DockerImage)
        assert image.uri == "us-central1-docker.pkg.dev/test-project/my-repo/my-image@sha256:abc123"

    def test_get_docker_image_not_found(self, mock_google_client):
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.dockerImages.return_value.get
        )
        mock_get.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = ArtifactRegistryService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.get_docker_image(
                "us-central1", "my-repo", "missing-image"
            )


# --- Package service tests ---


class TestListPackages:
    def test_list_packages(
        self, mock_google_client, sample_package_response
    ):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "packages": [sample_package_response, sample_package_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ArtifactRegistryService(project_id="test-project")
        packages = service.list_packages("us-central1", "my-repo")

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1/repositories/my-repo"
        )
        assert len(packages) == 2
        assert isinstance(packages[0], Package)
        assert packages[0].display_name == "My Package"

    def test_list_packages_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ArtifactRegistryService(project_id="test-project")
        packages = service.list_packages("us-central1", "my-repo")
        assert packages == []

    def test_list_packages_pagination(
        self, mock_google_client, sample_package_response
    ):
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.list
        )
        mock_list.return_value = mock_request_page1

        mock_request_page1.execute.return_value = {
            "packages": [sample_package_response]
        }
        mock_request_page2.execute.return_value = {
            "packages": [sample_package_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.list_next
        )
        mock_list_next.side_effect = [mock_request_page2, None]

        service = ArtifactRegistryService(project_id="test-project")
        packages = service.list_packages("us-central1", "my-repo")
        assert len(packages) == 2


class TestGetPackage:
    def test_get_package(
        self, mock_google_client, sample_package_response
    ):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_package_response

        service = ArtifactRegistryService(project_id="test-project")
        pkg = service.get_package(
            "us-central1", "my-repo", "my-package"
        )

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/repositories/my-repo/packages/my-package"
        )
        assert isinstance(pkg, Package)
        assert pkg.name == "my-package"

    def test_get_package_not_found(self, mock_google_client):
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.get
        )
        mock_get.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = ArtifactRegistryService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.get_package(
                "us-central1", "my-repo", "missing-package"
            )


class TestDeletePackage:
    def test_delete_package(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = ArtifactRegistryService(project_id="test-project")
        result = service.delete_package(
            "us-central1", "my-repo", "my-package"
        )

        mock_delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/repositories/my-repo/packages/my-package"
        )
        assert result is True

    def test_delete_package_not_found(self, mock_google_client):
        mock_delete = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.delete
        )
        mock_delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = ArtifactRegistryService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.delete_package(
                "us-central1", "my-repo", "missing-package"
            )


# --- Version service tests ---


class TestListVersions:
    def test_list_versions(
        self, mock_google_client, sample_version_response
    ):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.versions.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "versions": [sample_version_response, sample_version_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.versions.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ArtifactRegistryService(project_id="test-project")
        versions = service.list_versions(
            "us-central1", "my-repo", "my-package"
        )

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1/repositories/my-repo/packages/my-package"
        )
        assert len(versions) == 2
        assert isinstance(versions[0], PackageVersion)
        assert versions[0].name == "1.0.0"

    def test_list_versions_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.versions.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.versions.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ArtifactRegistryService(project_id="test-project")
        versions = service.list_versions(
            "us-central1", "my-repo", "my-package"
        )
        assert versions == []

    def test_list_versions_pagination(
        self, mock_google_client, sample_version_response
    ):
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.versions.return_value.list
        )
        mock_list.return_value = mock_request_page1

        mock_request_page1.execute.return_value = {
            "versions": [sample_version_response]
        }
        mock_request_page2.execute.return_value = {
            "versions": [sample_version_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.versions.return_value.list_next
        )
        mock_list_next.side_effect = [mock_request_page2, None]

        service = ArtifactRegistryService(project_id="test-project")
        versions = service.list_versions(
            "us-central1", "my-repo", "my-package"
        )
        assert len(versions) == 2


class TestGetVersion:
    def test_get_version(
        self, mock_google_client, sample_version_response
    ):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.versions.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_version_response

        service = ArtifactRegistryService(project_id="test-project")
        version = service.get_version(
            "us-central1", "my-repo", "my-package", "1.0.0"
        )

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/repositories/my-repo/packages/my-package/versions/1.0.0"
        )
        assert isinstance(version, PackageVersion)
        assert version.name == "1.0.0"
        assert version.description == "Initial release"

    def test_get_version_not_found(self, mock_google_client):
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.versions.return_value.get
        )
        mock_get.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = ArtifactRegistryService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.get_version(
                "us-central1", "my-repo", "my-package", "9.9.9"
            )


class TestDeleteVersion:
    def test_delete_version(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.versions.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = ArtifactRegistryService(project_id="test-project")
        result = service.delete_version(
            "us-central1", "my-repo", "my-package", "1.0.0"
        )

        mock_delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/repositories/my-repo/packages/my-package/versions/1.0.0"
        )
        assert result is True

    def test_delete_version_not_found(self, mock_google_client):
        mock_delete = (
            mock_google_client.projects.return_value.locations.return_value.repositories.return_value.packages.return_value.versions.return_value.delete
        )
        mock_delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = ArtifactRegistryService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.delete_version(
                "us-central1", "my-repo", "my-package", "9.9.9"
            )
