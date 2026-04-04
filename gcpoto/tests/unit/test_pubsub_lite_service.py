"""Tests for Pub/Sub Lite service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.pubsub_lite import PubSubLiteService
from gcpoto.models.pubsub_lite import LiteTopic, LiteSubscription
from gcpoto.exceptions import ResourceNotFoundError, APIError


PROJECT_ID = "test-project"
LOCATION = "us-central1-a"
TOPIC_ID = "my-lite-topic"
SUBSCRIPTION_ID = "my-lite-subscription"


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_topics = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.topics.return_value = (
            mock_topics
        )

        mock_subscriptions = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.subscriptions.return_value = (
            mock_subscriptions
        )

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a PubSubLiteService with mocked client."""
    return PubSubLiteService(project_id=PROJECT_ID)


@pytest.fixture
def mock_topics(mock_google_client):
    """Shortcut to mock topics resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .topics.return_value
    )


@pytest.fixture
def mock_subscriptions(mock_google_client):
    """Shortcut to mock subscriptions resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .subscriptions.return_value
    )


@pytest.fixture
def sample_topic_response():
    """Sample topic API response."""
    return {
        "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/topics/{TOPIC_ID}",
        "partitionConfig": {
            "count": 2,
            "capacity": {
                "publishMibPerSec": 4,
                "subscribeMibPerSec": 8,
            },
        },
        "retentionConfig": {
            "perPartitionBytes": "32212254720",
            "period": "86400s",
        },
        "reservationConfig": {
            "throughputReservation": f"projects/{PROJECT_ID}/locations/{LOCATION}/reservations/my-reservation",
        },
    }


@pytest.fixture
def sample_subscription_response():
    """Sample subscription API response."""
    return {
        "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/subscriptions/{SUBSCRIPTION_ID}",
        "topic": f"projects/{PROJECT_ID}/locations/{LOCATION}/topics/{TOPIC_ID}",
        "deliveryConfig": {
            "deliveryRequirement": "DELIVER_AFTER_STORED",
        },
    }


class TestPubSubLiteServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the PubSubLiteService."""
        from googleapiclient.discovery import build

        svc = PubSubLiteService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with(
            "pubsublite", "v1/admin", credentials=None
        )


class TestListTopics:
    def test_list_topics(
        self, service, mock_topics, sample_topic_response
    ):
        """Test listing topics."""
        mock_request = mock.MagicMock()
        mock_topics.list.return_value = mock_request
        mock_request.execute.return_value = {
            "topics": [sample_topic_response]
        }
        mock_topics.list_next.return_value = None

        results = service.list_topics(LOCATION)

        mock_topics.list.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}"
        )
        assert len(results) == 1
        assert isinstance(results[0], LiteTopic)
        assert results[0].partition_config["count"] == 2

    def test_list_topics_empty(self, service, mock_topics):
        """Test listing topics when none exist."""
        mock_request = mock.MagicMock()
        mock_topics.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_topics.list_next.return_value = None

        results = service.list_topics(LOCATION)
        assert len(results) == 0


class TestGetTopic:
    def test_get_topic(
        self, service, mock_topics, sample_topic_response
    ):
        """Test getting a specific topic."""
        mock_request = mock.MagicMock()
        mock_topics.get.return_value = mock_request
        mock_request.execute.return_value = sample_topic_response

        result = service.get_topic(LOCATION, TOPIC_ID)

        assert isinstance(result, LiteTopic)
        assert result.partition_config["count"] == 2
        assert result.retention_config["period"] == "86400s"
        assert result.reservation_config is not None

    def test_get_topic_not_found(self, service, mock_topics):
        """Test getting a topic that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_topics.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_topic(LOCATION, TOPIC_ID)


class TestCreateTopic:
    def test_create_topic(
        self, service, mock_topics, sample_topic_response
    ):
        """Test creating a new topic."""
        mock_request = mock.MagicMock()
        mock_topics.create.return_value = mock_request
        mock_request.execute.return_value = sample_topic_response

        partition_config = {"count": 2, "capacity": {"publishMibPerSec": 4}}
        retention_config = {"perPartitionBytes": "32212254720"}

        result = service.create_topic(
            LOCATION, TOPIC_ID, partition_config, retention_config
        )

        mock_topics.create.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}",
            topicId=TOPIC_ID,
            body={
                "partitionConfig": partition_config,
                "retentionConfig": retention_config,
            },
        )
        assert isinstance(result, LiteTopic)

    def test_create_topic_with_reservation(
        self, service, mock_topics, sample_topic_response
    ):
        """Test creating a topic with reservation config."""
        mock_request = mock.MagicMock()
        mock_topics.create.return_value = mock_request
        mock_request.execute.return_value = sample_topic_response

        partition_config = {"count": 2}
        retention_config = {"perPartitionBytes": "32212254720"}
        reservation_config = {"throughputReservation": "reservations/my-res"}

        result = service.create_topic(
            LOCATION,
            TOPIC_ID,
            partition_config,
            retention_config,
            reservation_config=reservation_config,
        )

        call_body = mock_topics.create.call_args[1]["body"]
        assert call_body["reservationConfig"] == reservation_config
        assert isinstance(result, LiteTopic)

    def test_create_topic_api_error(self, service, mock_topics):
        """Test creating a topic when API returns an error."""
        mock_request = mock.MagicMock()
        mock_topics.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_topic(LOCATION, TOPIC_ID, {}, {})


class TestUpdateTopic:
    def test_update_topic(
        self, service, mock_topics, sample_topic_response
    ):
        """Test updating a topic."""
        mock_request = mock.MagicMock()
        mock_topics.patch.return_value = mock_request
        mock_request.execute.return_value = sample_topic_response

        result = service.update_topic(
            LOCATION,
            TOPIC_ID,
            "partitionConfig.count",
            {"partitionConfig": {"count": 4}},
        )

        mock_topics.patch.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/topics/{TOPIC_ID}",
            updateMask="partitionConfig.count",
            body={
                "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/topics/{TOPIC_ID}",
                "partitionConfig": {"count": 4},
            },
        )
        assert isinstance(result, LiteTopic)

    def test_update_topic_not_found(self, service, mock_topics):
        """Test updating a topic that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_topics.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_topic(LOCATION, TOPIC_ID, "partitionConfig", {})


class TestDeleteTopic:
    def test_delete_topic(self, service, mock_topics):
        """Test deleting a topic."""
        mock_topics.delete.return_value.execute.return_value = {}

        result = service.delete_topic(LOCATION, TOPIC_ID)
        assert result is True

    def test_delete_topic_not_found(self, service, mock_topics):
        """Test deleting a topic that doesn't exist."""
        mock_topics.delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_topic(LOCATION, TOPIC_ID)


class TestListSubscriptions:
    def test_list_subscriptions(
        self, service, mock_subscriptions, sample_subscription_response
    ):
        """Test listing subscriptions."""
        mock_request = mock.MagicMock()
        mock_subscriptions.list.return_value = mock_request
        mock_request.execute.return_value = {
            "subscriptions": [sample_subscription_response]
        }
        mock_subscriptions.list_next.return_value = None

        results = service.list_subscriptions(LOCATION)

        mock_subscriptions.list.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}"
        )
        assert len(results) == 1
        assert isinstance(results[0], LiteSubscription)
        assert results[0].topic.endswith(TOPIC_ID)

    def test_list_subscriptions_empty(
        self, service, mock_subscriptions
    ):
        """Test listing subscriptions when none exist."""
        mock_request = mock.MagicMock()
        mock_subscriptions.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_subscriptions.list_next.return_value = None

        results = service.list_subscriptions(LOCATION)
        assert len(results) == 0


class TestGetSubscription:
    def test_get_subscription(
        self, service, mock_subscriptions, sample_subscription_response
    ):
        """Test getting a specific subscription."""
        mock_request = mock.MagicMock()
        mock_subscriptions.get.return_value = mock_request
        mock_request.execute.return_value = sample_subscription_response

        result = service.get_subscription(LOCATION, SUBSCRIPTION_ID)

        assert isinstance(result, LiteSubscription)
        assert result.topic.endswith(TOPIC_ID)
        assert result.delivery_config is not None

    def test_get_subscription_not_found(
        self, service, mock_subscriptions
    ):
        """Test getting a subscription that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_subscriptions.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_subscription(LOCATION, SUBSCRIPTION_ID)


class TestCreateSubscription:
    def test_create_subscription(
        self, service, mock_subscriptions, sample_subscription_response
    ):
        """Test creating a new subscription."""
        mock_request = mock.MagicMock()
        mock_subscriptions.create.return_value = mock_request
        mock_request.execute.return_value = sample_subscription_response

        topic = f"projects/{PROJECT_ID}/locations/{LOCATION}/topics/{TOPIC_ID}"
        result = service.create_subscription(
            LOCATION, SUBSCRIPTION_ID, topic
        )

        mock_subscriptions.create.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}",
            subscriptionId=SUBSCRIPTION_ID,
            body={"topic": topic},
        )
        assert isinstance(result, LiteSubscription)

    def test_create_subscription_with_delivery_config(
        self, service, mock_subscriptions, sample_subscription_response
    ):
        """Test creating a subscription with delivery config."""
        mock_request = mock.MagicMock()
        mock_subscriptions.create.return_value = mock_request
        mock_request.execute.return_value = sample_subscription_response

        topic = f"projects/{PROJECT_ID}/locations/{LOCATION}/topics/{TOPIC_ID}"
        delivery_config = {
            "deliveryRequirement": "DELIVER_AFTER_STORED"
        }

        result = service.create_subscription(
            LOCATION,
            SUBSCRIPTION_ID,
            topic,
            delivery_config=delivery_config,
        )

        call_body = mock_subscriptions.create.call_args[1]["body"]
        assert call_body["deliveryConfig"] == delivery_config
        assert isinstance(result, LiteSubscription)

    def test_create_subscription_api_error(
        self, service, mock_subscriptions
    ):
        """Test creating a subscription when API returns an error."""
        mock_request = mock.MagicMock()
        mock_subscriptions.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_subscription(
                LOCATION, SUBSCRIPTION_ID, "bad-topic"
            )


class TestUpdateSubscription:
    def test_update_subscription(
        self, service, mock_subscriptions, sample_subscription_response
    ):
        """Test updating a subscription."""
        mock_request = mock.MagicMock()
        mock_subscriptions.patch.return_value = mock_request
        mock_request.execute.return_value = sample_subscription_response

        result = service.update_subscription(
            LOCATION,
            SUBSCRIPTION_ID,
            "deliveryConfig",
            {"deliveryConfig": {"deliveryRequirement": "DELIVER_IMMEDIATELY"}},
        )

        assert isinstance(result, LiteSubscription)

    def test_update_subscription_not_found(
        self, service, mock_subscriptions
    ):
        """Test updating a subscription that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_subscriptions.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_subscription(
                LOCATION, SUBSCRIPTION_ID, "deliveryConfig", {}
            )


class TestDeleteSubscription:
    def test_delete_subscription(self, service, mock_subscriptions):
        """Test deleting a subscription."""
        mock_subscriptions.delete.return_value.execute.return_value = {}

        result = service.delete_subscription(LOCATION, SUBSCRIPTION_ID)
        assert result is True

    def test_delete_subscription_not_found(
        self, service, mock_subscriptions
    ):
        """Test deleting a subscription that doesn't exist."""
        mock_subscriptions.delete.return_value.execute.side_effect = (
            HttpError(
                resp=mock.MagicMock(status=404), content=b"Not found"
            )
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_subscription(LOCATION, SUBSCRIPTION_ID)


class TestLiteTopicModel:
    def test_from_api_response(self, sample_topic_response):
        """Test creating a LiteTopic from API response."""
        topic = LiteTopic.from_api_response(sample_topic_response)

        assert topic.id == TOPIC_ID
        assert topic.location == LOCATION
        assert topic.project == PROJECT_ID
        assert topic.partition_config["count"] == 2
        assert topic.retention_config["period"] == "86400s"
        assert topic.reservation_config is not None
        assert topic.type == "pubsublite.topic"

    def test_from_api_response_minimal(self):
        """Test creating a LiteTopic from minimal API response."""
        response = {
            "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/topics/minimal"
        }
        topic = LiteTopic.from_api_response(response)

        assert topic.id == "minimal"
        assert topic.partition_config == {}
        assert topic.retention_config == {}
        assert topic.reservation_config is None

    def test_to_dict(self, sample_topic_response):
        """Test converting a LiteTopic to dictionary."""
        topic = LiteTopic.from_api_response(sample_topic_response)
        result = topic.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == TOPIC_ID
        assert result["location"] == LOCATION


class TestLiteSubscriptionModel:
    def test_from_api_response(self, sample_subscription_response):
        """Test creating a LiteSubscription from API response."""
        sub = LiteSubscription.from_api_response(
            sample_subscription_response
        )

        assert sub.id == SUBSCRIPTION_ID
        assert sub.location == LOCATION
        assert sub.project == PROJECT_ID
        assert sub.topic.endswith(TOPIC_ID)
        assert sub.delivery_config is not None
        assert sub.type == "pubsublite.subscription"

    def test_from_api_response_minimal(self):
        """Test creating a LiteSubscription from minimal API response."""
        response = {
            "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/subscriptions/minimal"
        }
        sub = LiteSubscription.from_api_response(response)

        assert sub.id == "minimal"
        assert sub.topic == ""
        assert sub.delivery_config is None

    def test_to_dict(self, sample_subscription_response):
        """Test converting a LiteSubscription to dictionary."""
        sub = LiteSubscription.from_api_response(
            sample_subscription_response
        )
        result = sub.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == SUBSCRIPTION_ID
        assert result["location"] == LOCATION
