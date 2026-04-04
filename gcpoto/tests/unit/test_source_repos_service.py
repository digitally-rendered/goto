"""Tests for Cloud Source Repositories service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.source_repos import SourceReposService
from gcpoto.models.source_repos import Repo
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
)


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_service


@pytest.fixture
def sample_repo_response():
    """Sample Repo API response."""
    return {
        "name": "projects/test-project/repos/my-repo",
        "size": 1024,
        "url": "https://source.developers.google.com/p/test-project/r/my-repo",
        "mirrorConfig": {
            "url": "https://github.com/example/repo.git",
            "webhookId": "webhook-123",
            "deployKeyId": "key-456",
        },
        "pubsubConfigs": {
            "projects/test-project/topics/my-topic": {
                "topic": "projects/test-project/topics/my-topic",
                "messageFormat": "JSON",
            }
        },
    }


@pytest.fixture
def sample_iam_policy():
    """Sample IAM policy response."""
    return {
        "version": 1,
        "bindings": [
            {
                "role": "roles/source.reader",
                "members": ["user:test@example.com"],
            }
        ],
        "etag": "BwXyz123",
    }


@pytest.fixture
def service(mock_google_client):
    """Create a SourceReposService instance with mocked API client."""
    svc = SourceReposService(project_id="test-project")
    return svc


class TestSourceReposServiceInit:
    """Tests for SourceReposService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the SourceReposService."""
        from googleapiclient.discovery import build

        service = SourceReposService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "sourcerepo"
        assert service.version == "v1"
        build.assert_called_once_with(
            "sourcerepo", "v1", credentials=None
        )


class TestListRepos:
    """Tests for listing repositories."""

    def test_list_repos(self, service, sample_repo_response):
        """Test listing repositories."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value.repos.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "repos": [sample_repo_response]
        }

        mock_list_next = (
            service.service.projects.return_value.repos.return_value.list_next
        )
        mock_list_next.return_value = None

        repos = service.list_repos()

        mock_list.assert_called_once_with(name="projects/test-project")
        assert len(repos) == 1
        assert isinstance(repos[0], Repo)
        assert repos[0].size == 1024

    def test_list_repos_empty(self, service):
        """Test listing repositories when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value.repos.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"repos": []}

        mock_list_next = (
            service.service.projects.return_value.repos.return_value.list_next
        )
        mock_list_next.return_value = None

        repos = service.list_repos()

        assert len(repos) == 0


class TestGetRepo:
    """Tests for getting a repository."""

    def test_get_repo(self, service, sample_repo_response):
        """Test getting a specific repository."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value.repos.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_repo_response

        repo = service.get_repo("my-repo")

        mock_get.assert_called_once_with(
            name="projects/test-project/repos/my-repo"
        )
        assert isinstance(repo, Repo)
        assert repo.url == "https://source.developers.google.com/p/test-project/r/my-repo"

    def test_get_repo_not_found(self, service):
        """Test getting a repository that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value.repos.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_repo("missing-repo")


class TestCreateRepo:
    """Tests for creating a repository."""

    def test_create_repo(self, service, sample_repo_response):
        """Test creating a repository."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value.repos.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_repo_response

        repo = service.create_repo("my-repo")

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            body={"name": "projects/test-project/repos/my-repo"},
        )
        assert isinstance(repo, Repo)
        assert repo.size == 1024

    def test_create_repo_api_error(self, service):
        """Test creating a repository with an API error."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value.repos.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_repo("my-repo")


class TestDeleteRepo:
    """Tests for deleting a repository."""

    def test_delete_repo(self, service):
        """Test deleting a repository."""
        mock_delete = (
            service.service.projects.return_value.repos.return_value.delete
        )
        mock_delete.return_value.execute.return_value = {}

        result = service.delete_repo("my-repo")

        mock_delete.assert_called_once_with(
            name="projects/test-project/repos/my-repo"
        )
        assert result is True

    def test_delete_repo_not_found(self, service):
        """Test deleting a repository that does not exist."""
        mock_delete = (
            service.service.projects.return_value.repos.return_value.delete
        )
        mock_delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_repo("missing-repo")


class TestGetIamPolicy:
    """Tests for getting IAM policy."""

    def test_get_iam_policy(self, service, sample_iam_policy):
        """Test getting IAM policy for a repository."""
        mock_request = mock.MagicMock()
        mock_get_iam = (
            service.service.projects.return_value
            .repos.return_value.getIamPolicy
        )
        mock_get_iam.return_value = mock_request
        mock_request.execute.return_value = sample_iam_policy

        policy = service.get_iam_policy("my-repo")

        mock_get_iam.assert_called_once_with(
            resource="projects/test-project/repos/my-repo"
        )
        assert policy["version"] == 1
        assert len(policy["bindings"]) == 1

    def test_get_iam_policy_not_found(self, service):
        """Test getting IAM policy for a repository that does not exist."""
        mock_request = mock.MagicMock()
        mock_get_iam = (
            service.service.projects.return_value
            .repos.return_value.getIamPolicy
        )
        mock_get_iam.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_iam_policy("missing-repo")


class TestSetIamPolicy:
    """Tests for setting IAM policy."""

    def test_set_iam_policy(self, service, sample_iam_policy):
        """Test setting IAM policy for a repository."""
        mock_request = mock.MagicMock()
        mock_set_iam = (
            service.service.projects.return_value
            .repos.return_value.setIamPolicy
        )
        mock_set_iam.return_value = mock_request
        mock_request.execute.return_value = sample_iam_policy

        policy = service.set_iam_policy("my-repo", sample_iam_policy)

        mock_set_iam.assert_called_once_with(
            resource="projects/test-project/repos/my-repo",
            body={"policy": sample_iam_policy},
        )
        assert policy["version"] == 1

    def test_set_iam_policy_not_found(self, service):
        """Test setting IAM policy for a repository that does not exist."""
        mock_request = mock.MagicMock()
        mock_set_iam = (
            service.service.projects.return_value
            .repos.return_value.setIamPolicy
        )
        mock_set_iam.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.set_iam_policy("missing-repo", {"bindings": []})

    def test_set_iam_policy_api_error(self, service):
        """Test setting IAM policy with an API error."""
        mock_request = mock.MagicMock()
        mock_set_iam = (
            service.service.projects.return_value
            .repos.return_value.setIamPolicy
        )
        mock_set_iam.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.set_iam_policy("my-repo", {"bindings": []})


class TestRepoModel:
    """Tests for the Repo model."""

    def test_from_api_response(self, sample_repo_response):
        """Test creating a Repo from an API response."""
        repo = Repo.from_api_response(sample_repo_response)

        assert repo.name == "projects/test-project/repos/my-repo"
        assert repo.size == 1024
        assert repo.url == "https://source.developers.google.com/p/test-project/r/my-repo"
        assert repo.mirror_config is not None
        assert repo.pubsub_configs is not None
        assert repo.type == "sourcerepo.repo"
        assert repo.project == "test-project"

    def test_from_api_response_minimal(self):
        """Test creating a Repo from a minimal API response."""
        repo = Repo.from_api_response(
            {"name": "projects/test/repos/my-repo"}
        )

        assert repo.size is None
        assert repo.url is None
        assert repo.mirror_config is None
        assert repo.pubsub_configs is None
