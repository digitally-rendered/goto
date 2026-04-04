"""Tests for the Apigee service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.apigee import ApigeeService
from gcpoto.models.apigee import (
    ApigeeOrganization,
    ApigeeEnvironment,
    ApigeeAPIProxy,
)
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
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
def sample_organization_response():
    """Sample Apigee Organization response."""
    return {
        "name": "organizations/my-org",
        "projectId": "test-project",
        "analyticsRegion": "us-central1",
        "authorizedNetwork": "projects/test-project/global/networks/default",
        "runtimeType": "CLOUD",
        "state": "ACTIVE",
        "labels": {"env": "production"},
        "createdAt": "2024-06-01T10:00:00.000Z",
        "lastModifiedAt": "2024-06-01T12:00:00.000Z",
    }


@pytest.fixture
def sample_environment_response():
    """Sample Apigee Environment response."""
    return {
        "name": "organizations/my-org/environments/test-env",
        "displayName": "Test Environment",
        "description": "A test environment",
        "state": "ACTIVE",
        "organization": "my-org",
        "labels": {"env": "test"},
        "createdAt": "2024-06-01T10:00:00.000Z",
        "lastModifiedAt": "2024-06-01T12:00:00.000Z",
    }


@pytest.fixture
def sample_api_proxy_response():
    """Sample Apigee API Proxy response."""
    return {
        "name": "organizations/my-org/apis/my-proxy",
        "revision": ["1", "2", "3"],
        "latestRevisionId": "3",
        "organization": "my-org",
        "labels": {"version": "v1"},
        "createdAt": "2024-06-01T10:00:00.000Z",
        "lastModifiedAt": "2024-06-01T12:00:00.000Z",
    }


@pytest.fixture
def service(mock_google_client):
    """Create an ApigeeService instance with mocked API client."""
    return ApigeeService(project_id="test-project")


# ------------------------------------------------------------------ #
#  Service init
# ------------------------------------------------------------------ #


class TestApigeeServiceInit:
    """Tests for ApigeeService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the Apigee service."""
        from googleapiclient.discovery import build

        svc = ApigeeService(project_id="test-project")

        assert svc.project_id == "test-project"
        assert svc.service_name == "apigee"
        assert svc.version == "v1"
        build.assert_called_once_with("apigee", "v1", credentials=None)

    def test_init_with_credentials(self, mock_google_client):
        """Test initializing with credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = ApigeeService(
                project_id="test-project",
                credentials_file="/path/to/creds.json",
            )
            assert svc.project_id == "test-project"
            mock_creds.assert_called_once()


# ------------------------------------------------------------------ #
#  Organization operations
# ------------------------------------------------------------------ #


class TestGetOrganization:
    """Tests for getting an organization."""

    def test_get_organization(self, service, sample_organization_response):
        """Test getting a specific organization."""
        mock_orgs = service.service.organizations.return_value
        mock_request = mock.MagicMock()
        mock_orgs.get.return_value = mock_request
        mock_request.execute.return_value = sample_organization_response

        org = service.get_organization("my-org")

        mock_orgs.get.assert_called_once_with(name="organizations/my-org")
        assert isinstance(org, ApigeeOrganization)
        assert org.id == "my-org"
        assert org.analytics_region == "us-central1"
        assert org.runtime_type == "CLOUD"
        assert org.state == "ACTIVE"

    def test_get_organization_not_found(self, service):
        """Test getting an organization that does not exist."""
        mock_orgs = service.service.organizations.return_value
        mock_request = mock.MagicMock()
        mock_orgs.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_organization("nonexistent")

    def test_get_organization_api_error(self, service):
        """Test getting an organization with an API error."""
        mock_orgs = service.service.organizations.return_value
        mock_request = mock.MagicMock()
        mock_orgs.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_organization("my-org")


# ------------------------------------------------------------------ #
#  Environment operations
# ------------------------------------------------------------------ #


class TestListEnvironments:
    """Tests for listing environments."""

    def test_list_environments(
        self, service, sample_environment_response
    ):
        """Test listing environments."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value

        # list returns a list of environment names
        mock_list_request = mock.MagicMock()
        mock_envs.list.return_value = mock_list_request
        mock_list_request.execute.return_value = ["test-env"]

        # get returns the full environment
        mock_get_request = mock.MagicMock()
        mock_envs.get.return_value = mock_get_request
        mock_get_request.execute.return_value = (
            sample_environment_response
        )

        envs = service.list_environments("my-org")

        mock_envs.list.assert_called_once_with(
            parent="organizations/my-org"
        )
        assert len(envs) == 1
        assert isinstance(envs[0], ApigeeEnvironment)
        assert envs[0].id == "test-env"

    def test_list_environments_empty(self, service):
        """Test listing environments when none exist."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value

        mock_list_request = mock.MagicMock()
        mock_envs.list.return_value = mock_list_request
        mock_list_request.execute.return_value = []

        envs = service.list_environments("my-org")
        assert len(envs) == 0


class TestGetEnvironment:
    """Tests for getting an environment."""

    def test_get_environment(self, service, sample_environment_response):
        """Test getting a specific environment."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_request = mock.MagicMock()
        mock_envs.get.return_value = mock_request
        mock_request.execute.return_value = sample_environment_response

        env = service.get_environment("my-org", "test-env")

        mock_envs.get.assert_called_once_with(
            name="organizations/my-org/environments/test-env"
        )
        assert isinstance(env, ApigeeEnvironment)
        assert env.id == "test-env"
        assert env.display_name == "Test Environment"
        assert env.description == "A test environment"

    def test_get_environment_not_found(self, service):
        """Test getting an environment that does not exist."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_request = mock.MagicMock()
        mock_envs.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_environment("my-org", "nonexistent")

    def test_get_environment_api_error(self, service):
        """Test getting an environment with an API error."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_request = mock.MagicMock()
        mock_envs.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_environment("my-org", "test-env")


class TestCreateEnvironment:
    """Tests for creating an environment."""

    def test_create_environment(
        self, service, sample_environment_response
    ):
        """Test creating an environment."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_request = mock.MagicMock()
        mock_envs.create.return_value = mock_request
        mock_request.execute.return_value = sample_environment_response

        env = service.create_environment(
            org_name="my-org",
            env_name="test-env",
            description="A test environment",
        )

        mock_envs.create.assert_called_once_with(
            parent="organizations/my-org",
            body={"name": "test-env", "description": "A test environment"},
        )
        assert isinstance(env, ApigeeEnvironment)
        assert env.id == "test-env"

    def test_create_environment_minimal(
        self, service, sample_environment_response
    ):
        """Test creating an environment with minimal parameters."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_request = mock.MagicMock()
        mock_envs.create.return_value = mock_request
        mock_request.execute.return_value = sample_environment_response

        service.create_environment(
            org_name="my-org", env_name="test-env"
        )

        mock_envs.create.assert_called_once_with(
            parent="organizations/my-org",
            body={"name": "test-env"},
        )

    def test_create_environment_already_exists(self, service):
        """Test creating an environment that already exists."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_request = mock.MagicMock()
        mock_envs.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_environment(
                org_name="my-org", env_name="test-env"
            )

    def test_create_environment_api_error(self, service):
        """Test creating an environment with an API error."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_request = mock.MagicMock()
        mock_envs.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_environment(
                org_name="my-org", env_name="test-env"
            )


class TestDeleteEnvironment:
    """Tests for deleting an environment."""

    def test_delete_environment(self, service):
        """Test deleting an environment."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_request = mock.MagicMock()
        mock_envs.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_environment("my-org", "test-env")

        mock_envs.delete.assert_called_once_with(
            name="organizations/my-org/environments/test-env"
        )
        assert result is True

    def test_delete_environment_not_found(self, service):
        """Test deleting an environment that does not exist."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_request = mock.MagicMock()
        mock_envs.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_environment("my-org", "nonexistent")


# ------------------------------------------------------------------ #
#  API Proxy operations
# ------------------------------------------------------------------ #


class TestListApiProxies:
    """Tests for listing API proxies."""

    def test_list_api_proxies(self, service, sample_api_proxy_response):
        """Test listing API proxies."""
        mock_orgs = service.service.organizations.return_value
        mock_apis = mock_orgs.apis.return_value
        mock_request = mock.MagicMock()
        mock_apis.list.return_value = mock_request
        mock_request.execute.return_value = {
            "proxies": [sample_api_proxy_response]
        }

        proxies = service.list_api_proxies("my-org")

        mock_apis.list.assert_called_once_with(
            parent="organizations/my-org"
        )
        assert len(proxies) == 1
        assert isinstance(proxies[0], ApigeeAPIProxy)
        assert proxies[0].id == "my-proxy"
        assert proxies[0].revision == ["1", "2", "3"]
        assert proxies[0].latest_revision_id == "3"

    def test_list_api_proxies_empty(self, service):
        """Test listing API proxies when none exist."""
        mock_orgs = service.service.organizations.return_value
        mock_apis = mock_orgs.apis.return_value
        mock_request = mock.MagicMock()
        mock_apis.list.return_value = mock_request
        mock_request.execute.return_value = {"proxies": []}

        proxies = service.list_api_proxies("my-org")
        assert len(proxies) == 0


class TestGetApiProxy:
    """Tests for getting an API proxy."""

    def test_get_api_proxy(self, service, sample_api_proxy_response):
        """Test getting a specific API proxy."""
        mock_orgs = service.service.organizations.return_value
        mock_apis = mock_orgs.apis.return_value
        mock_request = mock.MagicMock()
        mock_apis.get.return_value = mock_request
        mock_request.execute.return_value = sample_api_proxy_response

        proxy = service.get_api_proxy("my-org", "my-proxy")

        mock_apis.get.assert_called_once_with(
            name="organizations/my-org/apis/my-proxy"
        )
        assert isinstance(proxy, ApigeeAPIProxy)
        assert proxy.id == "my-proxy"
        assert proxy.latest_revision_id == "3"

    def test_get_api_proxy_not_found(self, service):
        """Test getting an API proxy that does not exist."""
        mock_orgs = service.service.organizations.return_value
        mock_apis = mock_orgs.apis.return_value
        mock_request = mock.MagicMock()
        mock_apis.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_api_proxy("my-org", "nonexistent")

    def test_get_api_proxy_api_error(self, service):
        """Test getting an API proxy with an API error."""
        mock_orgs = service.service.organizations.return_value
        mock_apis = mock_orgs.apis.return_value
        mock_request = mock.MagicMock()
        mock_apis.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_api_proxy("my-org", "my-proxy")


class TestCreateApiProxy:
    """Tests for creating an API proxy."""

    def test_create_api_proxy(self, service, sample_api_proxy_response):
        """Test creating an API proxy."""
        mock_orgs = service.service.organizations.return_value
        mock_apis = mock_orgs.apis.return_value
        mock_request = mock.MagicMock()
        mock_apis.create.return_value = mock_request
        mock_request.execute.return_value = sample_api_proxy_response

        proxy = service.create_api_proxy(
            org_name="my-org",
            proxy_name="my-proxy",
            proxy_bundle=b"proxy-bundle-data",
        )

        mock_apis.create.assert_called_once_with(
            parent="organizations/my-org",
            name="my-proxy",
            body={
                "name": "my-proxy",
                "content": b"proxy-bundle-data",
            },
        )
        assert isinstance(proxy, ApigeeAPIProxy)
        assert proxy.id == "my-proxy"

    def test_create_api_proxy_already_exists(self, service):
        """Test creating an API proxy that already exists."""
        mock_orgs = service.service.organizations.return_value
        mock_apis = mock_orgs.apis.return_value
        mock_request = mock.MagicMock()
        mock_apis.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_api_proxy(
                org_name="my-org",
                proxy_name="my-proxy",
                proxy_bundle=b"data",
            )

    def test_create_api_proxy_api_error(self, service):
        """Test creating an API proxy with an API error."""
        mock_orgs = service.service.organizations.return_value
        mock_apis = mock_orgs.apis.return_value
        mock_request = mock.MagicMock()
        mock_apis.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_api_proxy(
                org_name="my-org",
                proxy_name="my-proxy",
                proxy_bundle=b"data",
            )


class TestDeleteApiProxy:
    """Tests for deleting an API proxy."""

    def test_delete_api_proxy(self, service):
        """Test deleting an API proxy."""
        mock_orgs = service.service.organizations.return_value
        mock_apis = mock_orgs.apis.return_value
        mock_request = mock.MagicMock()
        mock_apis.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_api_proxy("my-org", "my-proxy")

        mock_apis.delete.assert_called_once_with(
            name="organizations/my-org/apis/my-proxy"
        )
        assert result is True

    def test_delete_api_proxy_not_found(self, service):
        """Test deleting an API proxy that does not exist."""
        mock_orgs = service.service.organizations.return_value
        mock_apis = mock_orgs.apis.return_value
        mock_request = mock.MagicMock()
        mock_apis.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_api_proxy("my-org", "nonexistent")


# ------------------------------------------------------------------ #
#  Deployment operations
# ------------------------------------------------------------------ #


class TestDeployApiProxy:
    """Tests for deploying an API proxy."""

    def test_deploy_api_proxy(self, service):
        """Test deploying an API proxy revision."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_apis = mock_envs.apis.return_value
        mock_revisions = mock_apis.revisions.return_value
        mock_request = mock.MagicMock()
        mock_revisions.deploy.return_value = mock_request
        mock_request.execute.return_value = {
            "environment": "test-env",
            "apiProxy": "my-proxy",
            "revision": "1",
            "deployStartTime": "2024-06-01T10:00:00.000Z",
        }

        result = service.deploy_api_proxy(
            "my-org", "test-env", "my-proxy", "1"
        )

        mock_revisions.deploy.assert_called_once_with(
            name="organizations/my-org/environments/test-env/apis/my-proxy/revisions/1"
        )
        assert result["apiProxy"] == "my-proxy"

    def test_deploy_api_proxy_not_found(self, service):
        """Test deploying an API proxy that does not exist."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_apis = mock_envs.apis.return_value
        mock_revisions = mock_apis.revisions.return_value
        mock_request = mock.MagicMock()
        mock_revisions.deploy.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.deploy_api_proxy(
                "my-org", "test-env", "nonexistent", "1"
            )

    def test_deploy_api_proxy_api_error(self, service):
        """Test deploying an API proxy with an API error."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_apis = mock_envs.apis.return_value
        mock_revisions = mock_apis.revisions.return_value
        mock_request = mock.MagicMock()
        mock_revisions.deploy.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.deploy_api_proxy(
                "my-org", "test-env", "my-proxy", "1"
            )


class TestUndeployApiProxy:
    """Tests for undeploying an API proxy."""

    def test_undeploy_api_proxy(self, service):
        """Test undeploying an API proxy revision."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_apis = mock_envs.apis.return_value
        mock_revisions = mock_apis.revisions.return_value
        mock_request = mock.MagicMock()
        mock_revisions.undeploy.return_value = mock_request
        mock_request.execute.return_value = {
            "environment": "test-env",
            "apiProxy": "my-proxy",
            "revision": "1",
        }

        result = service.undeploy_api_proxy(
            "my-org", "test-env", "my-proxy", "1"
        )

        mock_revisions.undeploy.assert_called_once_with(
            name="organizations/my-org/environments/test-env/apis/my-proxy/revisions/1"
        )
        assert result["apiProxy"] == "my-proxy"

    def test_undeploy_api_proxy_not_found(self, service):
        """Test undeploying an API proxy that does not exist."""
        mock_orgs = service.service.organizations.return_value
        mock_envs = mock_orgs.environments.return_value
        mock_apis = mock_envs.apis.return_value
        mock_revisions = mock_apis.revisions.return_value
        mock_request = mock.MagicMock()
        mock_revisions.undeploy.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.undeploy_api_proxy(
                "my-org", "test-env", "nonexistent", "1"
            )


# ------------------------------------------------------------------ #
#  Model tests
# ------------------------------------------------------------------ #


class TestApigeeOrganizationModel:
    """Tests for the ApigeeOrganization model."""

    def test_from_api_response(self, sample_organization_response):
        """Test creating an ApigeeOrganization from an API response."""
        org = ApigeeOrganization.from_api_response(
            sample_organization_response
        )

        assert org.id == "my-org"
        assert org.name == "organizations/my-org"
        assert org.type == "apigee.organization"
        assert org.project == "test-project"
        assert org.analytics_region == "us-central1"
        assert org.runtime_type == "CLOUD"
        assert org.state == "ACTIVE"
        assert org.labels == {"env": "production"}

    def test_from_api_response_minimal(self):
        """Test creating an ApigeeOrganization from a minimal response."""
        org = ApigeeOrganization.from_api_response(
            {"name": "simple-org"}
        )

        assert org.id == "simple-org"
        assert org.name == "simple-org"
        assert org.analytics_region is None
        assert org.runtime_type is None
        assert org.state is None

    def test_get_tag(self, sample_organization_response):
        """Test the get_tag method."""
        org = ApigeeOrganization.from_api_response(
            sample_organization_response
        )

        assert org.get_tag("env") == "production"
        assert org.get_tag("missing") == ""
        assert org.get_tag("missing", "default") == "default"


class TestApigeeEnvironmentModel:
    """Tests for the ApigeeEnvironment model."""

    def test_from_api_response(self, sample_environment_response):
        """Test creating an ApigeeEnvironment from an API response."""
        env = ApigeeEnvironment.from_api_response(
            sample_environment_response
        )

        assert env.id == "test-env"
        assert env.name == "organizations/my-org/environments/test-env"
        assert env.type == "apigee.environment"
        assert env.display_name == "Test Environment"
        assert env.description == "A test environment"
        assert env.state == "ACTIVE"

    def test_from_api_response_minimal(self):
        """Test creating an ApigeeEnvironment from a minimal response."""
        env = ApigeeEnvironment.from_api_response(
            {"name": "simple-env"}
        )

        assert env.id == "simple-env"
        assert env.display_name is None
        assert env.description is None
        assert env.state is None


class TestApigeeAPIProxyModel:
    """Tests for the ApigeeAPIProxy model."""

    def test_from_api_response(self, sample_api_proxy_response):
        """Test creating an ApigeeAPIProxy from an API response."""
        proxy = ApigeeAPIProxy.from_api_response(
            sample_api_proxy_response
        )

        assert proxy.id == "my-proxy"
        assert proxy.name == "organizations/my-org/apis/my-proxy"
        assert proxy.type == "apigee.apiProxy"
        assert proxy.revision == ["1", "2", "3"]
        assert proxy.latest_revision_id == "3"

    def test_from_api_response_minimal(self):
        """Test creating an ApigeeAPIProxy from a minimal response."""
        proxy = ApigeeAPIProxy.from_api_response(
            {"name": "simple-proxy"}
        )

        assert proxy.id == "simple-proxy"
        assert proxy.revision is None
        assert proxy.latest_revision_id is None
