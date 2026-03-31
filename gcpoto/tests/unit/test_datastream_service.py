"""Tests for Datastream service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.datastream import DatastreamService
from gcpoto.models.datastream import ConnectionProfile, Stream
from gcpoto.exceptions import ResourceNotFoundError, APIError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
PROFILE_ID = "my-mysql-profile"
STREAM_ID = "my-stream"


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_conn_profiles = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.connectionProfiles.return_value = (
            mock_conn_profiles
        )

        mock_streams = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.streams.return_value = (
            mock_streams
        )

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a DatastreamService with mocked client."""
    return DatastreamService(project_id=PROJECT_ID)


@pytest.fixture
def mock_conn_profiles(mock_google_client):
    """Shortcut to mock connection profiles resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .connectionProfiles.return_value
    )


@pytest.fixture
def mock_streams(mock_google_client):
    """Shortcut to mock streams resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .streams.return_value
    )


@pytest.fixture
def sample_connection_profile_response():
    """Sample connection profile API response."""
    return {
        "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/connectionProfiles/{PROFILE_ID}",
        "displayName": "My MySQL Profile",
        "createTime": "2026-03-31T10:00:00Z",
        "updateTime": "2026-03-31T11:00:00Z",
        "mysqlProfile": {
            "hostname": "10.0.0.1",
            "port": 3306,
            "username": "root",
        },
        "labels": {"env": "test"},
    }


@pytest.fixture
def sample_stream_response():
    """Sample stream API response."""
    return {
        "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/streams/{STREAM_ID}",
        "displayName": "My Stream",
        "createTime": "2026-03-31T10:00:00Z",
        "updateTime": "2026-03-31T11:00:00Z",
        "state": "RUNNING",
        "sourceConfig": {
            "sourceConnectionProfile": f"projects/{PROJECT_ID}/locations/{LOCATION}/connectionProfiles/src",
            "mysqlSourceConfig": {},
        },
        "destinationConfig": {
            "destinationConnectionProfile": f"projects/{PROJECT_ID}/locations/{LOCATION}/connectionProfiles/dst",
            "bigqueryDestinationConfig": {},
        },
        "backfillAll": {},
        "labels": {"env": "test", "team": "data"},
    }


class TestDatastreamServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the DatastreamService."""
        from googleapiclient.discovery import build

        svc = DatastreamService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with("datastream", "v1", credentials=None)


class TestListConnectionProfiles:
    def test_list_connection_profiles(
        self, service, mock_conn_profiles, sample_connection_profile_response
    ):
        """Test listing connection profiles."""
        mock_request = mock.MagicMock()
        mock_conn_profiles.list.return_value = mock_request
        mock_request.execute.return_value = {
            "connectionProfiles": [sample_connection_profile_response]
        }
        mock_conn_profiles.list_next.return_value = None

        results = service.list_connection_profiles(LOCATION)

        mock_conn_profiles.list.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}"
        )
        assert len(results) == 1
        assert isinstance(results[0], ConnectionProfile)
        assert results[0].display_name == "My MySQL Profile"

    def test_list_connection_profiles_empty(
        self, service, mock_conn_profiles
    ):
        """Test listing connection profiles when none exist."""
        mock_request = mock.MagicMock()
        mock_conn_profiles.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_conn_profiles.list_next.return_value = None

        results = service.list_connection_profiles(LOCATION)
        assert len(results) == 0


class TestGetConnectionProfile:
    def test_get_connection_profile(
        self, service, mock_conn_profiles, sample_connection_profile_response
    ):
        """Test getting a specific connection profile."""
        mock_request = mock.MagicMock()
        mock_conn_profiles.get.return_value = mock_request
        mock_request.execute.return_value = (
            sample_connection_profile_response
        )

        result = service.get_connection_profile(LOCATION, PROFILE_ID)

        assert isinstance(result, ConnectionProfile)
        assert result.display_name == "My MySQL Profile"
        assert result.mysql_profile is not None

    def test_get_connection_profile_not_found(
        self, service, mock_conn_profiles
    ):
        """Test getting a connection profile that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_conn_profiles.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_connection_profile(LOCATION, PROFILE_ID)


class TestCreateConnectionProfile:
    def test_create_connection_profile(
        self, service, mock_conn_profiles, sample_connection_profile_response
    ):
        """Test creating a new connection profile."""
        mock_request = mock.MagicMock()
        mock_conn_profiles.create.return_value = mock_request
        mock_request.execute.return_value = (
            sample_connection_profile_response
        )

        result = service.create_connection_profile(
            LOCATION,
            PROFILE_ID,
            "My MySQL Profile",
            {"mysqlProfile": {"hostname": "10.0.0.1", "port": 3306}},
        )

        assert isinstance(result, ConnectionProfile)
        assert result.display_name == "My MySQL Profile"

    def test_create_connection_profile_api_error(
        self, service, mock_conn_profiles
    ):
        """Test creating a connection profile when API returns an error."""
        mock_request = mock.MagicMock()
        mock_conn_profiles.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_connection_profile(
                LOCATION, PROFILE_ID, "Bad", {}
            )


class TestDeleteConnectionProfile:
    def test_delete_connection_profile(
        self, service, mock_conn_profiles
    ):
        """Test deleting a connection profile."""
        mock_conn_profiles.delete.return_value.execute.return_value = {}

        result = service.delete_connection_profile(LOCATION, PROFILE_ID)
        assert result is True

    def test_delete_connection_profile_not_found(
        self, service, mock_conn_profiles
    ):
        """Test deleting a connection profile that doesn't exist."""
        mock_conn_profiles.delete.return_value.execute.side_effect = (
            HttpError(
                resp=mock.MagicMock(status=404), content=b"Not found"
            )
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_connection_profile(LOCATION, PROFILE_ID)


class TestListStreams:
    def test_list_streams(
        self, service, mock_streams, sample_stream_response
    ):
        """Test listing streams."""
        mock_request = mock.MagicMock()
        mock_streams.list.return_value = mock_request
        mock_request.execute.return_value = {
            "streams": [sample_stream_response]
        }
        mock_streams.list_next.return_value = None

        results = service.list_streams(LOCATION)

        assert len(results) == 1
        assert isinstance(results[0], Stream)
        assert results[0].display_name == "My Stream"
        assert results[0].state == "RUNNING"

    def test_list_streams_empty(self, service, mock_streams):
        """Test listing streams when none exist."""
        mock_request = mock.MagicMock()
        mock_streams.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_streams.list_next.return_value = None

        results = service.list_streams(LOCATION)
        assert len(results) == 0


class TestGetStream:
    def test_get_stream(
        self, service, mock_streams, sample_stream_response
    ):
        """Test getting a specific stream."""
        mock_request = mock.MagicMock()
        mock_streams.get.return_value = mock_request
        mock_request.execute.return_value = sample_stream_response

        result = service.get_stream(LOCATION, STREAM_ID)

        assert isinstance(result, Stream)
        assert result.display_name == "My Stream"
        assert result.state == "RUNNING"
        assert result.source_config is not None
        assert result.destination_config is not None

    def test_get_stream_not_found(self, service, mock_streams):
        """Test getting a stream that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_streams.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_stream(LOCATION, STREAM_ID)


class TestCreateStream:
    def test_create_stream(
        self, service, mock_streams, sample_stream_response
    ):
        """Test creating a new stream."""
        mock_request = mock.MagicMock()
        mock_streams.create.return_value = mock_request
        mock_request.execute.return_value = sample_stream_response

        result = service.create_stream(
            LOCATION,
            STREAM_ID,
            "My Stream",
            source_config={"sourceConnectionProfile": "src"},
            destination_config={"destinationConnectionProfile": "dst"},
        )

        assert isinstance(result, Stream)
        assert result.display_name == "My Stream"

    def test_create_stream_api_error(self, service, mock_streams):
        """Test creating a stream when API returns an error."""
        mock_request = mock.MagicMock()
        mock_streams.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_stream(
                LOCATION, STREAM_ID, "Bad", {}, {}
            )


class TestUpdateStream:
    def test_update_stream(
        self, service, mock_streams, sample_stream_response
    ):
        """Test updating a stream."""
        mock_request = mock.MagicMock()
        mock_streams.patch.return_value = mock_request
        mock_request.execute.return_value = sample_stream_response

        result = service.update_stream(
            LOCATION, STREAM_ID, "displayName", {"displayName": "Updated"}
        )

        mock_streams.patch.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/streams/{STREAM_ID}",
            updateMask="displayName",
            body={"displayName": "Updated"},
        )
        assert isinstance(result, Stream)

    def test_update_stream_not_found(self, service, mock_streams):
        """Test updating a stream that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_streams.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_stream(
                LOCATION, STREAM_ID, "state", {"state": "PAUSED"}
            )


class TestDeleteStream:
    def test_delete_stream(self, service, mock_streams):
        """Test deleting a stream."""
        mock_streams.delete.return_value.execute.return_value = {}

        result = service.delete_stream(LOCATION, STREAM_ID)
        assert result is True

    def test_delete_stream_not_found(self, service, mock_streams):
        """Test deleting a stream that doesn't exist."""
        mock_streams.delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_stream(LOCATION, STREAM_ID)


class TestStartStopStream:
    def test_start_stream(
        self, service, mock_streams, sample_stream_response
    ):
        """Test starting a stream."""
        mock_request = mock.MagicMock()
        mock_streams.patch.return_value = mock_request
        mock_request.execute.return_value = {
            **sample_stream_response,
            "state": "RUNNING",
        }

        result = service.start_stream(LOCATION, STREAM_ID)

        mock_streams.patch.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/streams/{STREAM_ID}",
            updateMask="state",
            body={"state": "RUNNING"},
        )
        assert isinstance(result, Stream)

    def test_stop_stream(
        self, service, mock_streams, sample_stream_response
    ):
        """Test stopping a stream."""
        mock_request = mock.MagicMock()
        mock_streams.patch.return_value = mock_request
        mock_request.execute.return_value = {
            **sample_stream_response,
            "state": "PAUSED",
        }

        result = service.stop_stream(LOCATION, STREAM_ID)

        mock_streams.patch.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/streams/{STREAM_ID}",
            updateMask="state",
            body={"state": "PAUSED"},
        )
        assert isinstance(result, Stream)


class TestConnectionProfileModel:
    def test_from_api_response(self, sample_connection_profile_response):
        """Test creating a ConnectionProfile from API response."""
        cp = ConnectionProfile.from_api_response(
            sample_connection_profile_response
        )

        assert cp.id == PROFILE_ID
        assert cp.location == LOCATION
        assert cp.project == PROJECT_ID
        assert cp.display_name == "My MySQL Profile"
        assert cp.mysql_profile is not None
        assert cp.type == "datastream.connectionProfile"

    def test_from_api_response_minimal(self):
        """Test creating a ConnectionProfile from minimal API response."""
        response = {
            "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/connectionProfiles/minimal"
        }
        cp = ConnectionProfile.from_api_response(response)

        assert cp.id == "minimal"
        assert cp.oracle_profile is None
        assert cp.mysql_profile is None

    def test_get_tag(self, sample_connection_profile_response):
        """Test getting tags from a ConnectionProfile."""
        cp = ConnectionProfile.from_api_response(
            sample_connection_profile_response
        )

        assert cp.get_tag("env") == "test"
        assert cp.get_tag("missing") == ""
        assert cp.get_tag("missing", "default") == "default"


class TestStreamModel:
    def test_from_api_response(self, sample_stream_response):
        """Test creating a Stream from API response."""
        stream = Stream.from_api_response(sample_stream_response)

        assert stream.id == STREAM_ID
        assert stream.location == LOCATION
        assert stream.project == PROJECT_ID
        assert stream.display_name == "My Stream"
        assert stream.state == "RUNNING"
        assert stream.source_config is not None
        assert stream.destination_config is not None
        assert stream.backfill_all is not None
        assert stream.type == "datastream.stream"

    def test_from_api_response_minimal(self):
        """Test creating a Stream from minimal API response."""
        response = {
            "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/streams/minimal"
        }
        stream = Stream.from_api_response(response)

        assert stream.id == "minimal"
        assert stream.state == ""
        assert stream.backfill_all is None

    def test_get_tag(self, sample_stream_response):
        """Test getting tags from a Stream."""
        stream = Stream.from_api_response(sample_stream_response)

        assert stream.get_tag("env") == "test"
        assert stream.get_tag("team") == "data"
        assert stream.get_tag("missing") == ""
        assert stream.get_tag("missing", "default") == "default"
