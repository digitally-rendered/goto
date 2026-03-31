"""Tests for Binary Authorization service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.binary_auth import BinaryAuthService
from gcpoto.models.binary_auth import Policy, Attestor
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
def sample_policy_response():
    """Sample Binary Authorization policy API response."""
    return {
        "name": "projects/test-project/policy",
        "globalPolicyEvaluationMode": "ENABLE",
        "defaultAdmissionRule": {
            "evaluationMode": "ALWAYS_ALLOW",
            "enforcementMode": "ENFORCED_BLOCK_AND_AUDIT_LOG",
        },
        "clusterAdmissionRules": {
            "us-central1-a.prod-cluster": {
                "evaluationMode": "REQUIRE_ATTESTATION",
                "enforcementMode": "ENFORCED_BLOCK_AND_AUDIT_LOG",
                "requireAttestationsBy": [
                    "projects/test-project/attestors/build-attestor"
                ],
            }
        },
        "updateTime": "2024-01-15T10:30:00.000Z",
    }


@pytest.fixture
def sample_attestor_response():
    """Sample Binary Authorization attestor API response."""
    return {
        "name": "projects/test-project/attestors/build-attestor",
        "description": "Build pipeline attestor",
        "userOwnedGrafeasNote": {
            "noteReference": "projects/test-project/notes/build-note",
            "publicKeys": [
                {
                    "id": "key-1",
                    "asciiArmoredPgpPublicKey": "-----BEGIN PGP PUBLIC KEY BLOCK-----",
                }
            ],
        },
        "createTime": "2024-01-10T08:00:00.000Z",
        "updateTime": "2024-01-15T10:30:00.000Z",
    }


@pytest.fixture
def service(mock_google_client):
    """Create a BinaryAuthService instance with mocked API client."""
    svc = BinaryAuthService(project_id="test-project")
    return svc


class TestBinaryAuthServiceInit:
    """Tests for BinaryAuthService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the BinaryAuthService."""
        from googleapiclient.discovery import build

        service = BinaryAuthService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "binaryauthorization"
        assert service.version == "v1"
        build.assert_called_once_with(
            "binaryauthorization", "v1", credentials=None
        )


class TestGetPolicy:
    """Tests for getting the Binary Authorization policy."""

    def test_get_policy(self, service, sample_policy_response):
        """Test getting the project policy."""
        mock_request = mock.MagicMock()
        mock_get_policy = (
            service.service.projects.return_value.getPolicy
        )
        mock_get_policy.return_value = mock_request
        mock_request.execute.return_value = sample_policy_response

        policy = service.get_policy()

        mock_get_policy.assert_called_once_with(
            name="projects/test-project/policy"
        )
        assert isinstance(policy, Policy)
        assert policy.global_policy_evaluation_mode == "ENABLE"
        assert policy.default_admission_rule["evaluationMode"] == "ALWAYS_ALLOW"
        assert policy.cluster_admission_rules is not None

    def test_get_policy_not_found(self, service):
        """Test getting a policy that does not exist."""
        mock_request = mock.MagicMock()
        mock_get_policy = (
            service.service.projects.return_value.getPolicy
        )
        mock_get_policy.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_policy()


class TestUpdatePolicy:
    """Tests for updating the Binary Authorization policy."""

    def test_update_policy(self, service, sample_policy_response):
        """Test updating the project policy."""
        mock_request = mock.MagicMock()
        mock_update_policy = (
            service.service.projects.return_value.updatePolicy
        )
        mock_update_policy.return_value = mock_request
        mock_request.execute.return_value = sample_policy_response

        policy_body = {
            "defaultAdmissionRule": {
                "evaluationMode": "ALWAYS_ALLOW",
                "enforcementMode": "ENFORCED_BLOCK_AND_AUDIT_LOG",
            }
        }
        policy = service.update_policy(policy_body)

        mock_update_policy.assert_called_once_with(
            name="projects/test-project/policy",
            body=policy_body,
        )
        assert isinstance(policy, Policy)

    def test_update_policy_api_error(self, service):
        """Test updating the policy with an API error."""
        mock_request = mock.MagicMock()
        mock_update_policy = (
            service.service.projects.return_value.updatePolicy
        )
        mock_update_policy.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.update_policy({"defaultAdmissionRule": {}})


class TestListAttestors:
    """Tests for listing attestors."""

    def test_list_attestors(self, service, sample_attestor_response):
        """Test listing attestors."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value.attestors.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "attestors": [sample_attestor_response]
        }

        mock_list_next = (
            service.service.projects.return_value.attestors.return_value.list_next
        )
        mock_list_next.return_value = None

        attestors = service.list_attestors()

        mock_list.assert_called_once_with(parent="projects/test-project")
        assert len(attestors) == 1
        assert isinstance(attestors[0], Attestor)
        assert attestors[0].description == "Build pipeline attestor"

    def test_list_attestors_empty(self, service):
        """Test listing attestors when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            service.service.projects.return_value.attestors.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"attestors": []}

        mock_list_next = (
            service.service.projects.return_value.attestors.return_value.list_next
        )
        mock_list_next.return_value = None

        attestors = service.list_attestors()

        assert len(attestors) == 0


class TestGetAttestor:
    """Tests for getting an attestor."""

    def test_get_attestor(self, service, sample_attestor_response):
        """Test getting a specific attestor."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value.attestors.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_attestor_response

        attestor = service.get_attestor("build-attestor")

        mock_get.assert_called_once_with(
            name="projects/test-project/attestors/build-attestor"
        )
        assert isinstance(attestor, Attestor)
        assert attestor.description == "Build pipeline attestor"

    def test_get_attestor_not_found(self, service):
        """Test getting an attestor that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            service.service.projects.return_value.attestors.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_attestor("missing-attestor")


class TestCreateAttestor:
    """Tests for creating an attestor."""

    def test_create_attestor(self, service, sample_attestor_response):
        """Test creating an attestor."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value.attestors.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_attestor_response

        attestor_body = {
            "description": "Build pipeline attestor",
            "userOwnedGrafeasNote": {
                "noteReference": "projects/test-project/notes/build-note",
            },
        }
        attestor = service.create_attestor("build-attestor", attestor_body)

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            attestorId="build-attestor",
            body=attestor_body,
        )
        assert isinstance(attestor, Attestor)
        assert attestor.description == "Build pipeline attestor"

    def test_create_attestor_api_error(self, service):
        """Test creating an attestor with an API error."""
        mock_request = mock.MagicMock()
        mock_create = (
            service.service.projects.return_value.attestors.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_attestor("test-attestor", {})


class TestUpdateAttestor:
    """Tests for updating an attestor."""

    def test_update_attestor(self, service, sample_attestor_response):
        """Test updating an attestor."""
        mock_request = mock.MagicMock()
        mock_update = (
            service.service.projects.return_value.attestors.return_value.update
        )
        mock_update.return_value = mock_request
        mock_request.execute.return_value = sample_attestor_response

        attestor_body = {"description": "Updated attestor"}
        attestor = service.update_attestor("build-attestor", attestor_body)

        mock_update.assert_called_once_with(
            name="projects/test-project/attestors/build-attestor",
            body=attestor_body,
        )
        assert isinstance(attestor, Attestor)

    def test_update_attestor_not_found(self, service):
        """Test updating an attestor that does not exist."""
        mock_request = mock.MagicMock()
        mock_update = (
            service.service.projects.return_value.attestors.return_value.update
        )
        mock_update.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_attestor("missing-attestor", {})


class TestDeleteAttestor:
    """Tests for deleting an attestor."""

    def test_delete_attestor(self, service):
        """Test deleting an attestor."""
        mock_request = mock.MagicMock()
        mock_delete = (
            service.service.projects.return_value.attestors.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_attestor("build-attestor")

        mock_delete.assert_called_once_with(
            name="projects/test-project/attestors/build-attestor"
        )
        assert result is True

    def test_delete_attestor_not_found(self, service):
        """Test deleting an attestor that does not exist."""
        mock_request = mock.MagicMock()
        mock_delete = (
            service.service.projects.return_value.attestors.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_attestor("missing-attestor")


class TestPolicyModel:
    """Tests for the Policy model."""

    def test_from_api_response(self, sample_policy_response):
        """Test creating a Policy from an API response."""
        policy = Policy.from_api_response(sample_policy_response)

        assert policy.name == "projects/test-project/policy"
        assert policy.global_policy_evaluation_mode == "ENABLE"
        assert (
            policy.default_admission_rule["evaluationMode"] == "ALWAYS_ALLOW"
        )
        assert policy.cluster_admission_rules is not None
        assert policy.type == "binaryauthorization.policy"

    def test_from_api_response_minimal(self):
        """Test creating a Policy from a minimal API response."""
        policy = Policy.from_api_response(
            {"name": "projects/test-project/policy"}
        )

        assert policy.name == "projects/test-project/policy"
        assert policy.global_policy_evaluation_mode is None
        assert policy.default_admission_rule == {}


class TestAttestorModel:
    """Tests for the Attestor model."""

    def test_from_api_response(self, sample_attestor_response):
        """Test creating an Attestor from an API response."""
        attestor = Attestor.from_api_response(sample_attestor_response)

        assert (
            attestor.name
            == "projects/test-project/attestors/build-attestor"
        )
        assert attestor.description == "Build pipeline attestor"
        assert attestor.user_owned_grafeas_note is not None
        assert attestor.type == "binaryauthorization.attestor"

    def test_from_api_response_minimal(self):
        """Test creating an Attestor from a minimal API response."""
        attestor = Attestor.from_api_response(
            {"name": "projects/test-project/attestors/my-attestor"}
        )

        assert attestor.description is None
        assert attestor.user_owned_grafeas_note is None
