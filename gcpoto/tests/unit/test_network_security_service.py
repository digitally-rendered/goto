"""Tests for Network Security service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.network_security import NetworkSecurityService
from gcpoto.models.network_security import ServerTLSPolicy, AuthorizationPolicy
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
def sample_server_tls_policy_response():
    """Sample Server TLS Policy API response."""
    return {
        "name": "projects/test-project/locations/global/serverTlsPolicies/my-policy",
        "description": "Test server TLS policy",
        "allowOpen": False,
        "serverCertificate": {
            "certificateProviderInstance": {
                "pluginInstance": "google_cloud_private_spiffe",
            }
        },
        "mtlsPolicy": {
            "clientValidationCa": [
                {
                    "certificateProviderInstance": {
                        "pluginInstance": "google_cloud_private_spiffe",
                    }
                }
            ]
        },
        "labels": {"env": "test"},
        "createTime": "2024-01-15T10:30:00.000Z",
        "updateTime": "2024-01-16T12:00:00.000Z",
    }


@pytest.fixture
def sample_authorization_policy_response():
    """Sample Authorization Policy API response."""
    return {
        "name": "projects/test-project/locations/global/authorizationPolicies/my-auth-policy",
        "description": "Test authorization policy",
        "action": "ALLOW",
        "rules": [
            {
                "sources": [{"principals": ["spiffe://example.com/sa/test"]}],
                "destinations": [{"hosts": ["example.com"], "ports": [443]}],
            }
        ],
        "labels": {"team": "security"},
        "createTime": "2024-01-15T10:30:00.000Z",
        "updateTime": "2024-01-16T12:00:00.000Z",
    }


@pytest.fixture
def service(mock_google_client):
    """Create a NetworkSecurityService instance with mocked API client."""
    svc = NetworkSecurityService(project_id="test-project")
    return svc


class TestNetworkSecurityServiceInit:
    """Tests for NetworkSecurityService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the NetworkSecurityService."""
        from googleapiclient.discovery import build

        service = NetworkSecurityService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "networksecurity"
        assert service.version == "v1"
        build.assert_called_once_with(
            "networksecurity", "v1", credentials=None
        )


class TestListServerTlsPolicies:
    """Tests for listing server TLS policies."""

    def test_list_server_tls_policies(
        self, service, sample_server_tls_policy_response
    ):
        """Test listing server TLS policies."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .serverTlsPolicies.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "serverTlsPolicies": [sample_server_tls_policy_response]
        }

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .serverTlsPolicies.return_value.list_next
        )
        mock_list_next.return_value = None

        policies = service.list_server_tls_policies("global")

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/global"
        )
        assert len(policies) == 1
        assert isinstance(policies[0], ServerTLSPolicy)
        assert policies[0].allow_open is False

    def test_list_server_tls_policies_empty(self, service):
        """Test listing server TLS policies when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .serverTlsPolicies.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"serverTlsPolicies": []}

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .serverTlsPolicies.return_value.list_next
        )
        mock_list_next.return_value = None

        policies = service.list_server_tls_policies("global")

        assert len(policies) == 0


class TestGetServerTlsPolicy:
    """Tests for getting a server TLS policy."""

    def test_get_server_tls_policy(
        self, service, sample_server_tls_policy_response
    ):
        """Test getting a specific server TLS policy."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .serverTlsPolicies.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = (
            sample_server_tls_policy_response
        )

        policy = service.get_server_tls_policy("global", "my-policy")

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/global/serverTlsPolicies/my-policy"
        )
        assert isinstance(policy, ServerTLSPolicy)
        assert policy.description == "Test server TLS policy"

    def test_get_server_tls_policy_not_found(self, service):
        """Test getting a server TLS policy that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .serverTlsPolicies.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_server_tls_policy("global", "missing-policy")


class TestCreateServerTlsPolicy:
    """Tests for creating a server TLS policy."""

    def test_create_server_tls_policy(
        self, service, sample_server_tls_policy_response
    ):
        """Test creating a server TLS policy."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .serverTlsPolicies.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = (
            sample_server_tls_policy_response
        )

        policy = service.create_server_tls_policy(
            location="global",
            policy_name="my-policy",
            allow_open=False,
            server_certificate={
                "certificateProviderInstance": {
                    "pluginInstance": "google_cloud_private_spiffe",
                }
            },
        )

        assert isinstance(policy, ServerTLSPolicy)
        assert policy.allow_open is False

    def test_create_server_tls_policy_api_error(self, service):
        """Test creating a server TLS policy with an API error."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .serverTlsPolicies.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_server_tls_policy(
                location="global", policy_name="my-policy"
            )


class TestDeleteServerTlsPolicy:
    """Tests for deleting a server TLS policy."""

    def test_delete_server_tls_policy(self, service):
        """Test deleting a server TLS policy."""
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .serverTlsPolicies.return_value.delete
        )
        mock_delete.return_value.execute.return_value = {}

        result = service.delete_server_tls_policy("global", "my-policy")

        mock_delete.assert_called_once_with(
            name="projects/test-project/locations/global/serverTlsPolicies/my-policy"
        )
        assert result is True

    def test_delete_server_tls_policy_not_found(self, service):
        """Test deleting a server TLS policy that does not exist."""
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .serverTlsPolicies.return_value.delete
        )
        mock_delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_server_tls_policy("global", "missing-policy")


class TestListAuthorizationPolicies:
    """Tests for listing authorization policies."""

    def test_list_authorization_policies(
        self, service, sample_authorization_policy_response
    ):
        """Test listing authorization policies."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .authorizationPolicies.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "authorizationPolicies": [
                sample_authorization_policy_response
            ]
        }

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .authorizationPolicies.return_value.list_next
        )
        mock_list_next.return_value = None

        policies = service.list_authorization_policies("global")

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/global"
        )
        assert len(policies) == 1
        assert isinstance(policies[0], AuthorizationPolicy)
        assert policies[0].action == "ALLOW"

    def test_list_authorization_policies_empty(self, service):
        """Test listing authorization policies when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value
            .locations.return_value
            .authorizationPolicies.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"authorizationPolicies": []}

        mock_list_next = (
            service.service.projects.return_value
            .locations.return_value
            .authorizationPolicies.return_value.list_next
        )
        mock_list_next.return_value = None

        policies = service.list_authorization_policies("global")

        assert len(policies) == 0


class TestGetAuthorizationPolicy:
    """Tests for getting an authorization policy."""

    def test_get_authorization_policy(
        self, service, sample_authorization_policy_response
    ):
        """Test getting a specific authorization policy."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .authorizationPolicies.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = (
            sample_authorization_policy_response
        )

        policy = service.get_authorization_policy(
            "global", "my-auth-policy"
        )

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/global/authorizationPolicies/my-auth-policy"
        )
        assert isinstance(policy, AuthorizationPolicy)
        assert policy.action == "ALLOW"
        assert policy.description == "Test authorization policy"

    def test_get_authorization_policy_not_found(self, service):
        """Test getting an authorization policy that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value
            .locations.return_value
            .authorizationPolicies.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_authorization_policy("global", "missing-policy")


class TestCreateAuthorizationPolicy:
    """Tests for creating an authorization policy."""

    def test_create_authorization_policy(
        self, service, sample_authorization_policy_response
    ):
        """Test creating an authorization policy."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .authorizationPolicies.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = (
            sample_authorization_policy_response
        )

        policy = service.create_authorization_policy(
            location="global",
            policy_name="my-auth-policy",
            action="ALLOW",
            rules=[
                {
                    "sources": [
                        {"principals": ["spiffe://example.com/sa/test"]}
                    ],
                    "destinations": [
                        {"hosts": ["example.com"], "ports": [443]}
                    ],
                }
            ],
        )

        assert isinstance(policy, AuthorizationPolicy)
        assert policy.action == "ALLOW"

    def test_create_authorization_policy_api_error(self, service):
        """Test creating an authorization policy with an API error."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value
            .locations.return_value
            .authorizationPolicies.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_authorization_policy(
                location="global",
                policy_name="my-auth-policy",
                action="DENY",
            )


class TestDeleteAuthorizationPolicy:
    """Tests for deleting an authorization policy."""

    def test_delete_authorization_policy(self, service):
        """Test deleting an authorization policy."""
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .authorizationPolicies.return_value.delete
        )
        mock_delete.return_value.execute.return_value = {}

        result = service.delete_authorization_policy(
            "global", "my-auth-policy"
        )

        mock_delete.assert_called_once_with(
            name="projects/test-project/locations/global/authorizationPolicies/my-auth-policy"
        )
        assert result is True

    def test_delete_authorization_policy_not_found(self, service):
        """Test deleting an authorization policy that does not exist."""
        mock_delete = (
            service.service.projects.return_value
            .locations.return_value
            .authorizationPolicies.return_value.delete
        )
        mock_delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_authorization_policy(
                "global", "missing-policy"
            )


class TestServerTlsPolicyModel:
    """Tests for the ServerTLSPolicy model."""

    def test_from_api_response(self, sample_server_tls_policy_response):
        """Test creating a ServerTLSPolicy from an API response."""
        policy = ServerTLSPolicy.from_api_response(
            sample_server_tls_policy_response
        )

        assert policy.name == "projects/test-project/locations/global/serverTlsPolicies/my-policy"
        assert policy.description == "Test server TLS policy"
        assert policy.allow_open is False
        assert policy.server_certificate is not None
        assert policy.mtls_policy is not None
        assert policy.type == "networksecurity.serverTlsPolicy"
        assert policy.location == "global"

    def test_from_api_response_minimal(self):
        """Test creating a ServerTLSPolicy from a minimal API response."""
        policy = ServerTLSPolicy.from_api_response(
            {"name": "projects/test/locations/global/serverTlsPolicies/p1"}
        )

        assert policy.allow_open is False
        assert policy.server_certificate is None
        assert policy.mtls_policy is None

    def test_get_tag(self, sample_server_tls_policy_response):
        """Test get_tag method."""
        policy = ServerTLSPolicy.from_api_response(
            sample_server_tls_policy_response
        )

        assert policy.get_tag("env") == "test"
        assert policy.get_tag("missing", "default") == "default"


class TestAuthorizationPolicyModel:
    """Tests for the AuthorizationPolicy model."""

    def test_from_api_response(
        self, sample_authorization_policy_response
    ):
        """Test creating an AuthorizationPolicy from an API response."""
        policy = AuthorizationPolicy.from_api_response(
            sample_authorization_policy_response
        )

        assert policy.name == "projects/test-project/locations/global/authorizationPolicies/my-auth-policy"
        assert policy.description == "Test authorization policy"
        assert policy.action == "ALLOW"
        assert policy.rules is not None
        assert len(policy.rules) == 1
        assert policy.type == "networksecurity.authorizationPolicy"

    def test_from_api_response_minimal(self):
        """Test creating an AuthorizationPolicy from a minimal response."""
        policy = AuthorizationPolicy.from_api_response(
            {"name": "projects/test/locations/global/authorizationPolicies/p1"}
        )

        assert policy.action == "ALLOW"
        assert policy.rules is None

    def test_get_tag(self, sample_authorization_policy_response):
        """Test get_tag method."""
        policy = AuthorizationPolicy.from_api_response(
            sample_authorization_policy_response
        )

        assert policy.get_tag("team") == "security"
        assert policy.get_tag("missing", "default") == "default"
