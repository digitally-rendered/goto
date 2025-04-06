"""Integration tests for the Pub/Sub service."""

import os
import json
import time
import uuid
import base64
import pytest
from typing import Dict, Any, List, Tuple

from gcpoto.services.pubsub import PubSubService, PubSubTopic, PubSubSubscription


pytest.mark.integration = pytest.mark.skipif(
    "GCPOTO_RUN_INTEGRATION_TESTS" not in os.environ,
    reason="Integration tests are skipped unless GCPOTO_RUN_INTEGRATION_TESTS is set",
)


@pytest.fixture(scope="module")
def test_topic_name(test_resource_prefix: str) -> str:
    """Generate a unique topic name for testing.
    
    Args:
        test_resource_prefix: Prefix for test resources.
        
    Returns:
        str: A unique topic name.
    """
    return f"{test_resource_prefix}-topic-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def test_subscription_name(test_resource_prefix: str) -> str:
    """Generate a unique subscription name for testing.
    
    Args:
        test_resource_prefix: Prefix for test resources.
        
    Returns:
        str: A unique subscription name.
    """
    return f"{test_resource_prefix}-sub-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def test_deadletter_topic_name(test_resource_prefix: str) -> str:
    """Generate a unique dead letter topic name for testing.
    
    Args:
        test_resource_prefix: Prefix for test resources.
        
    Returns:
        str: A unique topic name for dead letter.
    """
    return f"{test_resource_prefix}-dl-topic-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def test_deadletter_subscription_name(test_resource_prefix: str) -> str:
    """Generate a unique dead letter subscription name for testing.
    
    Args:
        test_resource_prefix: Prefix for test resources.
        
    Returns:
        str: A unique subscription name for dead letter.
    """
    return f"{test_resource_prefix}-dl-sub-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def test_topic(pubsub_service: PubSubService, test_topic_name: str, 
              common_tags: Dict[str, str], request) -> PubSubTopic:
    """Create a test topic and clean it up after tests.
    
    Args:
        pubsub_service: The Pub/Sub service to use.
        test_topic_name: Name for the test topic.
        common_tags: Tags to apply to the topic.
        request: The pytest request fixture.
        
    Returns:
        PubSubTopic: The created topic.
    """
    # Create a new topic for testing
    topic = pubsub_service.create_topic(
        topic_name=test_topic_name,
        labels={"purpose": "integration-testing"},
        tags=common_tags
    )
    
    # Register finalizer to clean up the topic after tests
    def cleanup():
        try:
            # Delete the topic
            pubsub_service.delete_topic(test_topic_name)
            print(f"Cleaned up test topic: {test_topic_name}")
        except Exception as e:
            print(f"Error cleaning up test topic: {e}")
    
    request.addfinalizer(cleanup)
    
    return topic


@pytest.fixture(scope="module")
def test_deadletter_topic(pubsub_service: PubSubService, test_deadletter_topic_name: str, 
                        common_tags: Dict[str, str], request) -> PubSubTopic:
    """Create a test dead letter topic and clean it up after tests.
    
    Args:
        pubsub_service: The Pub/Sub service to use.
        test_deadletter_topic_name: Name for the test topic.
        common_tags: Tags to apply to the topic.
        request: The pytest request fixture.
        
    Returns:
        PubSubTopic: The created topic.
    """
    # Create a new topic for testing
    topic = pubsub_service.create_topic(
        topic_name=test_deadletter_topic_name,
        labels={"purpose": "integration-testing-deadletter"},
        tags=common_tags
    )
    
    # Register finalizer to clean up the topic after tests
    def cleanup():
        try:
            # Delete the topic
            pubsub_service.delete_topic(test_deadletter_topic_name)
            print(f"Cleaned up test dead letter topic: {test_deadletter_topic_name}")
        except Exception as e:
            print(f"Error cleaning up test dead letter topic: {e}")
    
    request.addfinalizer(cleanup)
    
    return topic


@pytest.fixture(scope="module")
def test_subscription(pubsub_service: PubSubService, 
                     test_topic: PubSubTopic,
                     test_subscription_name: str,
                     common_tags: Dict[str, str], 
                     request) -> PubSubSubscription:
    """Create a test subscription and clean it up after tests.
    
    Args:
        pubsub_service: The Pub/Sub service to use.
        test_topic: The topic to subscribe to.
        test_subscription_name: Name for the test subscription.
        common_tags: Tags to apply to the subscription.
        request: The pytest request fixture.
        
    Returns:
        PubSubSubscription: The created subscription.
    """
    # Create a new subscription for testing
    subscription = pubsub_service.create_subscription(
        subscription_name=test_subscription_name,
        topic_name=test_topic.name,
        ack_deadline_seconds=30,
        labels={"purpose": "integration-testing"},
        tags=common_tags
    )
    
    # Register finalizer to clean up the subscription after tests
    def cleanup():
        try:
            # Delete the subscription
            pubsub_service.delete_subscription(test_subscription_name)
            print(f"Cleaned up test subscription: {test_subscription_name}")
        except Exception as e:
            print(f"Error cleaning up test subscription: {e}")
    
    request.addfinalizer(cleanup)
    
    return subscription


@pytest.fixture(scope="module")
def test_deadletter_subscription(pubsub_service: PubSubService, 
                               test_deadletter_topic: PubSubTopic,
                               test_deadletter_subscription_name: str,
                               common_tags: Dict[str, str], 
                               request) -> PubSubSubscription:
    """Create a test dead letter subscription and clean it up after tests.
    
    Args:
        pubsub_service: The Pub/Sub service to use.
        test_deadletter_topic: The topic to subscribe to.
        test_deadletter_subscription_name: Name for the test subscription.
        common_tags: Tags to apply to the subscription.
        request: The pytest request fixture.
        
    Returns:
        PubSubSubscription: The created subscription.
    """
    # Create a new subscription for testing
    subscription = pubsub_service.create_subscription(
        subscription_name=test_deadletter_subscription_name,
        topic_name=test_deadletter_topic.name,
        ack_deadline_seconds=30,
        labels={"purpose": "integration-testing-deadletter"},
        tags=common_tags
    )
    
    # Register finalizer to clean up the subscription after tests
    def cleanup():
        try:
            # Delete the subscription
            pubsub_service.delete_subscription(test_deadletter_subscription_name)
            print(f"Cleaned up test dead letter subscription: {test_deadletter_subscription_name}")
        except Exception as e:
            print(f"Error cleaning up test dead letter subscription: {e}")
    
    request.addfinalizer(cleanup)
    
    return subscription


@pytest.mark.integration
class TestPubSubIntegration:
    """Integration tests for the Pub/Sub service."""
    
    def test_list_topics(self, pubsub_service: PubSubService):
        """Test listing topics in the project."""
        topics = pubsub_service.list_resources()
        # Just verify we can get a list without error
        assert isinstance(topics, list)
        # Print some info for debugging
        print(f"Found {len(topics)} topics in the project")
    
    def test_create_get_topic_with_tags(self, pubsub_service: PubSubService, 
                                      test_topic: PubSubTopic,
                                      test_topic_name: str,
                                      common_tags: Dict[str, str]):
        """Test creating a topic with tags and retrieving it."""
        # Verify the topic was created
        assert test_topic.name == test_topic_name
        
        # Verify tags were applied
        assert test_topic.tags is not None
        for key, value in common_tags.items():
            assert test_topic.tags.get(key) == value
        
        # Verify we can retrieve the topic
        retrieved_topic = pubsub_service.get_topic(test_topic_name)
        assert retrieved_topic.name == test_topic.name
        
        # Verify retrieved topic has the tags
        assert retrieved_topic.tags is not None
        for key, value in common_tags.items():
            assert retrieved_topic.tags.get(key) == value
    
    def test_create_get_subscription_with_tags(self, pubsub_service: PubSubService,
                                            test_subscription: PubSubSubscription,
                                            test_subscription_name: str,
                                            test_topic_name: str,
                                            common_tags: Dict[str, str]):
        """Test creating a subscription with tags and retrieving it."""
        # Verify the subscription was created
        assert test_subscription.name == test_subscription_name
        assert test_subscription.topic.endswith(test_topic_name)
        
        # Verify tags were applied
        assert test_subscription.tags is not None
        for key, value in common_tags.items():
            assert test_subscription.tags.get(key) == value
        
        # Verify we can retrieve the subscription
        retrieved_sub = pubsub_service.get_subscription(test_subscription_name)
        assert retrieved_sub.name == test_subscription.name
        
        # Verify retrieved subscription has the tags
        assert retrieved_sub.tags is not None
        for key, value in common_tags.items():
            assert retrieved_sub.tags.get(key) == value
    
    def test_publish_and_pull_messages(self, pubsub_service: PubSubService,
                                     test_topic_name: str,
                                     test_subscription_name: str):
        """Test publishing messages to a topic and pulling them from a subscription."""
        # Publish multiple messages
        msg_count = 5
        sent_messages = []
        sent_attributes = []
        
        for i in range(msg_count):
            msg_data = f"Test message {i} - {uuid.uuid4().hex}"
            attributes = {
                "message_id": str(i),
                "timestamp": str(time.time()),
                "test_run": "integration"
            }
            
            # Publish the message
            message_id = pubsub_service.publish_message(
                topic_name=test_topic_name,
                data=msg_data,
                attributes=attributes
            )
            
            assert message_id is not None
            sent_messages.append(msg_data)
            sent_attributes.append(attributes)
            print(f"Published message {i} with ID: {message_id}")
        
        # Allow some time for messages to be delivered
        time.sleep(5)
        
        # Pull messages from the subscription
        pulled_messages = pubsub_service.pull_messages(
            subscription_name=test_subscription_name,
            max_messages=msg_count
        )
        
        # We should have received at least one message
        assert len(pulled_messages) > 0
        print(f"Pulled {len(pulled_messages)} messages")
        
        # Process and verify received messages
        ack_ids = []
        for msg in pulled_messages:
            ack_id = msg.get("ackId")
            assert ack_id is not None
            ack_ids.append(ack_id)
            
            message_data = msg.get("message", {})
            data = message_data.get("data")
            attributes = message_data.get("attributes", {})
            
            # Decode the message data from base64
            decoded_data = base64.b64decode(data).decode("utf-8")
            print(f"Received message: {decoded_data}")
            
            # Verify the message was one we sent
            assert decoded_data in sent_messages
            
            # Verify attributes include test_run
            assert attributes.get("test_run") == "integration"
        
        # Acknowledge the messages
        if ack_ids:
            success = pubsub_service.acknowledge_messages(
                subscription_name=test_subscription_name,
                ack_ids=ack_ids
            )
            assert success
    
    def test_subscription_with_dead_letter(self, pubsub_service: PubSubService,
                                         test_topic: PubSubTopic,
                                         test_deadletter_topic: PubSubTopic,
                                         test_project_id: str,
                                         common_tags: Dict[str, str]):
        """Test creating a subscription with a dead letter policy."""
        # Create a unique name for this test
        dl_sub_name = f"dl-test-sub-{uuid.uuid4().hex[:8]}"
        
        try:
            # Create subscription with dead letter config
            dl_sub = pubsub_service.create_subscription(
                subscription_name=dl_sub_name,
                topic_name=test_topic.name,
                dead_letter_policy={
                    "deadLetterTopic": f"projects/{test_project_id}/topics/{test_deadletter_topic.name}",
                    "maxDeliveryAttempts": 5
                },
                labels={"purpose": "dead-letter-test"},
                tags={**common_tags, "test-type": "dead-letter"}
            )
            
            # Verify the subscription was created with the dead letter policy
            assert dl_sub.dead_letter_policy is not None
            assert dl_sub.dead_letter_policy.get("deadLetterTopic").endswith(test_deadletter_topic.name)
            assert dl_sub.dead_letter_policy.get("maxDeliveryAttempts") == 5
            
            # Verify tags
            assert dl_sub.tags.get("test-type") == "dead-letter"
            
            # Retrieve the subscription and check its properties
            retrieved_sub = pubsub_service.get_subscription(dl_sub_name)
            assert retrieved_sub.dead_letter_policy is not None
            assert retrieved_sub.dead_letter_policy.get("deadLetterTopic").endswith(test_deadletter_topic.name)
        
        finally:
            # Clean up
            try:
                pubsub_service.delete_subscription(dl_sub_name)
                print(f"Cleaned up dead letter test subscription: {dl_sub_name}")
            except Exception as e:
                print(f"Error cleaning up dead letter test subscription: {e}")
    
    def test_subscription_with_filter(self, pubsub_service: PubSubService,
                                    test_topic: PubSubTopic,
                                    common_tags: Dict[str, str]):
        """Test creating a subscription with a filter expression."""
        # Create a unique name for this test
        filter_sub_name = f"filter-test-sub-{uuid.uuid4().hex[:8]}"
        
        try:
            # Create subscription with filter
            filter_expr = "attributes.event_type = \"test-event\""
            filter_sub = pubsub_service.create_subscription(
                subscription_name=filter_sub_name,
                topic_name=test_topic.name,
                filter_expr=filter_expr,
                labels={"purpose": "filter-test"},
                tags={**common_tags, "test-type": "filter"}
            )
            
            # Verify the subscription was created with the filter
            assert filter_sub.filter == filter_expr
            
            # Verify tags
            assert filter_sub.tags.get("test-type") == "filter"
            
            # Retrieve the subscription and check its properties
            retrieved_sub = pubsub_service.get_subscription(filter_sub_name)
            assert retrieved_sub.filter == filter_expr
            
            # Publish a message that matches the filter
            match_msg = "This message should match the filter"
            match_id = pubsub_service.publish_message(
                topic_name=test_topic.name,
                data=match_msg,
                attributes={"event_type": "test-event"}
            )
            assert match_id is not None
            
            # Publish a message that doesn't match the filter
            no_match_msg = "This message should NOT match the filter"
            no_match_id = pubsub_service.publish_message(
                topic_name=test_topic.name,
                data=no_match_msg,
                attributes={"event_type": "other-event"}
            )
            assert no_match_id is not None
            
            # Wait for messages to be processed
            time.sleep(5)
            
            # Pull messages - we should only get the matching message
            messages = pubsub_service.pull_messages(
                subscription_name=filter_sub_name,
                max_messages=10
            )
            
            # We may have matching messages
            if messages:
                for msg in messages:
                    message_data = msg.get("message", {})
                    data = message_data.get("data")
                    attributes = message_data.get("attributes", {})
                    
                    # Decode the message
                    decoded_data = base64.b64decode(data).decode("utf-8")
                    
                    # Verify it's the matching message
                    assert attributes.get("event_type") == "test-event"
                    
                    # Acknowledge the message
                    pubsub_service.acknowledge_messages(
                        subscription_name=filter_sub_name,
                        ack_ids=[msg.get("ackId")]
                    )
        
        finally:
            # Clean up
            try:
                pubsub_service.delete_subscription(filter_sub_name)
                print(f"Cleaned up filter test subscription: {filter_sub_name}")
            except Exception as e:
                print(f"Error cleaning up filter test subscription: {e}")
    
    def test_list_subscriptions_for_topic(self, pubsub_service: PubSubService,
                                         test_topic: PubSubTopic,
                                         test_subscription: PubSubSubscription):
        """Test listing subscriptions for a specific topic."""
        # Get subscriptions for the test topic
        subscriptions = pubsub_service.list_subscriptions(topic_name=test_topic.name)
        
        # Should find at least our test subscription
        assert len(subscriptions) >= 1
        
        # Verify our test subscription is in the list
        assert any(sub.name == test_subscription.name for sub in subscriptions)
