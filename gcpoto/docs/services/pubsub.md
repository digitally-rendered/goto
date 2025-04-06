# GCPoto Pub/Sub Service

The Pub/Sub Service provides a simplified interface for interacting with Google Cloud Pub/Sub, allowing you to manage topics, subscriptions, and messages with a consistent API.

## Features

- Create, list, get, and delete Pub/Sub topics
- Create, list, get, and delete Pub/Sub subscriptions
- Publish messages to topics
- Pull and acknowledge messages from subscriptions
- Support for tags and labels on all resources
- Strongly typed models with full JSON schema validation
- 100% test coverage

## Installation

The Pub/Sub Service is included with the GCPoto package:

```bash
# Install from source
git clone https://github.com/yourusername/gcpoto.git
cd gcpoto
pip install .

# Or with poetry
poetry install
```

## Initialization

```python
from gcpoto.services.pubsub import PubSubService

# Initialize with project ID and credentials
pubsub = PubSubService(
    project_id="my-project-id",
    credentials_file="path/to/credentials.json"
)

# Or use environment credentials
# Make sure GOOGLE_APPLICATION_CREDENTIALS environment variable is set
pubsub = PubSubService(project_id="my-project-id")
```

## Working with Topics

### List Topics

```python
# List all topics in the project
topics = pubsub.list_resources()

# Print topic details
for topic in topics:
    print(f"Topic: {topic.name}")
    print(f"  Full path: {topic.id}")
    if topic.labels:
        print(f"  Labels: {topic.labels}")
    if topic.tags:
        print(f"  Tags: {topic.tags}")
    if topic.message_storage_policy:
        print(f"  Storage regions: {topic.message_storage_policy.allowed_persistence_regions}")
```

### Get a Topic

```python
# Get a specific topic by name
topic = pubsub.get_topic("my-topic")

# Get a topic using its full path
topic = pubsub.get_topic("projects/my-project-id/topics/my-topic")

# Access topic properties
print(f"Topic: {topic.name}")
print(f"Project: {topic.project}")
print(f"Created: {topic.created}")
```

### Create a Topic

```python
# Create a simple topic
topic = pubsub.create_topic("my-new-topic")

# Create a topic with advanced options and tags
topic = pubsub.create_topic(
    topic_name="my-advanced-topic",
    labels={"purpose": "notifications"},
    tags={"env": "production", "team": "backend", "cost-center": "12345"},
    message_storage_policy={"allowedPersistenceRegions": ["us-central1", "us-east1"]},
    message_retention_duration="86400s"  # 1 day retention
)

# Access the newly created topic
print(f"Created topic: {topic.name}")
print(f"Full path: {topic.id}")
```

### Delete a Topic

```python
# Delete a topic
success = pubsub.delete_topic("my-topic")
if success:
    print("Topic deleted successfully")
```

## Publishing Messages

```python
# Publish a simple message
message_id = pubsub.publish_message(
    topic_name="my-topic",
    data="Hello, world!"
)
print(f"Published message ID: {message_id}")

# Publish a message with attributes
message_id = pubsub.publish_message(
    topic_name="my-topic",
    data="Important notification",
    attributes={
        "priority": "high",
        "category": "alert",
        "source": "monitoring-system"
    }
)

# Publish binary data
import json
data = json.dumps({"user_id": 12345, "action": "login"}).encode("utf-8")
message_id = pubsub.publish_message(
    topic_name="my-topic",
    data=data,
    attributes={"event_type": "user_activity"}
)
```

## Working with Subscriptions

### List Subscriptions

```python
# List all subscriptions in the project
subscriptions = pubsub.list_subscriptions()

# List subscriptions for a specific topic
topic_subscriptions = pubsub.list_subscriptions(topic_name="my-topic")

# Print subscription details
for sub in subscriptions:
    print(f"Subscription: {sub.name}")
    print(f"  Topic: {sub.topic}")
    print(f"  Ack deadline: {sub.ack_deadline_seconds} seconds")
    if sub.push_config:
        print(f"  Push endpoint: {sub.push_config.push_endpoint}")
    if sub.tags:
        print(f"  Tags: {sub.tags}")
```

### Get a Subscription

```python
# Get a specific subscription
subscription = pubsub.get_subscription("my-subscription")

# Access subscription properties
print(f"Subscription: {subscription.name}")
print(f"Topic: {subscription.topic}")
print(f"Project: {subscription.project}")
```

### Create a Subscription

```python
# Create a simple pull subscription
subscription = pubsub.create_subscription(
    subscription_name="my-pull-subscription",
    topic_name="my-topic"
)

# Create a push subscription with tags
subscription = pubsub.create_subscription(
    subscription_name="my-push-subscription",
    topic_name="my-topic",
    push_config={"pushEndpoint": "https://my-app.example.com/push-handler"},
    ack_deadline_seconds=30,
    retain_acked_messages=True,
    message_retention_duration="604800s",  # 7 days
    labels={"type": "push"},
    tags={"env": "production", "team": "backend", "purpose": "monitoring"},
    filter_expr="attributes.event_type = \"alert\"",  # Only receive alert events
    enable_message_ordering=True
)

# Create a subscription with dead-letter policy
subscription = pubsub.create_subscription(
    subscription_name="my-dl-subscription",
    topic_name="my-topic",
    dead_letter_policy={
        "deadLetterTopic": "projects/my-project-id/topics/dead-letter",
        "maxDeliveryAttempts": 5
    },
    retry_policy={
        "minimumBackoff": "10s",
        "maximumBackoff": "600s"
    }
)
```

### Delete a Subscription

```python
# Delete a subscription
success = pubsub.delete_subscription("my-subscription")
if success:
    print("Subscription deleted successfully")
```

## Working with Messages

### Pull Messages

```python
# Pull messages from a subscription
messages = pubsub.pull_messages("my-subscription", max_messages=5)

# Process the messages
for msg in messages:
    ack_id = msg.get("ackId")
    message_data = msg.get("message", {})
    
    # Get message content
    data = message_data.get("data", "")
    attributes = message_data.get("attributes", {})
    message_id = message_data.get("messageId")
    
    # Handle base64 encoded data
    import base64
    try:
        decoded_data = base64.b64decode(data).decode("utf-8")
        print(f"Message {message_id}: {decoded_data}")
    except Exception:
        print(f"Message {message_id}: {data} (could not decode)")
    
    # Process message attributes
    for key, value in attributes.items():
        print(f"  {key}: {value}")
```

### Acknowledge Messages

```python
# Pull messages
messages = pubsub.pull_messages("my-subscription", max_messages=10)

# Collect the acknowledgement IDs
ack_ids = [msg.get("ackId") for msg in messages]

# Process messages...

# Acknowledge the messages
if ack_ids:
    success = pubsub.acknowledge_messages("my-subscription", ack_ids)
    if success:
        print(f"Acknowledged {len(ack_ids)} messages")
```

## CLI Usage

GCPoto provides a command-line interface for common Pub/Sub operations:

```bash
# List topics
gcpoto --project=my-project-id pubsub list-topics

# Create a topic
gcpoto --project=my-project-id pubsub create-topic my-new-topic --label="env=prod" --region="us-central1"

# Get a topic
gcpoto --project=my-project-id pubsub get-topic my-topic

# Publish a message
gcpoto --project=my-project-id pubsub publish my-topic "Hello from CLI" --attribute="source=cli"

# List subscriptions
gcpoto --project=my-project-id pubsub list-subscriptions

# List subscriptions for a specific topic
gcpoto --project=my-project-id pubsub list-subscriptions --topic=my-topic

# Create a subscription
gcpoto --project=my-project-id pubsub create-subscription my-subscription my-topic --ack-deadline=30

# Pull messages
gcpoto --project=my-project-id pubsub pull my-subscription --max-messages=5 --auto-ack
```

## JSON Schema

The Pub/Sub service uses JSON schema validation for all models, ensuring that all data conforms to the expected structure before being sent to the Google Cloud Pub/Sub API.

## Testing

All Pub/Sub service functionality is fully tested with unit tests. The test suite includes tests for topic and subscription operations, message handling, error conditions, and edge cases.

To run the Pub/Sub service tests specifically:

```bash
pytest tests/unit/test_pubsub*.py -v
```

The tests use mocking to avoid actual calls to the Google Cloud API, making them suitable for CI/CD pipelines.

## Error Handling

The Pub/Sub service provides meaningful error messages for common issues:

```python
try:
    # Try to create a topic that already exists
    pubsub.create_topic("existing-topic")
except ValueError as e:
    print(f"Error: {e}")  # Will print: "Error: Topic 'existing-topic' already exists"

try:
    # Try to get a topic that doesn't exist
    pubsub.get_topic("non-existent-topic")
except Exception as e:
    print(f"Error: {e}")  # Will print appropriate error message
```
