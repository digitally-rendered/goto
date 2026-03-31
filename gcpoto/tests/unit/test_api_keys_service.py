"""Tests for the API Keys service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.api_keys import APIKeysService
from gcpoto.models.api_keys import APIKey
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
def sample_key_response():
    """Sample API key response."""
    return {
        "name": "projects/test-project/locations/global/keys/key-123",
        "uid": "uid-abc-123",
        "displayName": "My API Key",
        "keyString": "AIzaSyB1234567890abcdefg",
        "restrictions": {
            "browserKeyRestrictions": {
                "allowedReferrers": ["https://example.com/*"]
            },
            "apiTargets": [
                {"service": "maps-backend.googleapis.com"}
            ],
        },
        "annotations": {"env": "test", "team": "platform"},
        "project": "test-project",
        "location": "global",
        "createTime": "2024-06-01T10:00:00.000Z",
        "updateTime": "2024-06-01T12:00:00.000Z",
    }


@pytest.fixture
def service(mock_google_client):
    """Create an APIKeysService instance with mocked API client."""
    return APIKeysService(project_id="test-project")


# ------------------------------------------------------------------ #
#  Service init
# ------------------------------------------------------------------ #


class TestAPIKeysServiceInit:
    """Tests for APIKeysService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the API Keys service."""
        from googleapiclient.discovery import build

        svc = APIKeysService(project_id="test-project")

        assert svc.project_id == "test-project"
        assert svc.service_name == "apikeys"
        assert svc.version == "v2"
        build.assert_called_once_with("apikeys", "v2", credentials=None)

    def test_init_with_credentials(self, mock_google_client):
        """Test initializing with credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = APIKeysService(
                project_id="test-project",
                credentials_file="/path/to/creds.json",
            )
            assert svc.project_id == "test-project"
            mock_creds.assert_called_once()


# ------------------------------------------------------------------ #
#  Key operations
# ------------------------------------------------------------------ #


class TestListKeys:
    """Tests for listing API keys."""

    def test_list_keys(self, service, sample_key_response):
        """Test listing API keys."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.list.return_value = mock_request
        mock_request.execute.return_value = {
            "keys": [sample_key_response]
        }
        mock_keys.list_next.return_value = None

        keys = service.list_keys()

        mock_keys.list.assert_called_once_with(
            parent="projects/test-project/locations/global"
        )
        assert len(keys) == 1
        assert isinstance(keys[0], APIKey)
        assert keys[0].display_name == "My API Key"

    def test_list_keys_custom_location(self, service, sample_key_response):
        """Test listing API keys with a custom location."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.list.return_value = mock_request
        mock_request.execute.return_value = {"keys": []}
        mock_keys.list_next.return_value = None

        service.list_keys(location="us-central1")

        mock_keys.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )

    def test_list_keys_empty(self, service):
        """Test listing keys when none exist."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.list.return_value = mock_request
        mock_request.execute.return_value = {"keys": []}
        mock_keys.list_next.return_value = None

        keys = service.list_keys()
        assert len(keys) == 0

    def test_list_keys_pagination(self, service, sample_key_response):
        """Test listing keys with pagination."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_keys.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "keys": [sample_key_response]
        }

        second_key = dict(sample_key_response)
        second_key["name"] = "projects/test-project/locations/global/keys/key-456"
        second_key["uid"] = "uid-def-456"
        mock_request_page2.execute.return_value = {
            "keys": [second_key]
        }

        mock_keys.list_next.side_effect = [mock_request_page2, None]

        keys = service.list_keys()
        assert len(keys) == 2


class TestGetKey:
    """Tests for getting an API key."""

    def test_get_key(self, service, sample_key_response):
        """Test getting a specific API key."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.get.return_value = mock_request
        mock_request.execute.return_value = sample_key_response

        key = service.get_key("global", "key-123")

        mock_keys.get.assert_called_once_with(
            name="projects/test-project/locations/global/keys/key-123"
        )
        assert isinstance(key, APIKey)
        assert key.display_name == "My API Key"
        assert key.restrictions is not None

    def test_get_key_not_found(self, service):
        """Test getting a key that does not exist."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_key("global", "nonexistent")

    def test_get_key_api_error(self, service):
        """Test getting a key with an API error."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_key("global", "key-123")


class TestCreateKey:
    """Tests for creating an API key."""

    def test_create_key(self, service, sample_key_response):
        """Test creating an API key."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.create.return_value = mock_request
        mock_request.execute.return_value = sample_key_response

        key = service.create_key(
            location="global",
            display_name="My API Key",
            restrictions={"apiTargets": [{"service": "maps-backend.googleapis.com"}]},
        )

        mock_keys.create.assert_called_once_with(
            parent="projects/test-project/locations/global",
            body={
                "displayName": "My API Key",
                "restrictions": {
                    "apiTargets": [
                        {"service": "maps-backend.googleapis.com"}
                    ]
                },
            },
        )
        assert isinstance(key, APIKey)
        assert key.display_name == "My API Key"

    def test_create_key_minimal(self, service, sample_key_response):
        """Test creating a key with minimal parameters."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.create.return_value = mock_request
        mock_request.execute.return_value = sample_key_response

        service.create_key(location="global")

        mock_keys.create.assert_called_once_with(
            parent="projects/test-project/locations/global",
            body={},
        )

    def test_create_key_api_error(self, service):
        """Test creating a key with an API error."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_key(location="global")


class TestUpdateKey:
    """Tests for updating an API key."""

    def test_update_key(self, service, sample_key_response):
        """Test updating an API key."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.patch.return_value = mock_request
        updated_response = dict(sample_key_response)
        updated_response["displayName"] = "Updated Key"
        mock_request.execute.return_value = updated_response

        key = service.update_key(
            location="global",
            key_id="key-123",
            display_name="Updated Key",
        )

        mock_keys.patch.assert_called_once_with(
            name="projects/test-project/locations/global/keys/key-123",
            updateMask="displayName",
            body={"displayName": "Updated Key"},
        )
        assert isinstance(key, APIKey)

    def test_update_key_restrictions(self, service, sample_key_response):
        """Test updating key restrictions."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.patch.return_value = mock_request
        mock_request.execute.return_value = sample_key_response

        new_restrictions = {
            "apiTargets": [{"service": "translate.googleapis.com"}]
        }

        service.update_key(
            location="global",
            key_id="key-123",
            restrictions=new_restrictions,
        )

        mock_keys.patch.assert_called_once_with(
            name="projects/test-project/locations/global/keys/key-123",
            updateMask="restrictions",
            body={"restrictions": new_restrictions},
        )

    def test_update_key_not_found(self, service):
        """Test updating a key that does not exist."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_key(
                location="global",
                key_id="nonexistent",
                display_name="Test",
            )


class TestDeleteKey:
    """Tests for deleting an API key."""

    def test_delete_key(self, service):
        """Test deleting an API key."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_key("global", "key-123")

        mock_keys.delete.assert_called_once_with(
            name="projects/test-project/locations/global/keys/key-123"
        )
        assert result is True

    def test_delete_key_not_found(self, service):
        """Test deleting a key that does not exist."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_key("global", "nonexistent")


class TestUndeleteKey:
    """Tests for undeleting an API key."""

    def test_undelete_key(self, service, sample_key_response):
        """Test undeleting an API key."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.undelete.return_value = mock_request
        mock_request.execute.return_value = sample_key_response

        key = service.undelete_key("global", "key-123")

        mock_keys.undelete.assert_called_once_with(
            name="projects/test-project/locations/global/keys/key-123"
        )
        assert isinstance(key, APIKey)

    def test_undelete_key_not_found(self, service):
        """Test undeleting a key that does not exist."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.undelete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.undelete_key("global", "nonexistent")


class TestGetKeyString:
    """Tests for getting the key string."""

    def test_get_key_string(self, service):
        """Test getting the key string for an API key."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.getKeyString.return_value = mock_request
        mock_request.execute.return_value = {
            "keyString": "AIzaSyB1234567890abcdefg"
        }

        result = service.get_key_string("global", "key-123")

        mock_keys.getKeyString.assert_called_once_with(
            name="projects/test-project/locations/global/keys/key-123"
        )
        assert result == "AIzaSyB1234567890abcdefg"

    def test_get_key_string_not_found(self, service):
        """Test getting key string for a nonexistent key."""
        mock_keys = (
            service.service.projects.return_value
            .locations.return_value
            .keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.getKeyString.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_key_string("global", "nonexistent")


# ------------------------------------------------------------------ #
#  Model tests
# ------------------------------------------------------------------ #


class TestAPIKeyModel:
    """Tests for the APIKey model."""

    def test_from_api_response(self, sample_key_response):
        """Test creating an APIKey from an API response."""
        key = APIKey.from_api_response(sample_key_response)

        assert key.id == "uid-abc-123"
        assert key.name == "projects/test-project/locations/global/keys/key-123"
        assert key.type == "apikeys.key"
        assert key.display_name == "My API Key"
        assert key.key_string == "AIzaSyB1234567890abcdefg"
        assert key.restrictions is not None
        assert key.labels == {"env": "test", "team": "platform"}

    def test_from_api_response_minimal(self):
        """Test creating an APIKey from a minimal response."""
        key = APIKey.from_api_response({"name": "simple-key"})

        assert key.id == "simple-key"
        assert key.name == "simple-key"
        assert key.display_name is None
        assert key.key_string is None
        assert key.restrictions is None

    def test_get_tag(self, sample_key_response):
        """Test the get_tag method."""
        key = APIKey.from_api_response(sample_key_response)

        assert key.get_tag("env") == "test"
        assert key.get_tag("team") == "platform"
        assert key.get_tag("missing") == ""
        assert key.get_tag("missing", "default") == "default"
