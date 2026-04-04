"""Tests for Eventarc service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.eventarc import EventarcService
from gcpoto.models.eventarc import EventarcTrigger
from gcpoto.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
TRIGGER_NAME = "test-trigger"

TRIGGER_PATH = (
    f"projects/{PROJECT_ID}/locations/{LOCATION}/triggers/{TRIGGER_NAME}"
)
LOCATION_PATH = f"projects/{PROJECT_ID}/locations/{LOCATION}"


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().locations().triggers() chain
        mock_triggers = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.triggers.return_value = (
            mock_triggers
        )

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create an EventarcService with mocked client."""
    return EventarcService(project_id=PROJECT_ID)


@pytest.fixture
def sample_trigger_response():
    """Sample Eventarc trigger API response."""
    return {
        "name": TRIGGER_PATH,
        "eventFilters": [
            {
                "attribute": "type",
                "value": "google.cloud.storage.object.v1.finalized",
            },
            {
                "attribute": "bucket",
                "value": "my-bucket",
            },
        ],
        "destination": {
            "cloudRun": {
                "service": "my-service",
                "path": "/handler",
                "region": "us-central1",
            },
        },
        "transport": {
            "pubsub": {
                "topic": "projects/test-project/topics/eventarc-trigger-topic",
            },
        },
        "serviceAccount": "trigger-sa@test-project.iam.gserviceaccount.com",
        "channel": "projects/test-project/locations/us-central1/channels/my-channel",
        "conditions": {
            "transport.pubsub.subscription": {
                "code": 0,
                "message": "OK",
            },
        },
        "labels": {"env": "test", "team": "platform"},
        "createTime": "2026-03-01T10:00:00Z",
        "updateTime": "2026-03-15T12:00:00Z",
    }


@pytest.fixture
def mock_triggers(mock_google_client):
    """Shortcut to mock triggers resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .triggers.return_value
    )


class TestEventarcServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the EventarcService."""
        from googleapiclient.discovery import build

        svc = EventarcService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with("eventarc", "v1", credentials=None)

    def test_init_with_credentials_file(self, mock_google_client):
        """Test initializing with a credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = EventarcService(
                project_id=PROJECT_ID, credentials_file="/path/to/creds.json"
            )
            assert svc.project_id == PROJECT_ID
            mock_creds.assert_called_once()


class TestListTriggers:
    def test_list_triggers(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test listing Eventarc triggers."""
        mock_request = mock.MagicMock()
        mock_triggers.list.return_value = mock_request
        mock_request.execute.return_value = {
            "triggers": [sample_trigger_response, sample_trigger_response]
        }
        mock_triggers.list_next.return_value = None

        triggers = service.list_triggers(LOCATION)

        mock_triggers.list.assert_called_once_with(parent=LOCATION_PATH)
        assert len(triggers) == 2
        assert isinstance(triggers[0], EventarcTrigger)
        assert triggers[0].name == TRIGGER_NAME
        assert triggers[0].project == PROJECT_ID
        assert triggers[0].location == LOCATION

    def test_list_triggers_all_locations(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test listing triggers across all locations."""
        mock_request = mock.MagicMock()
        mock_triggers.list.return_value = mock_request
        mock_request.execute.return_value = {
            "triggers": [sample_trigger_response]
        }
        mock_triggers.list_next.return_value = None

        triggers = service.list_triggers()

        mock_triggers.list.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/-"
        )
        assert len(triggers) == 1

    def test_list_triggers_empty(self, service, mock_triggers):
        """Test listing triggers when none exist."""
        mock_request = mock.MagicMock()
        mock_triggers.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_triggers.list_next.return_value = None

        triggers = service.list_triggers(LOCATION)

        assert len(triggers) == 0

    def test_list_triggers_pagination(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test listing triggers with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_triggers.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "triggers": [sample_trigger_response]
        }

        mock_triggers.list_next.side_effect = [mock_request_page2, None]
        mock_request_page2.execute.return_value = {
            "triggers": [sample_trigger_response]
        }

        triggers = service.list_triggers(LOCATION)
        assert len(triggers) == 2


class TestGetTrigger:
    def test_get_trigger(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test getting a specific trigger."""
        mock_request = mock.MagicMock()
        mock_triggers.get.return_value = mock_request
        mock_request.execute.return_value = sample_trigger_response

        trigger = service.get_trigger(LOCATION, TRIGGER_NAME)

        mock_triggers.get.assert_called_once_with(name=TRIGGER_PATH)
        assert isinstance(trigger, EventarcTrigger)
        assert trigger.name == TRIGGER_NAME
        assert trigger.location == LOCATION
        assert len(trigger.event_filters) == 2
        assert trigger.destination == sample_trigger_response["destination"]
        assert trigger.service_account == (
            "trigger-sa@test-project.iam.gserviceaccount.com"
        )

    def test_get_trigger_not_found(self, service, mock_triggers):
        """Test getting a trigger that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_triggers.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_trigger(LOCATION, TRIGGER_NAME)

    def test_get_trigger_with_full_path(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test getting a trigger using a full resource path."""
        mock_request = mock.MagicMock()
        mock_triggers.get.return_value = mock_request
        mock_request.execute.return_value = sample_trigger_response

        service.get_trigger(LOCATION, TRIGGER_PATH)
        mock_triggers.get.assert_called_once_with(name=TRIGGER_PATH)


class TestCreateTrigger:
    def test_create_trigger(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test creating a new trigger."""
        mock_request = mock.MagicMock()
        mock_triggers.create.return_value = mock_request
        mock_request.execute.return_value = sample_trigger_response

        event_filters = [
            {
                "attribute": "type",
                "value": "google.cloud.storage.object.v1.finalized",
            },
        ]
        destination = {
            "cloudRun": {
                "service": "my-service",
                "path": "/handler",
                "region": "us-central1",
            },
        }

        trigger = service.create_trigger(
            LOCATION,
            TRIGGER_NAME,
            event_filters=event_filters,
            destination=destination,
            service_account="trigger-sa@test-project.iam.gserviceaccount.com",
            labels={"env": "test"},
        )

        mock_triggers.create.assert_called_once_with(
            parent=LOCATION_PATH,
            body={
                "name": TRIGGER_PATH,
                "eventFilters": event_filters,
                "destination": destination,
                "serviceAccount": "trigger-sa@test-project.iam.gserviceaccount.com",
                "labels": {"env": "test"},
            },
            triggerId=TRIGGER_NAME,
        )
        assert isinstance(trigger, EventarcTrigger)
        assert trigger.name == TRIGGER_NAME

    def test_create_trigger_minimal(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test creating a trigger with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_triggers.create.return_value = mock_request
        mock_request.execute.return_value = sample_trigger_response

        event_filters = [
            {"attribute": "type", "value": "google.cloud.audit.log.v1.written"},
        ]
        destination = {"cloudRun": {"service": "my-service", "region": "us-central1"}}

        trigger = service.create_trigger(
            LOCATION, TRIGGER_NAME, event_filters, destination
        )

        mock_triggers.create.assert_called_once_with(
            parent=LOCATION_PATH,
            body={
                "name": TRIGGER_PATH,
                "eventFilters": event_filters,
                "destination": destination,
            },
            triggerId=TRIGGER_NAME,
        )
        assert isinstance(trigger, EventarcTrigger)

    def test_create_trigger_already_exists(self, service, mock_triggers):
        """Test creating a trigger that already exists."""
        mock_request = mock.MagicMock()
        mock_triggers.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_trigger(
                LOCATION,
                TRIGGER_NAME,
                event_filters=[{"attribute": "type", "value": "test"}],
                destination={"cloudRun": {"service": "svc", "region": "us-central1"}},
            )


class TestUpdateTrigger:
    def test_update_trigger(
        self, service, mock_triggers, sample_trigger_response
    ):
        """Test updating a trigger."""
        mock_request = mock.MagicMock()
        mock_triggers.patch.return_value = mock_request
        mock_request.execute.return_value = sample_trigger_response

        update_fields = {
            "destination": {
                "cloudRun": {
                    "service": "new-service",
                    "region": "us-central1",
                },
            },
        }
        trigger = service.update_trigger(
            LOCATION, TRIGGER_NAME, "destination", update_fields
        )

        mock_triggers.patch.assert_called_once_with(
            name=TRIGGER_PATH,
            body={
                "name": TRIGGER_PATH,
                "destination": update_fields["destination"],
            },
            updateMask="destination",
        )
        assert isinstance(trigger, EventarcTrigger)

    def test_update_trigger_not_found(self, service, mock_triggers):
        """Test updating a trigger that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_triggers.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_trigger(
                LOCATION,
                TRIGGER_NAME,
                "destination",
                {"destination": {"cloudRun": {"service": "svc", "region": "us-central1"}}},
            )


class TestDeleteTrigger:
    def test_delete_trigger(self, service, mock_triggers):
        """Test deleting a trigger."""
        mock_request = mock.MagicMock()
        mock_triggers.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_trigger(LOCATION, TRIGGER_NAME)

        mock_triggers.delete.assert_called_once_with(name=TRIGGER_PATH)
        assert result is True

    def test_delete_trigger_not_found(self, service, mock_triggers):
        """Test deleting a trigger that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_triggers.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_trigger(LOCATION, TRIGGER_NAME)


class TestEventarcTriggerModel:
    def test_from_api_response(self, sample_trigger_response):
        """Test creating an EventarcTrigger from API response."""
        trigger = EventarcTrigger.from_api_response(sample_trigger_response)

        assert trigger.name == TRIGGER_NAME
        assert trigger.project == PROJECT_ID
        assert trigger.location == LOCATION
        assert trigger.id == TRIGGER_PATH
        assert trigger.type == "eventarc.trigger"
        assert len(trigger.event_filters) == 2
        assert trigger.event_filters[0]["attribute"] == "type"
        assert trigger.destination == sample_trigger_response["destination"]
        assert trigger.transport == sample_trigger_response["transport"]
        assert trigger.service_account == (
            "trigger-sa@test-project.iam.gserviceaccount.com"
        )
        assert trigger.channel == (
            "projects/test-project/locations/us-central1/channels/my-channel"
        )
        assert trigger.conditions is not None

    def test_from_api_response_minimal(self):
        """Test creating an EventarcTrigger from minimal API response."""
        response = {"name": TRIGGER_PATH}
        trigger = EventarcTrigger.from_api_response(response)

        assert trigger.name == TRIGGER_NAME
        assert trigger.event_filters == []
        assert trigger.destination == {}
        assert trigger.transport is None
        assert trigger.service_account is None
        assert trigger.channel is None
        assert trigger.conditions is None

    def test_get_tag(self, sample_trigger_response):
        """Test getting tags from an EventarcTrigger."""
        trigger = EventarcTrigger.from_api_response(sample_trigger_response)

        assert trigger.get_tag("env") == "test"
        assert trigger.get_tag("team") == "platform"
        assert trigger.get_tag("missing") == ""
        assert trigger.get_tag("missing", "default") == "default"


class TestPathFormatting:
    def test_format_trigger_path(self, service):
        """Test trigger path formatting."""
        assert (
            service._format_trigger_path(LOCATION, TRIGGER_NAME)
            == TRIGGER_PATH
        )

    def test_format_trigger_path_already_formatted(self, service):
        """Test that already-formatted trigger paths are returned as-is."""
        assert (
            service._format_trigger_path(LOCATION, TRIGGER_PATH)
            == TRIGGER_PATH
        )

    def test_format_location_path(self, service):
        """Test location path formatting."""
        assert service._format_location_path(LOCATION) == LOCATION_PATH

    def test_format_location_path_all(self, service):
        """Test location path formatting with wildcard."""
        assert (
            service._format_location_path("-")
            == f"projects/{PROJECT_ID}/locations/-"
        )
