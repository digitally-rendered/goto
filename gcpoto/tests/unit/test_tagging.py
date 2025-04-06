"""Tests for resource tagging functionality."""

from unittest import mock

import pytest

from gcpoto.models.base import GCPResource
from gcpoto.services.base import GCPService
from gcpoto.models.pubsub import PubSubTopic, PubSubSubscription
from gcpoto.services.pubsub import PubSubService


def test_base_model_tags():
    """Test that the base model supports tags."""
    resource = GCPResource(
        id="test-id",
        name="test-resource",
        type="test.type",
        project="test-project",
        tags={"env": "test", "owner": "team-a"}
    )
    
    assert resource.tags == {"env": "test", "owner": "team-a"}
    
    # Test JSON serialization
    json_data = resource.model_dump()
    assert "tags" in json_data
    assert json_data["tags"] == {"env": "test", "owner": "team-a"}


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
    }


@pytest.fixture
def sample_subscription_response():
    """Sample Pub/Sub subscription API response."""
    return {
        "name": "projects/test-project/subscriptions/test-subscription",
        "topic": "projects/test-project/topics/test-topic",
        "labels": {"env": "test", "purpose": "testing"},
    }


def test_process_tags():
    """Test that the _process_tags method correctly processes tags."""
    # Mock the service creation to avoid API calls
    with mock.patch("googleapiclient.discovery.build"):
        service = GCPService(project_id="test-project", service_name="test")
    
    # Test with empty body and tags
    body = {}
    result = service._process_tags(body, None)
    assert result == {}
    
    # Test with empty body and non-empty tags
    body = {}
    tags = {"env": "test", "owner": "team-a"}
    result = service._process_tags(body, tags)
    assert result["labels"] == {"env": "test", "owner": "team-a"}
    
    # Test with existing labels and new tags
    body = {"labels": {"existing": "value"}}
    tags = {"env": "test", "owner": "team-a"}
    result = service._process_tags(body, tags)
    assert result["labels"] == {"existing": "value", "env": "test", "owner": "team-a"}


def test_pubsub_topic_create_with_tags(mock_google_client, mock_publisher_client, mock_subscriber_client, sample_topic_response):
    """Test creating a Pub/Sub topic with tags."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_create = mock_google_client.projects.return_value.topics.return_value.create
    mock_create.return_value = mock_request
    mock_request.execute.return_value = sample_topic_response
    
    # Create service and call create_topic with tags
    service = PubSubService(project_id="test-project")
    tags = {"env": "test", "cost-center": "12345", "team": "platform"}
    
    topic = service.create_topic(
        topic_name="test-topic",
        tags=tags
    )
    
    # Verify the API call was made correctly with tags incorporated into labels
    mock_create.assert_called_once()
    call_args = mock_create.call_args[1]
    assert "body" in call_args
    body = call_args["body"]
    assert "labels" in body
    
    # All tags should be in the labels
    for key, value in tags.items():
        assert key in body["labels"]
        assert body["labels"][key] == value
    
    # Tags should be set on the returned topic object
    assert topic.tags == tags


def test_pubsub_subscription_create_with_tags(mock_google_client, mock_publisher_client, mock_subscriber_client, sample_subscription_response):
    """Test creating a Pub/Sub subscription with tags."""
    # Setup mock response
    mock_request = mock.MagicMock()
    mock_create = mock_google_client.projects.return_value.subscriptions.return_value.create
    mock_create.return_value = mock_request
    mock_request.execute.return_value = sample_subscription_response
    
    # Create service and call create_subscription with tags
    service = PubSubService(project_id="test-project")
    tags = {"env": "test", "cost-center": "12345", "team": "platform"}
    
    subscription = service.create_subscription(
        subscription_name="test-subscription",
        topic_name="test-topic",
        tags=tags
    )
    
    # Verify the API call was made correctly with tags incorporated into labels
    mock_create.assert_called_once()
    call_args = mock_create.call_args[1]
    assert "body" in call_args
    body = call_args["body"]
    assert "labels" in body
    
    # All tags should be in the labels
    for key, value in tags.items():
        assert key in body["labels"]
        assert body["labels"][key] == value
    
    # Tags should be set on the returned subscription object
    assert subscription.tags == tags


def test_tags_with_labels(mock_google_client, mock_publisher_client, mock_subscriber_client):
    """Test that tags and labels can coexist."""
    service = PubSubService(project_id="test-project")
    
    # Simulate API call, just testing the body
    labels = {"env": "prod", "team": "backend"}
    tags = {"cost-center": "12345", "compliance": "pci-dss"}
    
    # Get the body that would be sent in an API call
    body = {}
    if labels:
        body["labels"] = labels
    
    body = service._process_tags(body, tags)
    
    # Both labels and tags should be merged in the labels field
    assert "labels" in body
    assert body["labels"] == {
        "env": "prod", 
        "team": "backend", 
        "cost-center": "12345", 
        "compliance": "pci-dss"
    }
