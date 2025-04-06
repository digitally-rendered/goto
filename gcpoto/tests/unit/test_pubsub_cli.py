"""Tests for Pub/Sub CLI commands."""

import json
from unittest import mock

import pytest
from click.testing import CliRunner

from gcpoto.cli.main import cli
from gcpoto.models.pubsub import PubSubTopic, PubSubSubscription


@pytest.fixture
def cli_runner():
    """Configure a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_pubsub_service():
    """Mock the PubSubService class."""
    with mock.patch("gcpoto.services.pubsub.PubSubService") as mock_service:
        mock_instance = mock.MagicMock()
        mock_service.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_topic():
    """Create a sample PubSubTopic for tests."""
    topic = PubSubTopic(
        id="projects/test-project/topics/test-topic",
        name="test-topic",
        project="test-project",
        type="pubsub.topic",
        labels={"env": "test", "owner": "test-team"},
        created="2023-04-05T12:00:00Z"
    )
    return topic


@pytest.fixture
def sample_subscription():
    """Create a sample PubSubSubscription for tests."""
    subscription = PubSubSubscription(
        id="projects/test-project/subscriptions/test-subscription",
        name="test-subscription",
        topic="test-topic",
        project="test-project",
        type="pubsub.subscription",
        ack_deadline_seconds=10,
        labels={"env": "test"},
        created="2023-04-05T12:00:00Z"
    )
    return subscription


def test_list_topics_command(cli_runner, mock_pubsub_service, sample_topic):
    """Test the 'list-topics' command."""
    mock_pubsub_service.list_resources.return_value = [sample_topic, sample_topic]
    
    result = cli_runner.invoke(
        cli, ["--project", "test-project", "pubsub", "list-topics", "--output", "json"]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.list_resources.assert_called_once()
    
    # Check for expected output in JSON format
    output = json.loads(result.output)
    assert len(output) == 2
    assert output[0]["name"] == "test-topic"
    assert output[0]["project"] == "test-project"
    
    # Test failure when project ID is missing
    result = cli_runner.invoke(cli, ["pubsub", "list-topics"])
    assert result.exit_code == 2
    assert "Project ID must be specified" in result.output


def test_get_topic_command(cli_runner, mock_pubsub_service, sample_topic):
    """Test the 'get-topic' command."""
    mock_pubsub_service.get_topic.return_value = sample_topic
    
    result = cli_runner.invoke(
        cli, ["--project", "test-project", "pubsub", "get-topic", "test-topic", "--output", "json"]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.get_topic.assert_called_once_with("test-topic")
    
    # Check for expected output in JSON format
    output = json.loads(result.output)
    assert output["name"] == "test-topic"
    assert output["project"] == "test-project"
    
    # Test failure when project ID is missing
    result = cli_runner.invoke(cli, ["pubsub", "get-topic", "test-topic"])
    assert result.exit_code == 2
    assert "Project ID must be specified" in result.output


def test_create_topic_command(cli_runner, mock_pubsub_service, sample_topic):
    """Test the 'create-topic' command."""
    mock_pubsub_service.create_topic.return_value = sample_topic
    
    result = cli_runner.invoke(
        cli, [
            "--project", "test-project", 
            "pubsub", "create-topic", 
            "test-topic",
            "--label", "env=test",
            "--label", "owner=test-team",
            "--kms-key", "test-key",
            "--message-retention", "P1D",
            "--region", "us-central1",
            "--region", "us-east1",
            "--output", "json"
        ]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.create_topic.assert_called_once_with(
        topic_name="test-topic",
        labels={"env": "test", "owner": "test-team"},
        kms_key_name="test-key",
        message_retention_duration="P1D",
        message_storage_policy={"allowedPersistenceRegions": ["us-central1", "us-east1"]}
    )
    
    # Check for expected output in JSON format
    output = json.loads(result.output)
    assert output["name"] == "test-topic"
    assert output["project"] == "test-project"
    
    # Test with malformed label
    result = cli_runner.invoke(
        cli, [
            "--project", "test-project", 
            "pubsub", "create-topic", 
            "test-topic",
            "--label", "malformed-label"
        ]
    )
    
    assert result.exit_code == 0
    assert "Warning: Ignoring malformed label 'malformed-label'" in result.output
    
    # Test failure when project ID is missing
    result = cli_runner.invoke(cli, ["pubsub", "create-topic", "test-topic"])
    assert result.exit_code == 2
    assert "Project ID must be specified" in result.output


def test_delete_topic_command(cli_runner, mock_pubsub_service):
    """Test the 'delete-topic' command."""
    mock_pubsub_service.delete_topic.return_value = True
    
    # Test with confirmation bypass
    result = cli_runner.invoke(
        cli, ["--project", "test-project", "pubsub", "delete-topic", "test-topic", "--yes"]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.delete_topic.assert_called_once_with("test-topic")
    assert "Deleted topic: test-topic" in result.output
    
    # Test without confirmation (should prompt and cancel)
    result = cli_runner.invoke(
        cli, ["--project", "test-project", "pubsub", "delete-topic", "test-topic"],
        input="n\n"
    )
    
    assert result.exit_code == 1  # Abort exit code
    
    # Test failure when project ID is missing
    result = cli_runner.invoke(cli, ["pubsub", "delete-topic", "test-topic", "--yes"])
    assert result.exit_code == 2
    assert "Project ID must be specified" in result.output


def test_publish_message_command(cli_runner, mock_pubsub_service):
    """Test the 'publish' command."""
    mock_pubsub_service.publish_message.return_value = "message-id-123"
    
    result = cli_runner.invoke(
        cli, [
            "--project", "test-project", 
            "pubsub", "publish", 
            "test-topic",
            "Hello, world!",
            "--attribute", "type=greeting",
            "--attribute", "language=english"
        ]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.publish_message.assert_called_once_with(
        topic_name="test-topic",
        data="Hello, world!",
        attributes={"type": "greeting", "language": "english"}
    )
    assert "Published message with ID: message-id-123" in result.output
    
    # Test with malformed attribute
    result = cli_runner.invoke(
        cli, [
            "--project", "test-project", 
            "pubsub", "publish", 
            "test-topic",
            "Hello, world!",
            "--attribute", "malformed-attribute"
        ]
    )
    
    assert result.exit_code == 0
    assert "Warning: Ignoring malformed attribute 'malformed-attribute'" in result.output
    
    # Test failure when project ID is missing
    result = cli_runner.invoke(cli, ["pubsub", "publish", "test-topic", "Hello, world!"])
    assert result.exit_code == 2
    assert "Project ID must be specified" in result.output


def test_list_subscriptions_command(cli_runner, mock_pubsub_service, sample_subscription):
    """Test the 'list-subscriptions' command."""
    mock_pubsub_service.list_subscriptions.return_value = [sample_subscription, sample_subscription]
    
    # Test list all subscriptions
    result = cli_runner.invoke(
        cli, ["--project", "test-project", "pubsub", "list-subscriptions", "--output", "json"]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.list_subscriptions.assert_called_once_with(None)
    
    # Check for expected output in JSON format
    output = json.loads(result.output)
    assert len(output) == 2
    assert output[0]["name"] == "test-subscription"
    assert output[0]["topic"] == "test-topic"
    
    # Test list subscriptions for a specific topic
    mock_pubsub_service.list_subscriptions.reset_mock()
    result = cli_runner.invoke(
        cli, ["--project", "test-project", "pubsub", "list-subscriptions", "--topic", "test-topic", "--output", "json"]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.list_subscriptions.assert_called_once_with("test-topic")
    
    # Test failure when project ID is missing
    result = cli_runner.invoke(cli, ["pubsub", "list-subscriptions"])
    assert result.exit_code == 2
    assert "Project ID must be specified" in result.output


def test_get_subscription_command(cli_runner, mock_pubsub_service, sample_subscription):
    """Test the 'get-subscription' command."""
    mock_pubsub_service.get_subscription.return_value = sample_subscription
    
    result = cli_runner.invoke(
        cli, ["--project", "test-project", "pubsub", "get-subscription", "test-subscription", "--output", "json"]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.get_subscription.assert_called_once_with("test-subscription")
    
    # Check for expected output in JSON format
    output = json.loads(result.output)
    assert output["name"] == "test-subscription"
    assert output["topic"] == "test-topic"
    assert output["project"] == "test-project"
    
    # Test failure when project ID is missing
    result = cli_runner.invoke(cli, ["pubsub", "get-subscription", "test-subscription"])
    assert result.exit_code == 2
    assert "Project ID must be specified" in result.output


def test_create_subscription_command(cli_runner, mock_pubsub_service, sample_subscription):
    """Test the 'create-subscription' command."""
    mock_pubsub_service.create_subscription.return_value = sample_subscription
    
    result = cli_runner.invoke(
        cli, [
            "--project", "test-project", 
            "pubsub", "create-subscription", 
            "test-subscription",
            "test-topic",
            "--ack-deadline", "10",
            "--push-endpoint", "https://example.com/push",
            "--retain-acked",
            "--message-retention", "P7D",
            "--label", "env=test",
            "--filter", "attributes.event_type = \"test\"",
            "--enable-ordering",
            "--output", "json"
        ]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.create_subscription.assert_called_once_with(
        subscription_name="test-subscription",
        topic_name="test-topic",
        ack_deadline_seconds=10,
        push_config={"pushEndpoint": "https://example.com/push"},
        retain_acked_messages=True,
        message_retention_duration="P7D",
        labels={"env": "test"},
        filter_expr="attributes.event_type = \"test\"",
        enable_message_ordering=True
    )
    
    # Check for expected output in JSON format
    output = json.loads(result.output)
    assert output["name"] == "test-subscription"
    assert output["topic"] == "test-topic"
    
    # Test with malformed label
    result = cli_runner.invoke(
        cli, [
            "--project", "test-project", 
            "pubsub", "create-subscription", 
            "test-subscription",
            "test-topic",
            "--label", "malformed-label"
        ]
    )
    
    assert result.exit_code == 0
    assert "Warning: Ignoring malformed label 'malformed-label'" in result.output
    
    # Test failure when project ID is missing
    result = cli_runner.invoke(cli, ["pubsub", "create-subscription", "test-subscription", "test-topic"])
    assert result.exit_code == 2
    assert "Project ID must be specified" in result.output


def test_delete_subscription_command(cli_runner, mock_pubsub_service):
    """Test the 'delete-subscription' command."""
    mock_pubsub_service.delete_subscription.return_value = True
    
    # Test with confirmation bypass
    result = cli_runner.invoke(
        cli, ["--project", "test-project", "pubsub", "delete-subscription", "test-subscription", "--yes"]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.delete_subscription.assert_called_once_with("test-subscription")
    assert "Deleted subscription: test-subscription" in result.output
    
    # Test without confirmation (should prompt and cancel)
    result = cli_runner.invoke(
        cli, ["--project", "test-project", "pubsub", "delete-subscription", "test-subscription"],
        input="n\n"
    )
    
    assert result.exit_code == 1  # Abort exit code
    
    # Test failure when project ID is missing
    result = cli_runner.invoke(cli, ["pubsub", "delete-subscription", "test-subscription", "--yes"])
    assert result.exit_code == 2
    assert "Project ID must be specified" in result.output


def test_pull_messages_command(cli_runner, mock_pubsub_service):
    """Test the 'pull' command."""
    # Mock messages with base64 encoded data
    mock_pubsub_service.pull_messages.return_value = [
        {
            "ackId": "ack-123",
            "message": {
                "messageId": "message-123",
                "data": "SGVsbG8sIHdvcmxkIQ==",  # base64 encoded "Hello, world!"
                "attributes": {"type": "greeting"}
            }
        }
    ]
    
    # Test pulling messages without auto-ack
    result = cli_runner.invoke(
        cli, [
            "--project", "test-project", 
            "pubsub", "pull", 
            "test-subscription",
            "--max-messages", "5"
        ]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.pull_messages.assert_called_once_with("test-subscription", 5)
    assert "Pulled 1 messages:" in result.output
    assert "Hello, world!" in result.output
    assert "type: greeting" in result.output
    assert mock_pubsub_service.acknowledge_messages.call_count == 0  # No ack
    
    # Test with auto-ack
    mock_pubsub_service.pull_messages.reset_mock()
    mock_pubsub_service.acknowledge_messages.reset_mock()
    result = cli_runner.invoke(
        cli, [
            "--project", "test-project", 
            "pubsub", "pull", 
            "test-subscription",
            "--auto-ack"
        ]
    )
    
    assert result.exit_code == 0
    mock_pubsub_service.acknowledge_messages.assert_called_once_with("test-subscription", ["ack-123"])
    assert "Acknowledged 1 messages." in result.output
    
    # Test with no messages
    mock_pubsub_service.pull_messages.reset_mock()
    mock_pubsub_service.pull_messages.return_value = []
    result = cli_runner.invoke(
        cli, ["--project", "test-project", "pubsub", "pull", "test-subscription"]
    )
    
    assert result.exit_code == 0
    assert "No messages available." in result.output
    
    # Test failure when project ID is missing
    result = cli_runner.invoke(cli, ["pubsub", "pull", "test-subscription"])
    assert result.exit_code == 2
    assert "Project ID must be specified" in result.output
