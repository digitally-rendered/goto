"""Tests for Pub/Sub service."""

import json
from unittest import mock

import pytest
from google.cloud import pubsub_v1
from googleapiclient.errors import HttpError

from gcpoto.services.pubsub import PubSubService
from gcpoto.models.pubsub import PubSubTopic, PubSubSubscription


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        # Create mock service
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        
        # Set up projects().topics() chain
        mock_topics = mock.MagicMock()
        mock_service.projects.return_value.topics.return_value = mock_topics
        
        # Set up projects().subscriptions() chain
        mock_subscriptions = mock.MagicMock()
        mock_service.projects.return_value.subscriptions.return_value = mock_subscriptions
        
        # Set up projects().topics().subscriptions() chain
        mock_topic_subscriptions = mock.MagicMock()
        mock_service.projects.return_value.topics.return_value.subscriptions.return_value = mock_topic_subscriptions
        
        yield mock_service


@pytest.fixture
def mock_publisher_client():
    """Mock Pub/Sub publisher client."""
    with mock.patch("google.cloud.pubsub_v1.PublisherClient") as mock_publisher:
        mock_instance = mock.MagicMock()
        mock_publisher.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_subscriber_client():
    """Mock Pub/Sub subscriber client."""
    with mock.patch("google.cloud.pubsub_v1.SubscriberClient") as mock_subscriber:
        mock_instance = mock.MagicMock()
        mock_subscriber.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_topic_response():
    """Sample Pub/Sub topic API response."""
    return {
        "name": "projects/test-project/topics/test-topic",
        "labels": {"env": "test", "owner": "test-team"},
        "messageStoragePolicy": {
            "allowedPersistenceRegions": ["us-central1", "us-east1"]
        },
        "kmsKeyName": "projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key",
        "schemaSettings": {
            "schema": "projects/test-project/schemas/test-schema",
            "encoding": "JSON"
        },
        "messageRetentionDuration": "86400s",
        "satisfiesPzs": False
    }


@pytest.fixture
def sample_subscription_response():
    """Sample Pub/Sub subscription API response."""
    return {
        "name": "projects/test-project/subscriptions/test-subscription",
        "topic": "projects/test-project/topics/test-topic",
        "pushConfig": {
            "pushEndpoint": "https://example.com/push",
            "attributes": {"x-goog-version": "v1"}
        },
        "ackDeadlineSeconds": 10,
        "retainAckedMessages": True,
        "messageRetentionDuration": "604800s",
        "labels": {"env": "test", "purpose": "testing"},
        "expirationPolicy": {
            "ttl": "2592000s"
        },
        "filter": "attributes.event_type = \"test\"",
        "deadLetterPolicy": {
            "deadLetterTopic": "projects/test-project/topics/dead-letter",
            "maxDeliveryAttempts": 5
        },
        "retryPolicy": {
            "minimumBackoff": "10s",
            "maximumBackoff": "600s"
        },
        "detached": False,
        "enableMessageOrdering": True
    }


def test_init(mock_google_client, mock_publisher_client, mock_subscriber_client):
    """Test initializing the PubSubService."""
    from googleapiclient.discovery import build
    
    service = PubSubService(project_id="test-project")
    
    # Assert that the service was initialized correctly
    assert service.project_id == "test-project"
    build.assert_called_once_with('pubsub', 'v1', credentials=None)
    
    # Assert that the publisher and subscriber clients were initialized
    pubsub_v1.PublisherClient.assert_called_once()
    pubsub_v1.SubscriberClient.assert_called_once()


def test_list_resources(mock_google_client, sample_topic_response):
    """Test listing Pub/Sub topics."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_list = mock_google_client.projects.return_value.topics.return_value.list
    mock_list.return_value = mock_request
    
    # Mock list_next for pagination
    mock_list_next = mock_google_client.projects.return_value.topics.return_value.list_next
    mock_list_next.side_effect = [mock.MagicMock(), None]
    
    # First page of results
    mock_request.execute.return_value = {
        "topics": [sample_topic_response, sample_topic_response]
    }
    
    # Create service and call list_resources
    service = PubSubService(project_id="test-project")
    topics = service.list_resources()
    
    # Verify the API call was made correctly
    mock_list.assert_called_once_with(project="projects/test-project")
    
    # Verify the topics were parsed correctly
    assert len(topics) == 2
    assert isinstance(topics[0], PubSubTopic)
    assert topics[0].name == "test-topic"
    assert topics[0].project == "test-project"


def test_get_topic(mock_google_client, sample_topic_response):
    """Test getting a Pub/Sub topic."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_get = mock_google_client.projects.return_value.topics.return_value.get
    mock_get.return_value = mock_request
    mock_request.execute.return_value = sample_topic_response
    
    # Create service and call get_topic
    service = PubSubService(project_id="test-project")
    topic = service.get_topic("test-topic")
    
    # Verify the API call was made correctly
    mock_get.assert_called_once_with(topic="projects/test-project/topics/test-topic")
    
    # Verify the topic was parsed correctly
    assert isinstance(topic, PubSubTopic)
    assert topic.name == "test-topic"
    assert topic.project == "test-project"
    assert topic.kms_key_name == "projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key"
    
    # Test with full path
    service.get_topic("projects/test-project/topics/test-topic")
    mock_get.assert_called_with(topic="projects/test-project/topics/test-topic")


def test_create_topic(mock_google_client, sample_topic_response):
    """Test creating a Pub/Sub topic."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_create = mock_google_client.projects.return_value.topics.return_value.create
    mock_create.return_value = mock_request
    mock_request.execute.return_value = sample_topic_response
    
    # Create service and call create_topic
    service = PubSubService(project_id="test-project")
    topic = service.create_topic(
        topic_name="test-topic",
        labels={"env": "test"},
        kms_key_name="test-key",
        message_storage_policy={"allowedPersistenceRegions": ["us-central1"]},
        message_retention_duration="86400s"
    )
    
    # Verify the API call was made correctly
    mock_create.assert_called_once_with(
        name="projects/test-project/topics/test-topic",
        body={
            "labels": {"env": "test"},
            "kmsKeyName": "test-key",
            "messageStoragePolicy": {"allowedPersistenceRegions": ["us-central1"]},
            "messageRetentionDuration": "86400s"
        }
    )
    
    # Verify the topic was parsed correctly
    assert isinstance(topic, PubSubTopic)
    assert topic.name == "test-topic"
    assert topic.project == "test-project"
    
    # Test with full path
    service.create_topic("projects/test-project/topics/test-topic")
    mock_create.assert_called_with(
        name="projects/test-project/topics/test-topic",
        body={}
    )
    
    # Test with conflict error
    mock_request.execute.side_effect = HttpError(
        resp=mock.MagicMock(status=409),
        content=b"Topic already exists"
    )
    
    with pytest.raises(ValueError, match="Topic 'test-topic' already exists"):
        service.create_topic("test-topic")


def test_delete_topic(mock_google_client):
    """Test deleting a Pub/Sub topic."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_delete = mock_google_client.projects.return_value.topics.return_value.delete
    mock_delete.return_value = mock_request
    mock_request.execute.return_value = {}
    
    # Create service and call delete_topic
    service = PubSubService(project_id="test-project")
    result = service.delete_topic("test-topic")
    
    # Verify the API call was made correctly
    mock_delete.assert_called_once_with(topic="projects/test-project/topics/test-topic")
    
    # Verify the result
    assert result is True
    
    # Test with full path
    service.delete_topic("projects/test-project/topics/test-topic")
    mock_delete.assert_called_with(topic="projects/test-project/topics/test-topic")


def test_publish_message(mock_google_client, mock_publisher_client):
    """Test publishing a message to a Pub/Sub topic."""
    # Setup mock response
    future = mock.MagicMock()
    future.result.return_value = "message-id-123"
    mock_publisher_client.publish.return_value = future
    
    # Create service and call publish_message
    service = PubSubService(project_id="test-project")
    message_id = service.publish_message(
        topic_name="test-topic",
        data="test message",
        attributes={"key": "value"}
    )
    
    # Verify the publisher client was called correctly
    mock_publisher_client.publish.assert_called_once_with(
        "projects/test-project/topics/test-topic",
        b"test message",
        key="value"
    )
    
    # Verify the result
    assert message_id == "message-id-123"
    
    # Test with binary data
    binary_data = b"binary message"
    service.publish_message("test-topic", binary_data)
    mock_publisher_client.publish.assert_called_with(
        "projects/test-project/topics/test-topic",
        binary_data
    )
    
    # Test with full path
    service.publish_message("projects/test-project/topics/test-topic", "test message")
    mock_publisher_client.publish.assert_called_with(
        "projects/test-project/topics/test-topic",
        b"test message"
    )


def test_list_subscriptions_by_project(mock_google_client, sample_subscription_response):
    """Test listing Pub/Sub subscriptions in a project."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_list = mock_google_client.projects.return_value.subscriptions.return_value.list
    mock_list.return_value = mock_request
    
    # Mock list_next for pagination
    mock_list_next = mock_google_client.projects.return_value.subscriptions.return_value.list_next
    mock_list_next.side_effect = [mock.MagicMock(), None]
    
    # First page of results
    mock_request.execute.return_value = {
        "subscriptions": [sample_subscription_response, sample_subscription_response]
    }
    
    # Create service and call list_subscriptions
    service = PubSubService(project_id="test-project")
    subscriptions = service.list_subscriptions()
    
    # Verify the API call was made correctly
    mock_list.assert_called_once_with(project="projects/test-project")
    
    # Verify the subscriptions were parsed correctly
    assert len(subscriptions) == 2
    assert isinstance(subscriptions[0], PubSubSubscription)
    assert subscriptions[0].name == "test-subscription"
    assert subscriptions[0].topic == "test-topic"
    assert subscriptions[0].project == "test-project"


def test_list_subscriptions_by_topic(mock_google_client, sample_subscription_response):
    """Test listing Pub/Sub subscriptions for a specific topic."""
    # Setup mock response for listing subscriptions by topic
    mock_request = mock.MagicMock()
    mock_list = mock_google_client.projects.return_value.topics.return_value.subscriptions.return_value.list
    mock_list.return_value = mock_request
    
    # Mock list_next for pagination
    mock_list_next = mock_google_client.projects.return_value.topics.return_value.subscriptions.return_value.list_next
    mock_list_next.side_effect = [mock.MagicMock(), None]
    
    # Setup response for topic subscriptions list
    mock_request.execute.return_value = {
        "subscriptions": [
            "projects/test-project/subscriptions/test-subscription",
            "projects/test-project/subscriptions/test-subscription-2"
        ]
    }
    
    # Setup mock response for getting subscription details
    mock_get_request = mock.MagicMock()
    mock_get = mock_google_client.projects.return_value.subscriptions.return_value.get
    mock_get.return_value = mock_get_request
    mock_get_request.execute.return_value = sample_subscription_response
    
    # Create service and call list_subscriptions with topic
    service = PubSubService(project_id="test-project")
    subscriptions = service.list_subscriptions("test-topic")
    
    # Verify the API calls were made correctly
    mock_list.assert_called_once_with(topic="projects/test-project/topics/test-topic")
    mock_get.assert_called_with(subscription="projects/test-project/subscriptions/test-subscription-2")
    
    # Verify the subscriptions were parsed correctly
    assert len(subscriptions) == 2
    assert isinstance(subscriptions[0], PubSubSubscription)
    assert subscriptions[0].name == "test-subscription"
    
    # Test with full path
    service.list_subscriptions("projects/test-project/topics/test-topic")
    mock_list.assert_called_with(topic="projects/test-project/topics/test-topic")


def test_get_subscription(mock_google_client, sample_subscription_response):
    """Test getting a Pub/Sub subscription."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_get = mock_google_client.projects.return_value.subscriptions.return_value.get
    mock_get.return_value = mock_request
    mock_request.execute.return_value = sample_subscription_response
    
    # Create service and call get_subscription
    service = PubSubService(project_id="test-project")
    subscription = service.get_subscription("test-subscription")
    
    # Verify the API call was made correctly
    mock_get.assert_called_once_with(
        subscription="projects/test-project/subscriptions/test-subscription"
    )
    
    # Verify the subscription was parsed correctly
    assert isinstance(subscription, PubSubSubscription)
    assert subscription.name == "test-subscription"
    assert subscription.topic == "test-topic"
    assert subscription.project == "test-project"
    assert subscription.push_config.push_endpoint == "https://example.com/push"
    
    # Test with full path
    service.get_subscription("projects/test-project/subscriptions/test-subscription")
    mock_get.assert_called_with(
        subscription="projects/test-project/subscriptions/test-subscription"
    )


def test_create_subscription(mock_google_client, sample_subscription_response):
    """Test creating a Pub/Sub subscription."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_create = mock_google_client.projects.return_value.subscriptions.return_value.create
    mock_create.return_value = mock_request
    mock_request.execute.return_value = sample_subscription_response
    
    # Create service and call create_subscription
    service = PubSubService(project_id="test-project")
    subscription = service.create_subscription(
        subscription_name="test-subscription",
        topic_name="test-topic",
        ack_deadline_seconds=10,
        push_config={"pushEndpoint": "https://example.com/push"},
        retain_acked_messages=True,
        message_retention_duration="604800s",
        labels={"env": "test"},
        enable_message_ordering=True,
        filter_expr="attributes.event_type = \"test\""
    )
    
    # Verify the API call was made correctly
    mock_create.assert_called_once_with(
        name="projects/test-project/subscriptions/test-subscription",
        body={
            "topic": "projects/test-project/topics/test-topic",
            "ackDeadlineSeconds": 10,
            "pushConfig": {"pushEndpoint": "https://example.com/push"},
            "retainAckedMessages": True,
            "messageRetentionDuration": "604800s",
            "labels": {"env": "test"},
            "enableMessageOrdering": True,
            "filter": "attributes.event_type = \"test\""
        }
    )
    
    # Verify the subscription was parsed correctly
    assert isinstance(subscription, PubSubSubscription)
    assert subscription.name == "test-subscription"
    assert subscription.topic == "test-topic"
    assert subscription.project == "test-project"
    
    # Test with conflict error
    mock_request.execute.side_effect = HttpError(
        resp=mock.MagicMock(status=409),
        content=b"Subscription already exists"
    )
    
    with pytest.raises(ValueError, match="Subscription 'test-subscription' already exists"):
        service.create_subscription("test-subscription", "test-topic")


def test_delete_subscription(mock_google_client):
    """Test deleting a Pub/Sub subscription."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_delete = mock_google_client.projects.return_value.subscriptions.return_value.delete
    mock_delete.return_value = mock_request
    mock_request.execute.return_value = {}
    
    # Create service and call delete_subscription
    service = PubSubService(project_id="test-project")
    result = service.delete_subscription("test-subscription")
    
    # Verify the API call was made correctly
    mock_delete.assert_called_once_with(
        subscription="projects/test-project/subscriptions/test-subscription"
    )
    
    # Verify the result
    assert result is True
    
    # Test with full path
    service.delete_subscription("projects/test-project/subscriptions/test-subscription")
    mock_delete.assert_called_with(
        subscription="projects/test-project/subscriptions/test-subscription"
    )


def test_pull_messages(mock_google_client):
    """Test pulling messages from a Pub/Sub subscription."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_pull = mock_google_client.projects.return_value.subscriptions.return_value.pull
    mock_pull.return_value = mock_request
    
    mock_messages = [
        {
            "ackId": "ack-123",
            "message": {
                "messageId": "message-123",
                "data": "dGVzdCBtZXNzYWdl",  # base64 encoded "test message"
                "attributes": {"key": "value"}
            }
        }
    ]
    
    mock_request.execute.return_value = {
        "receivedMessages": mock_messages
    }
    
    # Create service and call pull_messages
    service = PubSubService(project_id="test-project")
    messages = service.pull_messages("test-subscription", max_messages=5, return_immediately=True)
    
    # Verify the API call was made correctly
    mock_pull.assert_called_once_with(
        subscription="projects/test-project/subscriptions/test-subscription",
        body={
            "maxMessages": 5,
            "returnImmediately": True
        }
    )
    
    # Verify the result
    assert messages == mock_messages
    
    # Test with empty response
    mock_request.execute.return_value = {}
    messages = service.pull_messages("test-subscription")
    assert messages == []


def test_acknowledge_messages(mock_google_client):
    """Test acknowledging messages from a Pub/Sub subscription."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_ack = mock_google_client.projects.return_value.subscriptions.return_value.acknowledge
    mock_ack.return_value = mock_request
    mock_request.execute.return_value = {}
    
    # Create service and call acknowledge_messages
    service = PubSubService(project_id="test-project")
    result = service.acknowledge_messages("test-subscription", ["ack-id-1", "ack-id-2"])
    
    # Verify the API call was made correctly
    mock_ack.assert_called_once_with(
        subscription="projects/test-project/subscriptions/test-subscription",
        body={
            "ackIds": ["ack-id-1", "ack-id-2"]
        }
    )
    
    # Verify the result
    assert result is True
