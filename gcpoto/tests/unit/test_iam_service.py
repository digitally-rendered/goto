"""Tests for IAM service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.iam import IAMService, format_service_account_path
from gcpoto.models.iam import ServiceAccount, ServiceAccountKey, Role
from gcpoto.exceptions import ResourceNotFoundError


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # projects().serviceAccounts() chain
        mock_sa = mock.MagicMock()
        mock_service.projects.return_value.serviceAccounts.return_value = mock_sa

        # projects().serviceAccounts().keys() chain
        mock_keys = mock.MagicMock()
        mock_sa.keys.return_value = mock_keys

        # projects().roles() chain
        mock_roles = mock.MagicMock()
        mock_service.projects.return_value.roles.return_value = mock_roles

        yield mock_service


@pytest.fixture
def iam_service(mock_google_client):
    """Create an IAMService instance with mocked client."""
    return IAMService(project_id="test-project")


@pytest.fixture
def sample_service_account_response():
    """Sample IAM service account API response."""
    return {
        "name": "projects/test-project/serviceAccounts/test-sa@test-project.iam.gserviceaccount.com",
        "projectId": "test-project",
        "uniqueId": "123456789",
        "email": "test-sa@test-project.iam.gserviceaccount.com",
        "displayName": "Test Service Account",
        "description": "A test service account",
        "disabled": False,
        "oauth2ClientId": "987654321",
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-01-02T00:00:00Z",
    }


@pytest.fixture
def sample_key_response():
    """Sample IAM service account key API response."""
    return {
        "name": "projects/test-project/serviceAccounts/test-sa@test-project.iam.gserviceaccount.com/keys/abc123",
        "keyAlgorithm": "KEY_ALG_RSA_2048",
        "keyOrigin": "GOOGLE_PROVIDED",
        "keyType": "USER_MANAGED",
        "validAfterTime": "2025-01-01T00:00:00Z",
        "validBeforeTime": "2027-01-01T00:00:00Z",
        "privateKeyData": "base64encodeddata==",
    }


@pytest.fixture
def sample_role_response():
    """Sample IAM role API response."""
    return {
        "name": "projects/test-project/roles/customEditor",
        "title": "Custom Editor",
        "description": "A custom editor role",
        "includedPermissions": [
            "storage.buckets.get",
            "storage.buckets.list",
            "storage.objects.get",
        ],
        "stage": "GA",
        "deleted": False,
        "etag": "BwXyz123=",
    }


# ── Helper tests ─────────────────────────────────────────────────────


class TestFormatServiceAccountPath:
    def test_short_email(self):
        result = format_service_account_path(
            "my-project", "sa@my-project.iam.gserviceaccount.com"
        )
        assert (
            result
            == "projects/my-project/serviceAccounts/sa@my-project.iam.gserviceaccount.com"
        )

    def test_full_path_passthrough(self):
        full = "projects/my-project/serviceAccounts/sa@my-project.iam.gserviceaccount.com"
        assert format_service_account_path("my-project", full) == full


# ── Model tests ──────────────────────────────────────────────────────


class TestServiceAccountModel:
    def test_from_api_response(self, sample_service_account_response):
        sa = ServiceAccount.from_api_response(sample_service_account_response)
        assert sa.email == "test-sa@test-project.iam.gserviceaccount.com"
        assert sa.unique_id == "123456789"
        assert sa.display_name == "Test Service Account"
        assert sa.description == "A test service account"
        assert sa.disabled is False
        assert sa.oauth2_client_id == "987654321"
        assert sa.project == "test-project"
        assert sa.type == "iam.serviceAccount"

    def test_from_api_response_minimal(self):
        sa = ServiceAccount.from_api_response({
            "name": "projects/p/serviceAccounts/e",
            "email": "e",
            "uniqueId": "1",
        })
        assert sa.email == "e"
        assert sa.display_name == ""
        assert sa.disabled is False
        assert sa.oauth2_client_id is None

    def test_get_tag_from_tags(self, sample_service_account_response):
        sample_service_account_response["labels"] = {"env": "prod"}
        sa = ServiceAccount.from_api_response(sample_service_account_response)
        assert sa.get_tag("env") == "prod"

    def test_get_tag_default(self, sample_service_account_response):
        sa = ServiceAccount.from_api_response(sample_service_account_response)
        assert sa.get_tag("missing", "default") == "default"


class TestServiceAccountKeyModel:
    def test_from_api_response(self, sample_key_response):
        key = ServiceAccountKey.from_api_response(sample_key_response)
        assert key.id == "abc123"
        assert key.key_algorithm == "KEY_ALG_RSA_2048"
        assert key.key_origin == "GOOGLE_PROVIDED"
        assert key.key_type == "USER_MANAGED"
        assert key.private_key_data == "base64encodeddata=="
        assert key.project == "test-project"
        assert (
            key.service_account_email
            == "test-sa@test-project.iam.gserviceaccount.com"
        )

    def test_from_api_response_no_private_key(self):
        key = ServiceAccountKey.from_api_response({
            "name": "projects/p/serviceAccounts/e/keys/k1",
            "keyAlgorithm": "KEY_ALG_RSA_2048",
            "keyOrigin": "GOOGLE_PROVIDED",
            "keyType": "USER_MANAGED",
        })
        assert key.private_key_data is None
        assert key.valid_after_time is None


class TestRoleModel:
    def test_from_api_response(self, sample_role_response):
        role = Role.from_api_response(sample_role_response)
        assert role.id == "customEditor"
        assert role.title == "Custom Editor"
        assert role.description == "A custom editor role"
        assert len(role.included_permissions) == 3
        assert "storage.buckets.get" in role.included_permissions
        assert role.stage == "GA"
        assert role.deleted is False
        assert role.etag == "BwXyz123="
        assert role.project == "test-project"

    def test_from_api_response_predefined_role(self):
        role = Role.from_api_response({
            "name": "roles/editor",
            "title": "Editor",
            "includedPermissions": ["compute.instances.get"],
            "stage": "GA",
        })
        assert role.id == "editor"
        assert role.project == ""
        assert role.deleted is False

    def test_from_api_response_minimal(self):
        role = Role.from_api_response({"name": "roles/viewer"})
        assert role.title == ""
        assert role.included_permissions == []
        assert role.etag is None


# ── Service Account service tests ────────────────────────────────────


class TestIAMServiceInit:
    def test_init(self, mock_google_client):
        from googleapiclient.discovery import build

        service = IAMService(project_id="test-project")
        assert service.project_id == "test-project"
        build.assert_called_once_with("iam", "v1", credentials=None)


class TestListServiceAccounts:
    def test_list_service_accounts(
        self, iam_service, mock_google_client, sample_service_account_response
    ):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value
        mock_request = mock.MagicMock()
        mock_sa.list.return_value = mock_request
        mock_request.execute.return_value = {
            "accounts": [
                sample_service_account_response,
                sample_service_account_response,
            ]
        }
        mock_sa.list_next.return_value = None

        results = iam_service.list_service_accounts()

        mock_sa.list.assert_called_once_with(name="projects/test-project")
        assert len(results) == 2
        assert isinstance(results[0], ServiceAccount)
        assert results[0].email == "test-sa@test-project.iam.gserviceaccount.com"

    def test_list_service_accounts_empty(self, iam_service, mock_google_client):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value
        mock_request = mock.MagicMock()
        mock_sa.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_sa.list_next.return_value = None

        results = iam_service.list_service_accounts()
        assert results == []

    def test_list_service_accounts_pagination(
        self, iam_service, mock_google_client, sample_service_account_response
    ):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value

        # First page
        mock_request_1 = mock.MagicMock()
        mock_request_1.execute.return_value = {
            "accounts": [sample_service_account_response]
        }
        mock_sa.list.return_value = mock_request_1

        # Second page
        mock_request_2 = mock.MagicMock()
        mock_request_2.execute.return_value = {
            "accounts": [sample_service_account_response]
        }

        mock_sa.list_next.side_effect = [mock_request_2, None]

        results = iam_service.list_service_accounts()
        assert len(results) == 2


class TestGetServiceAccount:
    def test_get_service_account(
        self, iam_service, mock_google_client, sample_service_account_response
    ):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value
        mock_request = mock.MagicMock()
        mock_sa.get.return_value = mock_request
        mock_request.execute.return_value = sample_service_account_response

        result = iam_service.get_service_account(
            "test-sa@test-project.iam.gserviceaccount.com"
        )

        mock_sa.get.assert_called_once_with(
            name="projects/test-project/serviceAccounts/test-sa@test-project.iam.gserviceaccount.com"
        )
        assert isinstance(result, ServiceAccount)
        assert result.email == "test-sa@test-project.iam.gserviceaccount.com"

    def test_get_service_account_with_full_path(
        self, iam_service, mock_google_client, sample_service_account_response
    ):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value
        mock_request = mock.MagicMock()
        mock_sa.get.return_value = mock_request
        mock_request.execute.return_value = sample_service_account_response

        full_path = "projects/test-project/serviceAccounts/test-sa@test-project.iam.gserviceaccount.com"
        iam_service.get_service_account(full_path)
        mock_sa.get.assert_called_once_with(name=full_path)

    def test_get_service_account_not_found(
        self, iam_service, mock_google_client
    ):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value
        mock_request = mock.MagicMock()
        mock_sa.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404),
            content=b"Service account not found",
        )

        with pytest.raises(ResourceNotFoundError):
            iam_service.get_service_account("nonexistent@test.iam.gserviceaccount.com")


class TestCreateServiceAccount:
    def test_create_service_account(
        self, iam_service, mock_google_client, sample_service_account_response
    ):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value
        mock_request = mock.MagicMock()
        mock_sa.create.return_value = mock_request
        mock_request.execute.return_value = sample_service_account_response

        result = iam_service.create_service_account(
            account_id="test-sa",
            display_name="Test Service Account",
            description="A test service account",
        )

        mock_sa.create.assert_called_once_with(
            name="projects/test-project",
            body={
                "accountId": "test-sa",
                "serviceAccount": {
                    "displayName": "Test Service Account",
                    "description": "A test service account",
                },
            },
        )
        assert isinstance(result, ServiceAccount)
        assert result.display_name == "Test Service Account"

    def test_create_service_account_minimal(
        self, iam_service, mock_google_client, sample_service_account_response
    ):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value
        mock_request = mock.MagicMock()
        mock_sa.create.return_value = mock_request
        mock_request.execute.return_value = sample_service_account_response

        iam_service.create_service_account(account_id="test-sa")

        mock_sa.create.assert_called_once_with(
            name="projects/test-project",
            body={
                "accountId": "test-sa",
                "serviceAccount": {},
            },
        )


class TestUpdateServiceAccount:
    def test_update_service_account(
        self, iam_service, mock_google_client, sample_service_account_response
    ):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value
        mock_request = mock.MagicMock()
        mock_sa.update.return_value = mock_request
        sample_service_account_response["displayName"] = "Updated Name"
        mock_request.execute.return_value = sample_service_account_response

        email = "test-sa@test-project.iam.gserviceaccount.com"
        result = iam_service.update_service_account(
            email=email,
            display_name="Updated Name",
            description="Updated desc",
        )

        expected_name = f"projects/test-project/serviceAccounts/{email}"
        mock_sa.update.assert_called_once_with(
            name=expected_name,
            body={
                "name": expected_name,
                "displayName": "Updated Name",
                "description": "Updated desc",
            },
        )
        assert isinstance(result, ServiceAccount)
        assert result.display_name == "Updated Name"


class TestDeleteServiceAccount:
    def test_delete_service_account(self, iam_service, mock_google_client):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value
        mock_request = mock.MagicMock()
        mock_sa.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        email = "test-sa@test-project.iam.gserviceaccount.com"
        result = iam_service.delete_service_account(email)

        mock_sa.delete.assert_called_once_with(
            name=f"projects/test-project/serviceAccounts/{email}"
        )
        assert result is True


class TestEnableDisableServiceAccount:
    def test_enable_service_account(self, iam_service, mock_google_client):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value
        mock_request = mock.MagicMock()
        mock_sa.enable.return_value = mock_request
        mock_request.execute.return_value = {}

        email = "test-sa@test-project.iam.gserviceaccount.com"
        iam_service.enable_service_account(email)

        mock_sa.enable.assert_called_once_with(
            name=f"projects/test-project/serviceAccounts/{email}",
            body={},
        )

    def test_disable_service_account(self, iam_service, mock_google_client):
        mock_sa = mock_google_client.projects.return_value.serviceAccounts.return_value
        mock_request = mock.MagicMock()
        mock_sa.disable.return_value = mock_request
        mock_request.execute.return_value = {}

        email = "test-sa@test-project.iam.gserviceaccount.com"
        iam_service.disable_service_account(email)

        mock_sa.disable.assert_called_once_with(
            name=f"projects/test-project/serviceAccounts/{email}",
            body={},
        )


# ── Service Account Key service tests ────────────────────────────────


class TestListServiceAccountKeys:
    def test_list_keys(
        self, iam_service, mock_google_client, sample_key_response
    ):
        mock_keys = (
            mock_google_client.projects.return_value
            .serviceAccounts.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.list.return_value = mock_request
        mock_request.execute.return_value = {
            "keys": [sample_key_response, sample_key_response]
        }

        email = "test-sa@test-project.iam.gserviceaccount.com"
        results = iam_service.list_service_account_keys(email)

        mock_keys.list.assert_called_once_with(
            name=f"projects/test-project/serviceAccounts/{email}"
        )
        assert len(results) == 2
        assert isinstance(results[0], ServiceAccountKey)
        assert results[0].key_algorithm == "KEY_ALG_RSA_2048"

    def test_list_keys_with_filter(
        self, iam_service, mock_google_client, sample_key_response
    ):
        mock_keys = (
            mock_google_client.projects.return_value
            .serviceAccounts.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.list.return_value = mock_request
        mock_request.execute.return_value = {"keys": [sample_key_response]}

        email = "test-sa@test-project.iam.gserviceaccount.com"
        results = iam_service.list_service_account_keys(
            email, key_types=["USER_MANAGED"]
        )

        mock_keys.list.assert_called_once_with(
            name=f"projects/test-project/serviceAccounts/{email}",
            keyTypes=["USER_MANAGED"],
        )
        assert len(results) == 1

    def test_list_keys_empty(self, iam_service, mock_google_client):
        mock_keys = (
            mock_google_client.projects.return_value
            .serviceAccounts.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.list.return_value = mock_request
        mock_request.execute.return_value = {}

        results = iam_service.list_service_account_keys("sa@test.iam.gserviceaccount.com")
        assert results == []


class TestCreateServiceAccountKey:
    def test_create_key(
        self, iam_service, mock_google_client, sample_key_response
    ):
        mock_keys = (
            mock_google_client.projects.return_value
            .serviceAccounts.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.create.return_value = mock_request
        mock_request.execute.return_value = sample_key_response

        email = "test-sa@test-project.iam.gserviceaccount.com"
        result = iam_service.create_service_account_key(email)

        mock_keys.create.assert_called_once_with(
            name=f"projects/test-project/serviceAccounts/{email}",
            body={"keyAlgorithm": "KEY_ALG_RSA_2048"},
        )
        assert isinstance(result, ServiceAccountKey)
        assert result.private_key_data == "base64encodeddata=="

    def test_create_key_custom_algorithm(
        self, iam_service, mock_google_client, sample_key_response
    ):
        mock_keys = (
            mock_google_client.projects.return_value
            .serviceAccounts.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.create.return_value = mock_request
        mock_request.execute.return_value = sample_key_response

        email = "test-sa@test-project.iam.gserviceaccount.com"
        iam_service.create_service_account_key(email, key_algorithm="KEY_ALG_RSA_1024")

        mock_keys.create.assert_called_once_with(
            name=f"projects/test-project/serviceAccounts/{email}",
            body={"keyAlgorithm": "KEY_ALG_RSA_1024"},
        )


class TestDeleteServiceAccountKey:
    def test_delete_key(self, iam_service, mock_google_client):
        mock_keys = (
            mock_google_client.projects.return_value
            .serviceAccounts.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        email = "test-sa@test-project.iam.gserviceaccount.com"
        result = iam_service.delete_service_account_key(email, "abc123")

        mock_keys.delete.assert_called_once_with(
            name=f"projects/test-project/serviceAccounts/{email}/keys/abc123"
        )
        assert result is True


# ── Role service tests ───────────────────────────────────────────────


class TestListRoles:
    def test_list_roles(
        self, iam_service, mock_google_client, sample_role_response
    ):
        mock_roles = mock_google_client.projects.return_value.roles.return_value
        mock_request = mock.MagicMock()
        mock_roles.list.return_value = mock_request
        mock_request.execute.return_value = {
            "roles": [sample_role_response, sample_role_response]
        }
        mock_roles.list_next.return_value = None

        results = iam_service.list_roles()

        mock_roles.list.assert_called_once_with(
            parent="projects/test-project", showDeleted=False
        )
        assert len(results) == 2
        assert isinstance(results[0], Role)
        assert results[0].title == "Custom Editor"

    def test_list_roles_show_deleted(
        self, iam_service, mock_google_client, sample_role_response
    ):
        mock_roles = mock_google_client.projects.return_value.roles.return_value
        mock_request = mock.MagicMock()
        mock_roles.list.return_value = mock_request
        mock_request.execute.return_value = {"roles": [sample_role_response]}
        mock_roles.list_next.return_value = None

        iam_service.list_roles(show_deleted=True)

        mock_roles.list.assert_called_once_with(
            parent="projects/test-project", showDeleted=True
        )

    def test_list_roles_with_parent(
        self, iam_service, mock_google_client, sample_role_response
    ):
        mock_roles = mock_google_client.projects.return_value.roles.return_value
        mock_request = mock.MagicMock()
        mock_roles.list.return_value = mock_request
        mock_request.execute.return_value = {"roles": [sample_role_response]}
        mock_roles.list_next.return_value = None

        iam_service.list_roles(parent="organizations/12345")

        mock_roles.list.assert_called_once_with(
            parent="organizations/12345", showDeleted=False
        )

    def test_list_roles_empty(self, iam_service, mock_google_client):
        mock_roles = mock_google_client.projects.return_value.roles.return_value
        mock_request = mock.MagicMock()
        mock_roles.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_roles.list_next.return_value = None

        results = iam_service.list_roles()
        assert results == []


class TestGetRole:
    def test_get_role(
        self, iam_service, mock_google_client, sample_role_response
    ):
        mock_roles = mock_google_client.projects.return_value.roles.return_value
        mock_request = mock.MagicMock()
        mock_roles.get.return_value = mock_request
        mock_request.execute.return_value = sample_role_response

        result = iam_service.get_role("projects/test-project/roles/customEditor")

        mock_roles.get.assert_called_once_with(
            name="projects/test-project/roles/customEditor"
        )
        assert isinstance(result, Role)
        assert result.title == "Custom Editor"
        assert len(result.included_permissions) == 3

    def test_get_role_not_found(self, iam_service, mock_google_client):
        mock_roles = mock_google_client.projects.return_value.roles.return_value
        mock_request = mock.MagicMock()
        mock_roles.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404),
            content=b"Role not found",
        )

        with pytest.raises(ResourceNotFoundError):
            iam_service.get_role("projects/test-project/roles/nonexistent")


class TestCreateRole:
    def test_create_role(
        self, iam_service, mock_google_client, sample_role_response
    ):
        mock_roles = mock_google_client.projects.return_value.roles.return_value
        mock_request = mock.MagicMock()
        mock_roles.create.return_value = mock_request
        mock_request.execute.return_value = sample_role_response

        result = iam_service.create_role(
            role_id="customEditor",
            title="Custom Editor",
            permissions=["storage.buckets.get", "storage.buckets.list"],
            description="A custom editor role",
            stage="GA",
        )

        mock_roles.create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "roleId": "customEditor",
                "role": {
                    "title": "Custom Editor",
                    "description": "A custom editor role",
                    "includedPermissions": [
                        "storage.buckets.get",
                        "storage.buckets.list",
                    ],
                    "stage": "GA",
                },
            },
        )
        assert isinstance(result, Role)
        assert result.title == "Custom Editor"

    def test_create_role_minimal(
        self, iam_service, mock_google_client, sample_role_response
    ):
        mock_roles = mock_google_client.projects.return_value.roles.return_value
        mock_request = mock.MagicMock()
        mock_roles.create.return_value = mock_request
        mock_request.execute.return_value = sample_role_response

        iam_service.create_role(role_id="minRole")

        mock_roles.create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "roleId": "minRole",
                "role": {
                    "title": "",
                    "description": "",
                    "includedPermissions": [],
                    "stage": "GA",
                },
            },
        )


class TestUpdateRole:
    def test_update_role(
        self, iam_service, mock_google_client, sample_role_response
    ):
        mock_roles = mock_google_client.projects.return_value.roles.return_value
        mock_request = mock.MagicMock()
        mock_roles.patch.return_value = mock_request
        sample_role_response["title"] = "Updated Editor"
        mock_request.execute.return_value = sample_role_response

        role_name = "projects/test-project/roles/customEditor"
        result = iam_service.update_role(
            role_name=role_name,
            title="Updated Editor",
            permissions=["storage.buckets.get"],
            description="Updated description",
            stage="BETA",
        )

        mock_roles.patch.assert_called_once_with(
            name=role_name,
            body={
                "title": "Updated Editor",
                "includedPermissions": ["storage.buckets.get"],
                "description": "Updated description",
                "stage": "BETA",
            },
        )
        assert isinstance(result, Role)
        assert result.title == "Updated Editor"

    def test_update_role_partial(
        self, iam_service, mock_google_client, sample_role_response
    ):
        mock_roles = mock_google_client.projects.return_value.roles.return_value
        mock_request = mock.MagicMock()
        mock_roles.patch.return_value = mock_request
        mock_request.execute.return_value = sample_role_response

        role_name = "projects/test-project/roles/customEditor"
        iam_service.update_role(role_name=role_name, title="New Title")

        mock_roles.patch.assert_called_once_with(
            name=role_name,
            body={"title": "New Title"},
        )


class TestDeleteRole:
    def test_delete_role(
        self, iam_service, mock_google_client, sample_role_response
    ):
        mock_roles = mock_google_client.projects.return_value.roles.return_value
        mock_request = mock.MagicMock()
        mock_roles.delete.return_value = mock_request
        sample_role_response["deleted"] = True
        mock_request.execute.return_value = sample_role_response

        role_name = "projects/test-project/roles/customEditor"
        result = iam_service.delete_role(role_name)

        mock_roles.delete.assert_called_once_with(name=role_name)
        assert isinstance(result, Role)
        assert result.deleted is True
