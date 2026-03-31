"""Tests for Secret Manager service."""

import base64
from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.secret_manager import SecretManagerService
from gcpoto.models.secret_manager import Secret, SecretVersion
from gcpoto.utils import format_secret_path, format_secret_version_path


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().secrets() chain
        mock_secrets = mock.MagicMock()
        mock_service.projects.return_value.secrets.return_value = mock_secrets

        # Set up projects().secrets().versions() chain
        mock_versions = mock.MagicMock()
        mock_service.projects.return_value.secrets.return_value.versions.return_value = (
            mock_versions
        )

        yield mock_service


@pytest.fixture
def sample_secret_response():
    """Sample Secret Manager secret API response."""
    return {
        "name": "projects/test-project/secrets/my-secret",
        "replication": {"automatic": {}},
        "createTime": "2025-01-15T10:30:00Z",
        "labels": {"env": "test", "team": "backend"},
        "topics": [
            {"name": "projects/test-project/topics/secret-notifications"}
        ],
    }


@pytest.fixture
def sample_version_response():
    """Sample Secret Manager version API response."""
    return {
        "name": "projects/test-project/secrets/my-secret/versions/1",
        "createTime": "2025-01-15T10:30:00Z",
        "state": "ENABLED",
        "replicationStatus": {"automatic": {}},
    }


@pytest.fixture
def sample_disabled_version_response():
    """Sample disabled Secret Manager version API response."""
    return {
        "name": "projects/test-project/secrets/my-secret/versions/1",
        "createTime": "2025-01-15T10:30:00Z",
        "state": "DISABLED",
        "replicationStatus": {"automatic": {}},
    }


@pytest.fixture
def sample_destroyed_version_response():
    """Sample destroyed Secret Manager version API response."""
    return {
        "name": "projects/test-project/secrets/my-secret/versions/1",
        "createTime": "2025-01-15T10:30:00Z",
        "destroyTime": "2025-02-01T12:00:00Z",
        "state": "DESTROYED",
        "replicationStatus": {"automatic": {}},
    }


# --- Utility tests ---


class TestFormatPaths:
    def test_format_secret_path_short_name(self):
        result = format_secret_path("my-project", "my-secret")
        assert result == "projects/my-project/secrets/my-secret"

    def test_format_secret_path_full_name(self):
        full = "projects/my-project/secrets/my-secret"
        assert format_secret_path("my-project", full) == full

    def test_format_secret_version_path_short_name(self):
        result = format_secret_version_path("my-project", "my-secret", "3")
        assert result == "projects/my-project/secrets/my-secret/versions/3"

    def test_format_secret_version_path_latest(self):
        result = format_secret_version_path(
            "my-project", "my-secret", "latest"
        )
        assert (
            result == "projects/my-project/secrets/my-secret/versions/latest"
        )

    def test_format_secret_version_path_full_secret(self):
        result = format_secret_version_path(
            "my-project",
            "projects/my-project/secrets/my-secret",
            "1",
        )
        assert result == "projects/my-project/secrets/my-secret/versions/1"


# --- Model tests ---


class TestSecretModel:
    def test_from_api_response(self, sample_secret_response):
        secret = Secret.from_api_response(
            sample_secret_response, "test-project"
        )
        assert secret.name == "my-secret"
        assert secret.project == "test-project"
        assert secret.type == "secretmanager.secret"
        assert secret.replication == {"automatic": {}}
        assert secret.labels == {"env": "test", "team": "backend"}
        assert secret.topics == [
            "projects/test-project/topics/secret-notifications"
        ]

    def test_from_api_response_extracts_project(self, sample_secret_response):
        secret = Secret.from_api_response(sample_secret_response)
        assert secret.project == "test-project"

    def test_from_api_response_minimal(self):
        secret = Secret.from_api_response(
            {"name": "projects/p/secrets/s", "replication": {"automatic": {}}},
            "p",
        )
        assert secret.name == "s"
        assert secret.expire_time is None
        assert secret.ttl is None
        assert secret.rotation is None
        assert secret.topics is None

    def test_get_tag_from_tags(self, sample_secret_response):
        secret = Secret.from_api_response(
            sample_secret_response, "test-project"
        )
        assert secret.get_tag("env") == "test"
        assert secret.get_tag("team") == "backend"

    def test_get_tag_default(self, sample_secret_response):
        secret = Secret.from_api_response(
            sample_secret_response, "test-project"
        )
        assert secret.get_tag("missing") == ""
        assert secret.get_tag("missing", "fallback") == "fallback"


class TestSecretVersionModel:
    def test_from_api_response(self, sample_version_response):
        version = SecretVersion.from_api_response(
            sample_version_response, "test-project"
        )
        assert version.secret_name == "my-secret"
        assert version.version_id == "1"
        assert version.state == "ENABLED"
        assert version.project == "test-project"
        assert version.destroy_time is None

    def test_from_api_response_destroyed(
        self, sample_destroyed_version_response
    ):
        version = SecretVersion.from_api_response(
            sample_destroyed_version_response, "test-project"
        )
        assert version.state == "DESTROYED"
        assert version.destroy_time is not None

    def test_from_api_response_extracts_project(
        self, sample_version_response
    ):
        version = SecretVersion.from_api_response(sample_version_response)
        assert version.project == "test-project"


# --- Service tests ---


class TestSecretManagerServiceInit:
    def test_init(self, mock_google_client):
        from googleapiclient.discovery import build

        service = SecretManagerService(project_id="test-project")
        assert service.project_id == "test-project"
        build.assert_called_once_with(
            "secretmanager", "v1", credentials=None
        )


class TestListSecrets:
    def test_list_secrets(self, mock_google_client, sample_secret_response):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.secrets.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "secrets": [sample_secret_response, sample_secret_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.secrets.return_value.list_next
        )
        mock_list_next.return_value = None

        service = SecretManagerService(project_id="test-project")
        secrets = service.list_secrets()

        mock_list.assert_called_once_with(parent="projects/test-project")
        assert len(secrets) == 2
        assert isinstance(secrets[0], Secret)
        assert secrets[0].name == "my-secret"
        assert secrets[0].project == "test-project"

    def test_list_secrets_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.secrets.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value.secrets.return_value.list_next
        )
        mock_list_next.return_value = None

        service = SecretManagerService(project_id="test-project")
        secrets = service.list_secrets()
        assert secrets == []

    def test_list_secrets_pagination(
        self, mock_google_client, sample_secret_response
    ):
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = (
            mock_google_client.projects.return_value.secrets.return_value.list
        )
        mock_list.return_value = mock_request_page1

        mock_request_page1.execute.return_value = {
            "secrets": [sample_secret_response]
        }
        mock_request_page2.execute.return_value = {
            "secrets": [sample_secret_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.secrets.return_value.list_next
        )
        mock_list_next.side_effect = [mock_request_page2, None]

        service = SecretManagerService(project_id="test-project")
        secrets = service.list_secrets()
        assert len(secrets) == 2


class TestGetSecret:
    def test_get_secret(self, mock_google_client, sample_secret_response):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.secrets.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_secret_response

        service = SecretManagerService(project_id="test-project")
        secret = service.get_secret("my-secret")

        mock_get.assert_called_once_with(
            name="projects/test-project/secrets/my-secret"
        )
        assert isinstance(secret, Secret)
        assert secret.name == "my-secret"

    def test_get_secret_full_path(
        self, mock_google_client, sample_secret_response
    ):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.secrets.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_secret_response

        service = SecretManagerService(project_id="test-project")
        service.get_secret("projects/test-project/secrets/my-secret")

        mock_get.assert_called_once_with(
            name="projects/test-project/secrets/my-secret"
        )


class TestCreateSecret:
    def test_create_secret_default_replication(
        self, mock_google_client, sample_secret_response
    ):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.secrets.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_secret_response

        service = SecretManagerService(project_id="test-project")
        secret = service.create_secret("my-secret")

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            secretId="my-secret",
            body={"replication": {"automatic": {}}},
        )
        assert isinstance(secret, Secret)
        assert secret.name == "my-secret"

    def test_create_secret_with_labels(
        self, mock_google_client, sample_secret_response
    ):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.secrets.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_secret_response

        service = SecretManagerService(project_id="test-project")
        service.create_secret(
            "my-secret",
            replication={"userManaged": {"replicas": [{"location": "us-east1"}]}},
            labels={"env": "test"},
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            secretId="my-secret",
            body={
                "replication": {
                    "userManaged": {"replicas": [{"location": "us-east1"}]}
                },
                "labels": {"env": "test"},
            },
        )

    def test_create_secret_conflict(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.secrets.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        service = SecretManagerService(project_id="test-project")
        with pytest.raises(ValueError, match="Secret 'my-secret' already exists"):
            service.create_secret("my-secret")


class TestDeleteSecret:
    def test_delete_secret(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.secrets.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = SecretManagerService(project_id="test-project")
        result = service.delete_secret("my-secret")

        mock_delete.assert_called_once_with(
            name="projects/test-project/secrets/my-secret"
        )
        assert result is True

    def test_delete_secret_full_path(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.secrets.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = SecretManagerService(project_id="test-project")
        service.delete_secret("projects/test-project/secrets/my-secret")

        mock_delete.assert_called_once_with(
            name="projects/test-project/secrets/my-secret"
        )


class TestUpdateSecret:
    def test_update_secret_labels(
        self, mock_google_client, sample_secret_response
    ):
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.secrets.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_secret_response

        service = SecretManagerService(project_id="test-project")
        secret = service.update_secret("my-secret", labels={"env": "prod"})

        mock_patch.assert_called_once_with(
            name="projects/test-project/secrets/my-secret",
            body={
                "name": "projects/test-project/secrets/my-secret",
                "labels": {"env": "prod"},
            },
            updateMask="labels",
        )
        assert isinstance(secret, Secret)


class TestAddSecretVersion:
    def test_add_secret_version(
        self, mock_google_client, sample_version_response
    ):
        mock_request = mock.MagicMock()
        mock_add = (
            mock_google_client.projects.return_value.secrets.return_value.addVersion
        )
        mock_add.return_value = mock_request
        mock_request.execute.return_value = sample_version_response

        service = SecretManagerService(project_id="test-project")
        payload = b"super-secret-value"
        version = service.add_secret_version("my-secret", payload)

        expected_data = base64.b64encode(payload).decode("utf-8")
        mock_add.assert_called_once_with(
            parent="projects/test-project/secrets/my-secret",
            body={"payload": {"data": expected_data}},
        )
        assert isinstance(version, SecretVersion)
        assert version.version_id == "1"
        assert version.state == "ENABLED"


class TestAccessSecretVersion:
    def test_access_secret_version_latest(self, mock_google_client):
        secret_data = b"my-secret-payload"
        encoded = base64.b64encode(secret_data).decode("utf-8")

        mock_request = mock.MagicMock()
        mock_access = (
            mock_google_client.projects.return_value.secrets.return_value.versions.return_value.access
        )
        mock_access.return_value = mock_request
        mock_request.execute.return_value = {
            "name": "projects/test-project/secrets/my-secret/versions/1",
            "payload": {"data": encoded},
        }

        service = SecretManagerService(project_id="test-project")
        result = service.access_secret_version("my-secret")

        mock_access.assert_called_once_with(
            name="projects/test-project/secrets/my-secret/versions/latest"
        )
        assert result == secret_data

    def test_access_secret_version_specific(self, mock_google_client):
        secret_data = b"version-2-payload"
        encoded = base64.b64encode(secret_data).decode("utf-8")

        mock_request = mock.MagicMock()
        mock_access = (
            mock_google_client.projects.return_value.secrets.return_value.versions.return_value.access
        )
        mock_access.return_value = mock_request
        mock_request.execute.return_value = {
            "name": "projects/test-project/secrets/my-secret/versions/2",
            "payload": {"data": encoded},
        }

        service = SecretManagerService(project_id="test-project")
        result = service.access_secret_version("my-secret", "2")

        mock_access.assert_called_once_with(
            name="projects/test-project/secrets/my-secret/versions/2"
        )
        assert result == secret_data


class TestListSecretVersions:
    def test_list_secret_versions(
        self, mock_google_client, sample_version_response
    ):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.secrets.return_value.versions.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "versions": [sample_version_response, sample_version_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.secrets.return_value.versions.return_value.list_next
        )
        mock_list_next.return_value = None

        service = SecretManagerService(project_id="test-project")
        versions = service.list_secret_versions("my-secret")

        mock_list.assert_called_once_with(
            parent="projects/test-project/secrets/my-secret"
        )
        assert len(versions) == 2
        assert isinstance(versions[0], SecretVersion)
        assert versions[0].version_id == "1"

    def test_list_secret_versions_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.secrets.return_value.versions.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value.secrets.return_value.versions.return_value.list_next
        )
        mock_list_next.return_value = None

        service = SecretManagerService(project_id="test-project")
        versions = service.list_secret_versions("my-secret")
        assert versions == []


class TestGetSecretVersion:
    def test_get_secret_version(
        self, mock_google_client, sample_version_response
    ):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.secrets.return_value.versions.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_version_response

        service = SecretManagerService(project_id="test-project")
        version = service.get_secret_version("my-secret", "1")

        mock_get.assert_called_once_with(
            name="projects/test-project/secrets/my-secret/versions/1"
        )
        assert isinstance(version, SecretVersion)
        assert version.version_id == "1"
        assert version.state == "ENABLED"


class TestDisableSecretVersion:
    def test_disable_secret_version(
        self, mock_google_client, sample_disabled_version_response
    ):
        mock_request = mock.MagicMock()
        mock_disable = (
            mock_google_client.projects.return_value.secrets.return_value.versions.return_value.disable
        )
        mock_disable.return_value = mock_request
        mock_request.execute.return_value = sample_disabled_version_response

        service = SecretManagerService(project_id="test-project")
        version = service.disable_secret_version("my-secret", "1")

        mock_disable.assert_called_once_with(
            name="projects/test-project/secrets/my-secret/versions/1",
            body={},
        )
        assert isinstance(version, SecretVersion)
        assert version.state == "DISABLED"


class TestEnableSecretVersion:
    def test_enable_secret_version(
        self, mock_google_client, sample_version_response
    ):
        mock_request = mock.MagicMock()
        mock_enable = (
            mock_google_client.projects.return_value.secrets.return_value.versions.return_value.enable
        )
        mock_enable.return_value = mock_request
        mock_request.execute.return_value = sample_version_response

        service = SecretManagerService(project_id="test-project")
        version = service.enable_secret_version("my-secret", "1")

        mock_enable.assert_called_once_with(
            name="projects/test-project/secrets/my-secret/versions/1",
            body={},
        )
        assert isinstance(version, SecretVersion)
        assert version.state == "ENABLED"


class TestDestroySecretVersion:
    def test_destroy_secret_version(
        self, mock_google_client, sample_destroyed_version_response
    ):
        mock_request = mock.MagicMock()
        mock_destroy = (
            mock_google_client.projects.return_value.secrets.return_value.versions.return_value.destroy
        )
        mock_destroy.return_value = mock_request
        mock_request.execute.return_value = (
            sample_destroyed_version_response
        )

        service = SecretManagerService(project_id="test-project")
        version = service.destroy_secret_version("my-secret", "1")

        mock_destroy.assert_called_once_with(
            name="projects/test-project/secrets/my-secret/versions/1",
            body={},
        )
        assert isinstance(version, SecretVersion)
        assert version.state == "DESTROYED"
        assert version.destroy_time is not None
