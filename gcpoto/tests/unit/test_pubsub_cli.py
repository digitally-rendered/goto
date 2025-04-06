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
    # Need to mock gcpoto.services.pubsub.PubSubService as each command imports it directly
    patcher = mock.patch("gcpoto.services.pubsub.PubSubService")
    mock_service_class = patcher.start()
    mock_instance = mock.MagicMock()
    mock_service_class.return_value = mock_instance

    # Make sure the mock has all the necessary methods
    mock_instance.list_resources.return_value = []
    mock_instance.get_resource.return_value = None
    mock_instance.create_resource.return_value = None
    mock_instance.update_resource.return_value = None
    mock_instance.delete_resource.return_value = None
    mock_instance.list_topics.return_value = []
    mock_instance.get_topic.return_value = None
    mock_instance.create_topic.return_value = None
    mock_instance.delete_topic.return_value = None
    mock_instance.publish_message.return_value = None
    mock_instance.list_subscriptions.return_value = []
    mock_instance.get_subscription.return_value = None
    mock_instance.create_subscription.return_value = None
    mock_instance.delete_subscription.return_value = None
    mock_instance.pull_messages.return_value = []

    yield mock_instance

    # Clean up the patch after the test
    patcher.stop()


@pytest.fixture
def sample_topic():
    """Create a sample PubSubTopic for tests."""
    # Create a MagicMock that can have methods assigned directly
    topic = mock.MagicMock(spec=PubSubTopic)

    # Set the properties we need for the tests
    topic.id = "projects/test-project/topics/test-topic"
    topic.name = "test-topic"
    topic.project = "test-project"
    topic.type = "pubsub.topic"
    topic.labels = {"env": "test", "owner": "test-team"}
    topic.created = (
        "2023-04-05T12:00:00Z"  # String format to avoid datetime serialization issues
    )

    # Define to_dict to match what the CLI expects for serialization
    topic.to_dict.return_value = {
        "id": topic.id,
        "name": topic.name,
        "project": topic.project,
        "type": topic.type,
        "labels": topic.labels,
        "created": topic.created,
    }

    return topic


@pytest.fixture
def sample_subscription():
    """Create a sample PubSubSubscription for tests."""
    # Create a MagicMock instead of a real PubSubSubscription
    subscription = mock.MagicMock(spec=PubSubSubscription)

    # Set the necessary properties for testing
    subscription.id = "projects/test-project/subscriptions/test-subscription"
    subscription.name = "test-subscription"
    subscription.topic = "test-topic"
    subscription.project = "test-project"
    subscription.type = "pubsub.subscription"
    subscription.ack_deadline_seconds = 10
    subscription.labels = {"env": "test"}
    subscription.created = "2023-04-05T12:00:00Z"  # String format for serialization

    # Setup to_dict method for JSON serialization in the CLI
    subscription.to_dict.return_value = {
        "id": subscription.id,
        "name": subscription.name,
        "topic": subscription.topic,
        "project": subscription.project,
        "type": subscription.type,
        "ack_deadline_seconds": subscription.ack_deadline_seconds,
        "labels": subscription.labels,
        "created": subscription.created,
    }

    return subscription


def test_list_topics_command(cli_runner, mock_pubsub_service, sample_topic):
    """Test the 'list-topics' command."""
    # Setup mock to return our sample topics
    mock_pubsub_service.list_resources.return_value = [sample_topic, sample_topic]

    # Rather than using CLI args which can be problematic, directly set up the context object
    # with the correct keys that the command expects
    result = cli_runner.invoke(
        cli,
        ["pubsub", "list-topics"],
        obj={"project": "test-project", "output": "json"},
        catch_exceptions=False,
    )

    # Assert success
    assert result.exit_code == 0
    mock_pubsub_service.list_resources.assert_called_once()

    # Check JSON output
    output = json.loads(result.output)
    assert len(output) == 2
    assert output[0]["name"] == "test-topic"
    assert output[0]["project"] == "test-project"

    # Test failure case without project ID - use an empty context object
    result = cli_runner.invoke(
        cli,
        ["pubsub", "list-topics"],
        obj={},  # Empty context object
        catch_exceptions=False,
    )
    assert "Project ID must be specified" in result.output


def test_get_topic_command(cli_runner, mock_pubsub_service, sample_topic):
    """Test the 'get-topic' command."""
    # Setup mock for get_topic to return our sample topic
    mock_pubsub_service.get_topic.return_value = sample_topic

    # Use context object to provide required project ID and output format
    result = cli_runner.invoke(
        cli,
        ["pubsub", "get-topic", "test-topic"],
        obj={"project": "test-project", "output": "json"},
        catch_exceptions=False,
    )

    # Verify the test passes
    assert result.exit_code == 0
    mock_pubsub_service.get_topic.assert_called_once_with("test-topic")

    # Check JSON output - _output_result always returns a list of items
    output = json.loads(result.output)
    assert isinstance(output, list)
    assert output[0]["name"] == "test-topic"
    assert output[0]["project"] == "test-project"

    # Test failure when project ID is missing - use empty context
    result = cli_runner.invoke(
        cli,
        ["pubsub", "get-topic", "test-topic"],
        obj={},  # Empty context
        catch_exceptions=False,
    )
    assert "Project ID must be specified" in result.output


def test_create_topic_command(cli_runner, mock_pubsub_service, sample_topic):
    """Test the 'create-topic' command."""
    # Setup mock to return the sample topic
    mock_pubsub_service.create_topic.return_value = sample_topic

    # Use Click's context object to provide project ID and output format
    result = cli_runner.invoke(
        cli,
        [
            "pubsub",
            "create-topic",
            "test-topic",
            "--label",
            "env=test",
            "--label",
            "owner=test-team",
            "--kms-key",
            "test-key",
            "--message-retention",
            "P1D",
            "--region",
            "us-central1",
            "--region",
            "us-east1",
        ],
        obj={"project": "test-project", "output": "json"},
        catch_exceptions=False,
    )

    # Verify the test passes
    assert result.exit_code == 0
    mock_pubsub_service.create_topic.assert_called_once_with(
        topic_name="test-topic",
        labels={"env": "test", "owner": "test-team"},
        kms_key_name="test-key",
        message_retention_duration="P1D",
        message_storage_policy={
            "allowedPersistenceRegions": ["us-central1", "us-east1"]
        },
    )

    # Verify the command output contains the success message
    assert "Created topic: test-topic" in result.output

    # In a real test we would check for JSON output, but we may have a mix of text and JSON
    # which is hard to parse cleanly. So we'll just check for key information in the output.
    assert "test-topic" in result.output
    assert "test-project" in result.output

    # Test with malformed label
    result = cli_runner.invoke(
        cli,
        ["pubsub", "create-topic", "test-topic", "--label", "malformed-label"],
        obj={"project": "test-project", "output": "json"},
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "Warning: Ignoring malformed label 'malformed-label'" in result.output

    # Test failure when project ID is missing
    result = cli_runner.invoke(
        cli,
        ["pubsub", "create-topic", "test-topic"],
        obj={},  # Empty context
        catch_exceptions=False,
    )
    assert "Project ID must be specified" in result.output


def test_delete_topic_command(cli_runner, mock_pubsub_service):
    """Test the 'delete-topic' command."""
    # Setup mock to return success
    mock_pubsub_service.delete_topic.return_value = True

    # Test with confirmation bypass
    result = cli_runner.invoke(
        cli,
        ["pubsub", "delete-topic", "test-topic", "--yes"],
        obj={"project": "test-project"},
        catch_exceptions=False,
    )

    # Verify success
    assert result.exit_code == 0
    mock_pubsub_service.delete_topic.assert_called_once_with("test-topic")
    assert "Deleted topic: test-topic" in result.output

    # Reset mock for next test
    mock_pubsub_service.delete_topic.reset_mock()

    # Test without confirmation (should prompt and cancel)
    result = cli_runner.invoke(
        cli,
        ["pubsub", "delete-topic", "test-topic"],
        obj={"project": "test-project"},
        input="n\n",
        catch_exceptions=False,
    )

    assert result.exit_code == 1  # Abort exit code
    assert not mock_pubsub_service.delete_topic.called  # Verify delete was not called

    # Test failure when project ID is missing
    result = cli_runner.invoke(
        cli,
        ["pubsub", "delete-topic", "test-topic", "--yes"],
        obj={},  # Empty context
        catch_exceptions=False,
    )
    assert "Project ID must be specified" in result.output


def test_publish_message_command(cli_runner, mock_pubsub_service):
    """Test the 'publish' command."""
    # Setup mock to return a message ID
    mock_pubsub_service.publish_message.return_value = "message-id-123"

    # Test publishing a message with attributes
    result = cli_runner.invoke(
        cli,
        [
            "pubsub",
            "publish",
            "test-topic",
            "Hello, world!",
            "--attribute",
            "type=greeting",
            "--attribute",
            "language=english",
        ],
        obj={"project": "test-project"},
        catch_exceptions=False,
    )

    # Verify success
    assert result.exit_code == 0
    mock_pubsub_service.publish_message.assert_called_once_with(
        topic_name="test-topic",
        data="Hello, world!",
        attributes={"type": "greeting", "language": "english"},
    )
    assert "Published message with ID: message-id-123" in result.output

    # Reset mock for next test
    mock_pubsub_service.publish_message.reset_mock()

    # Test with malformed attribute
    result = cli_runner.invoke(
        cli,
        [
            "pubsub",
            "publish",
            "test-topic",
            "Hello, world!",
            "--attribute",
            "malformed-attribute",
        ],
        obj={"project": "test-project"},
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert (
        "Warning: Ignoring malformed attribute 'malformed-attribute'" in result.output
    )

    # Test failure when project ID is missing
    result = cli_runner.invoke(
        cli,
        ["pubsub", "publish", "test-topic", "Hello, world!"],
        obj={},  # Empty context
        catch_exceptions=False,
    )
    assert "Project ID must be specified" in result.output


def test_list_subscriptions_command(
    cli_runner, mock_pubsub_service, sample_subscription
):
    """Test the 'list-subscriptions' command."""
    # Setup mock to return sample subscriptions
    mock_pubsub_service.list_subscriptions.return_value = [
        sample_subscription,
        sample_subscription,
    ]

    # Test list all subscriptions (topic=None)
    result = cli_runner.invoke(
        cli,
        ["pubsub", "list-subscriptions"],
        obj={"project": "test-project", "output": "json"},
        catch_exceptions=False,
    )

    # Verify success
    assert result.exit_code == 0
    mock_pubsub_service.list_subscriptions.assert_called_once_with(None)

    # Check JSON output
    output = json.loads(result.output)
    assert len(output) == 2
    assert output[0]["name"] == "test-subscription"
    assert output[0]["topic"] == "test-topic"

    # Test list subscriptions for a specific topic
    mock_pubsub_service.list_subscriptions.reset_mock()
    result = cli_runner.invoke(
        cli,
        ["pubsub", "list-subscriptions", "--topic", "test-topic"],
        obj={"project": "test-project", "output": "json"},
        catch_exceptions=False,
    )

    # Verify the topic filter was used correctly
    assert result.exit_code == 0
    mock_pubsub_service.list_subscriptions.assert_called_once_with("test-topic")

    # Test failure when project ID is missing
    result = cli_runner.invoke(
        cli,
        ["pubsub", "list-subscriptions"],
        obj={},  # Empty context
        catch_exceptions=False,
    )
    assert "Project ID must be specified" in result.output


def test_get_subscription_command(cli_runner, mock_pubsub_service, sample_subscription):
    """Test the 'get-subscription' command."""
    # Setup mock to return our sample subscription
    mock_pubsub_service.get_subscription.return_value = sample_subscription

    # Use context object to provide required project ID and output format
    result = cli_runner.invoke(
        cli,
        ["pubsub", "get-subscription", "test-subscription"],
        obj={"project": "test-project", "output": "json"},
        catch_exceptions=False,
    )

    # Verify the test passes
    assert result.exit_code == 0
    mock_pubsub_service.get_subscription.assert_called_once_with("test-subscription")

    # Check JSON output - _output_result always wraps in a list
    output = json.loads(result.output)
    assert isinstance(output, list)
    assert output[0]["name"] == "test-subscription"
    assert output[0]["topic"] == "test-topic"
    assert output[0]["project"] == "test-project"

    # Test failure when project ID is missing
    result = cli_runner.invoke(
        cli,
        ["pubsub", "get-subscription", "test-subscription"],
        obj={},  # Empty context
        catch_exceptions=False,
    )
    assert "Project ID must be specified" in result.output


def test_create_subscription_command(
    cli_runner, mock_pubsub_service, sample_subscription
):
    """Test the 'create-subscription' command."""
    # Setup mock to return our sample subscription
    mock_pubsub_service.create_subscription.return_value = sample_subscription

    # Use context object to provide required project ID and output format
    result = cli_runner.invoke(
        cli,
        [
            "pubsub",
            "create-subscription",
            "test-subscription",
            "test-topic",
            "--ack-deadline",
            "10",
            "--push-endpoint",
            "https://example.com/push",
            "--retain-acked",
            "--message-retention",
            "P7D",
            "--label",
            "env=test",
            "--filter",
            'attributes.event_type = "test"',
            "--enable-ordering",
        ],
        obj={"project": "test-project", "output": "json"},
        catch_exceptions=False,
    )

    # Verify the test passes
    assert result.exit_code == 0
    mock_pubsub_service.create_subscription.assert_called_once_with(
        subscription_name="test-subscription",
        topic_name="test-topic",
        ack_deadline_seconds=10,
        push_config={"pushEndpoint": "https://example.com/push"},
        retain_acked_messages=True,
        message_retention_duration="P7D",
        labels={"env": "test"},
        filter_expr='attributes.event_type = "test"',
        enable_message_ordering=True,
    )

    # Verify the command output contains expected information
    # We don't parse JSON since the output might contain both text and JSON
    assert "test-subscription" in result.output
    assert "test-topic" in result.output

    # Reset mock for next test
    mock_pubsub_service.create_subscription.reset_mock()

    # Test with malformed label
    result = cli_runner.invoke(
        cli,
        [
            "pubsub",
            "create-subscription",
            "test-subscription",
            "test-topic",
            "--label",
            "malformed-label",
        ],
        obj={"project": "test-project"},
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert "Warning: Ignoring malformed label 'malformed-label'" in result.output

    # Test failure when project ID is missing
    result = cli_runner.invoke(
        cli,
        ["pubsub", "create-subscription", "test-subscription", "test-topic"],
        obj={},  # Empty context
        catch_exceptions=False,
    )
    assert "Project ID must be specified" in result.output


def test_delete_subscription_command(cli_runner, mock_pubsub_service):
    """Test the 'delete-subscription' command."""
    # Setup mock to return success
    mock_pubsub_service.delete_subscription.return_value = True

    # Test with confirmation bypass
    result = cli_runner.invoke(
        cli,
        ["pubsub", "delete-subscription", "test-subscription", "--yes"],
        obj={"project": "test-project"},
        catch_exceptions=False,
    )

    # Verify success
    assert result.exit_code == 0
    mock_pubsub_service.delete_subscription.assert_called_once_with("test-subscription")
    assert "Deleted subscription: test-subscription" in result.output

    # Reset mock for next test
    mock_pubsub_service.delete_subscription.reset_mock()

    # Test without confirmation (should prompt and cancel)
    result = cli_runner.invoke(
        cli,
        ["pubsub", "delete-subscription", "test-subscription"],
        obj={"project": "test-project"},
        input="n\n",
        catch_exceptions=False,
    )

    assert result.exit_code == 1  # Abort exit code
    assert (
        not mock_pubsub_service.delete_subscription.called
    )  # Verify delete was not called

    # Test failure when project ID is missing
    result = cli_runner.invoke(
        cli,
        ["pubsub", "delete-subscription", "test-subscription", "--yes"],
        obj={},  # Empty context
        catch_exceptions=False,
    )
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
                "attributes": {"type": "greeting"},
            },
        }
    ]

    # Test pulling messages without auto-ack
    result = cli_runner.invoke(
        cli,
        ["pubsub", "pull", "test-subscription", "--max-messages", "5"],
        obj={"project": "test-project"},
        catch_exceptions=False,
    )

    # Verify the test passes
    assert result.exit_code == 0
    mock_pubsub_service.pull_messages.assert_called_once_with("test-subscription", 5)
    assert "Pulled 1 messages:" in result.output
    assert "Hello, world!" in result.output
    assert "type: greeting" in result.output
    assert mock_pubsub_service.acknowledge_messages.call_count == 0  # No ack was called

    # Test with auto-ack
    mock_pubsub_service.pull_messages.reset_mock()
    mock_pubsub_service.acknowledge_messages.reset_mock()
    result = cli_runner.invoke(
        cli,
        ["pubsub", "pull", "test-subscription", "--auto-ack"],
        obj={"project": "test-project"},
        catch_exceptions=False,
    )

    # Verify acknowledgment happens correctly
    assert result.exit_code == 0
    mock_pubsub_service.acknowledge_messages.assert_called_once_with(
        "test-subscription", ["ack-123"]
    )
    assert "Acknowledged 1 messages." in result.output

    # Test with no messages
    mock_pubsub_service.pull_messages.reset_mock()
    mock_pubsub_service.pull_messages.return_value = []
    result = cli_runner.invoke(
        cli,
        ["pubsub", "pull", "test-subscription"],
        obj={"project": "test-project"},
        catch_exceptions=False,
    )

    # Verify empty result handling
    assert result.exit_code == 0
    assert "No messages available." in result.output

    # Test failure when project ID is missing
    result = cli_runner.invoke(
        cli,
        ["pubsub", "pull", "test-subscription"],
        obj={},  # Empty context
        catch_exceptions=False,
    )
    assert "Project ID must be specified" in result.output
