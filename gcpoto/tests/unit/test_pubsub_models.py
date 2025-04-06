"""Tests for Pub/Sub models."""

import json
from unittest import mock
from datetime import datetime

import pytest

from gcpoto.models.pubsub import PubSubTopic, PubSubSubscription, MessageStoragePolicy, SchemaSettings
from gcpoto.schemas.pubsub import get_schema


@pytest.fixture
def sample_topic_response():
    """Return a sample Pub/Sub topic response."""
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
        "satisfiesPzs": False,
        "created": "2023-04-05T12:00:00Z",
        "updated": "2023-04-05T13:00:00Z"
    }


@pytest.fixture
def sample_subscription_response():
    """Return a sample Pub/Sub subscription response."""
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
        "enableMessageOrdering": True,
        "created": "2023-04-05T12:00:00Z",
        "updated": "2023-04-05T13:00:00Z"
    }


def test_pubsub_topic_schema():
    """Test that the Pub/Sub Topic schema is valid."""
    schema = get_schema("topic")
    assert schema["title"] == "GCP Pub/Sub Topic"
    assert schema["type"] == "object"
    assert "name" in schema["required"]
    assert "project" in schema["required"]
    assert "name" in schema["properties"]
    assert "labels" in schema["properties"]
    assert "schemaSettings" in schema["properties"]


def test_pubsub_subscription_schema():
    """Test that the Pub/Sub Subscription schema is valid."""
    schema = get_schema("subscription")
    assert schema["title"] == "GCP Pub/Sub Subscription"
    assert schema["type"] == "object"
    assert "name" in schema["required"]
    assert "topic" in schema["required"]
    assert "project" in schema["required"]
    assert "name" in schema["properties"]
    assert "pushConfig" in schema["properties"]
    assert "deadLetterPolicy" in schema["properties"]


def test_message_storage_policy_model():
    """Test creating a MessageStoragePolicy model."""
    regions = ["us-central1", "us-east1"]
    policy = MessageStoragePolicy(allowed_persistence_regions=regions)
    
    assert policy.allowed_persistence_regions == regions
    
    # Test with empty list
    empty_policy = MessageStoragePolicy()
    assert empty_policy.allowed_persistence_regions == []


def test_schema_settings_model():
    """Test creating a SchemaSettings model."""
    schema = "projects/test-project/schemas/test-schema"
    encoding = "JSON"
    settings = SchemaSettings(schema=schema, encoding=encoding)
    
    assert settings.schema == schema
    assert settings.encoding == encoding


def test_pubsub_topic_model_creation():
    """Test creating a PubSubTopic model."""
    # Test minimal required fields
    topic = PubSubTopic(
        id="projects/test-project/topics/test-topic",
        name="test-topic",
        type="pubsub.topic",
        project="test-project"
    )
    assert topic.name == "test-topic"
    assert topic.project == "test-project"
    assert topic.type == "pubsub.topic"
    
    # Test with all fields
    storage_policy = MessageStoragePolicy(allowed_persistence_regions=["us-central1", "us-east1"])
    schema_settings = SchemaSettings(schema="test-schema", encoding="JSON")
    
    topic = PubSubTopic(
        id="projects/test-project/topics/test-topic",
        name="test-topic",
        type="pubsub.topic",
        project="test-project",
        labels={"env": "test"},
        kms_key_name="test-key",
        message_storage_policy=storage_policy,
        schema_settings=schema_settings,
        message_retention_duration="86400s",
        satisfies_pzs=False,
        created="2023-04-05T12:00:00Z",
        updated="2023-04-05T13:00:00Z"
    )
    
    assert topic.name == "test-topic"
    assert topic.project == "test-project"
    assert topic.kms_key_name == "test-key"
    assert topic.message_storage_policy.allowed_persistence_regions == ["us-central1", "us-east1"]
    assert topic.schema_settings.schema == "test-schema"
    assert topic.schema_settings.encoding == "JSON"
    assert topic.message_retention_duration == "86400s"
    assert topic.satisfies_pzs is False
    
    # Test JSON serialization
    json_data = json.loads(topic.model_dump_json())
    assert json_data["name"] == "test-topic"
    assert json_data["project"] == "test-project"
    assert json_data["kms_key_name"] == "test-key"
    assert json_data["message_storage_policy"]["allowed_persistence_regions"] == ["us-central1", "us-east1"]


def test_pubsub_topic_from_api_response(sample_topic_response):
    """Test creating a PubSubTopic from an API response."""
    topic = PubSubTopic.from_api_response(sample_topic_response)
    
    assert topic.name == "test-topic"
    assert topic.project == "test-project"
    assert topic.id == "projects/test-project/topics/test-topic"
    assert topic.kms_key_name == "projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key"
    assert topic.labels == {"env": "test", "owner": "test-team"}
    assert topic.message_storage_policy.allowed_persistence_regions == ["us-central1", "us-east1"]
    assert topic.schema_settings.schema == "projects/test-project/schemas/test-schema"
    assert topic.schema_settings.encoding == "JSON"
    assert topic.message_retention_duration == "86400s"
    assert topic.satisfies_pzs is False
    # Check datetime conversion
    assert topic.created.isoformat().replace('+00:00', 'Z') == "2023-04-05T12:00:00Z"
    assert topic.updated.isoformat().replace('+00:00', 'Z') == "2023-04-05T13:00:00Z"


def test_pubsub_subscription_model_creation():
    """Test creating a PubSubSubscription model."""
    # Test minimal required fields
    sub = PubSubSubscription(
        id="projects/test-project/subscriptions/test-sub",
        name="test-sub",
        topic="test-topic",
        type="pubsub.subscription",
        project="test-project"
    )
    assert sub.name == "test-sub"
    assert sub.topic == "test-topic"
    assert sub.project == "test-project"
    assert sub.type == "pubsub.subscription"
    
    # Test with all fields
    from gcpoto.models.pubsub import PushConfig, DeadLetterPolicy, RetryPolicy, ExpirationPolicy
    
    push_config = PushConfig(
        push_endpoint="https://example.com/push",
        attributes={"x-goog-version": "v1"}
    )
    dead_letter_policy = DeadLetterPolicy(
        dead_letter_topic="dead-letter",
        max_delivery_attempts=5
    )
    retry_policy = RetryPolicy(
        minimum_backoff="10s",
        maximum_backoff="600s"
    )
    expiration_policy = ExpirationPolicy(ttl="2592000s")
    
    sub = PubSubSubscription(
        id="projects/test-project/subscriptions/test-sub",
        name="test-sub",
        topic="test-topic",
        type="pubsub.subscription",
        project="test-project",
        labels={"env": "test"},
        push_config=push_config,
        ack_deadline_seconds=10,
        retain_acked_messages=True,
        message_retention_duration="604800s",
        expiration_policy=expiration_policy,
        filter="attributes.event_type = \"test\"",
        dead_letter_policy=dead_letter_policy,
        retry_policy=retry_policy,
        detached=False,
        enable_message_ordering=True,
        created="2023-04-05T12:00:00Z",
        updated="2023-04-05T13:00:00Z"
    )
    
    assert sub.name == "test-sub"
    assert sub.topic == "test-topic"
    assert sub.push_config.push_endpoint == "https://example.com/push"
    assert sub.ack_deadline_seconds == 10
    assert sub.retain_acked_messages is True
    assert sub.message_retention_duration == "604800s"
    assert sub.expiration_policy.ttl == "2592000s"
    assert sub.filter == "attributes.event_type = \"test\""
    assert sub.dead_letter_policy.dead_letter_topic == "dead-letter"
    assert sub.dead_letter_policy.max_delivery_attempts == 5
    assert sub.retry_policy.minimum_backoff == "10s"
    assert sub.retry_policy.maximum_backoff == "600s"
    assert sub.detached is False
    assert sub.enable_message_ordering is True
    
    # Test JSON serialization
    json_data = json.loads(sub.model_dump_json())
    assert json_data["name"] == "test-sub"
    assert json_data["topic"] == "test-topic"
    assert json_data["push_config"]["push_endpoint"] == "https://example.com/push"


def test_pubsub_subscription_from_api_response(sample_subscription_response):
    """Test creating a PubSubSubscription from an API response."""
    sub = PubSubSubscription.from_api_response(sample_subscription_response)
    
    assert sub.name == "test-subscription"
    assert sub.topic == "test-topic"
    assert sub.project == "test-project"
    assert sub.id == "projects/test-project/subscriptions/test-subscription"
    assert sub.labels == {"env": "test", "purpose": "testing"}
    assert sub.push_config.push_endpoint == "https://example.com/push"
    assert sub.push_config.attributes == {"x-goog-version": "v1"}
    assert sub.ack_deadline_seconds == 10
    assert sub.retain_acked_messages is True
    assert sub.message_retention_duration == "604800s"
    assert sub.expiration_policy.ttl == "2592000s"
    assert sub.filter == "attributes.event_type = \"test\""
    assert sub.dead_letter_policy.dead_letter_topic == "dead-letter"
    assert sub.dead_letter_policy.max_delivery_attempts == 5
    assert sub.retry_policy.minimum_backoff == "10s"
    assert sub.retry_policy.maximum_backoff == "600s"
    assert sub.detached is False
    assert sub.enable_message_ordering is True
    # Check datetime conversion
    assert sub.created.isoformat().replace('+00:00', 'Z') == "2023-04-05T12:00:00Z"
    assert sub.updated.isoformat().replace('+00:00', 'Z') == "2023-04-05T13:00:00Z"
