# GCPoto

A boto-like library and CLI for Google Cloud Platform. GCPoto provides a simplified, consistent interface for interacting with Google Cloud Platform services.

## Features

- Simple, consistent API for GCP services
- Unified command-line interface
- Strongly typed resource models
- Full test coverage
- JSON Schema validation

## Installation

### Prerequisites

- Python 3.9 or higher
- [Poetry](https://python-poetry.org/) (for development)

### Local Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gcpoto.git
cd gcpoto

# Install with Poetry (development mode with all dependencies)
poetry install --with dev

# Activate the virtual environment
poetry shell

# Or install as a regular package
pip install .
```

## Building

```bash
# Build the package using Poetry
poetry build

# This will create wheel and sdist in the dist/ directory
ls dist/
```

## Testing

GCPoto aims for 100% test coverage and follows strict quality standards. The project uses pytest, pytest-cov for coverage, and includes HTML and JSON reporting.

```bash
# Install development dependencies if you haven't already
poetry install --with dev

# Run tests with coverage
poetry run pytest

# Or if you're in a poetry shell
pytest

# Run tests with parallel execution
pytest -xvs

# View the coverage reports
open test-reports/report.html
```

The test commands will automatically generate:
- Terminal coverage report
- HTML coverage report in `test-reports/report.html`
- JSON coverage report in `test-reports/report.json`

## Code Quality

GCPoto follows strict code quality standards using Black and Pylint.

```bash
# Format code with Black
poetry run black gcpoto tests

# Run linting with Pylint
poetry run pylint gcpoto tests
```

## Usage

### Library Usage

GCPoto provides a consistent interface across different GCP services. Here are some examples of usage for each service.

#### Storage Service

```python
from gcpoto.services.storage import StorageService

# Initialize a storage service
storage = StorageService(
    project_id="my-project",
    credentials_file="path/to/credentials.json"
)

# List buckets
buckets = storage.list_resources()
for bucket in buckets:
    print(f"{bucket.name} ({bucket.storage_class}) in {bucket.location}")

# Get a specific bucket
bucket = storage.get_resource("my-bucket-name")

# Create a bucket with tags
from gcpoto.services.storage import StorageBucket
new_bucket = StorageBucket(
    id="",  # ID will be assigned by GCP
    name="my-new-bucket",
    type="storage.bucket",
    project="my-project",
    location="us-central1",
    storage_class="STANDARD",
    labels={"environment": "development"},
    tags={"env": "dev", "team": "data-science", "cost-center": "12345"}
)

created_bucket = storage.create_resource(new_bucket)

# List objects in a bucket
objects = storage.list_objects(bucket_name="my-bucket", prefix="folder/")
for obj in objects:
    print(f"{obj.name} - {obj.size} bytes")

# Download an object
storage.download("my-bucket", "path/to/object.txt", "local_file.txt")

# Upload an object with tags
storage.upload(
    bucket_name="my-bucket",
    source_file="local_file.txt",
    destination_blob_name="uploaded/file.txt",
    tags={"type": "document", "sensitivity": "low"}
)
```

#### Pub/Sub Service

```python
from gcpoto.services.pubsub import PubSubService

# Initialize a Pub/Sub service
pubsub = PubSubService(
    project_id="my-project",
    credentials_file="path/to/credentials.json"
)

# List all topics
topics = pubsub.list_resources()
for topic in topics:
    print(f"Topic: {topic.name}")

# Create a topic with tags
new_topic = pubsub.create_topic(
    topic_name="my-new-topic",
    labels={"purpose": "notifications"},
    tags={"env": "production", "team": "backend", "cost-center": "12345"}
)

# Publish a message to a topic
message_id = pubsub.publish_message(
    topic_name="my-topic",
    data="Hello, world!",
    attributes={"priority": "high"}
)

# Create a subscription with tags
sub = pubsub.create_subscription(
    subscription_name="my-subscription",
    topic_name="my-topic",
    ack_deadline_seconds=30,
    tags={"env": "production", "purpose": "monitoring"}
)

# Pull messages from a subscription
messages = pubsub.pull_messages("my-subscription", max_messages=10)

# Acknowledge messages
ack_ids = [msg.get('ackId') for msg in messages]
pubsub.acknowledge_messages("my-subscription", ack_ids)
```

#### Resource Tagging

All GCPoto resources support tagging for consistent organization and tracking:

```python
# Tags can be applied when creating any resource
topic = pubsub.create_topic(
    topic_name="tagged-topic",
    tags={"env": "dev", "team": "infrastructure", "project": "data-lake"}
)

# Tags are accessible as a property on the resource object
print(topic.tags)  # {'env': 'dev', 'team': 'infrastructure', 'project': 'data-lake'}

# Tags are automatically merged with labels in GCP API requests
# This provides consistent tagging across your GCP resources
```

More detailed examples can be found in the service-specific documentation.


### CLI Usage

```bash
# List storage buckets
gcpoto --project=my-project storage list-buckets

# List compute instances in a specific zone
gcpoto --project=my-project --region=us-central1 compute list-instances --zone=us-central1-a

# Format output as a table
gcpoto --project=my-project storage list-buckets --output=table

# Get help
gcpoto --help
gcpoto storage --help
```

## Documentation

Detailed documentation for each service is available in the [docs](docs/) directory:

- [Main Documentation Index](docs/README.md)
- [Storage Service Documentation](docs/services/storage.md)
- [Pub/Sub Service Documentation](docs/services/pubsub.md)
- [Resource Tagging Documentation](docs/tagging.md)

## Contributing

Contributions are welcome! Please make sure to write tests for any new features or bug fixes.

### Development Workflow

1. Fork and clone the repository
2. Install dependencies with `poetry install --with dev`
3. Create a branch for your feature
4. Write code and tests
5. Ensure tests pass and coverage is maintained
6. Submit a pull request

## License

[MIT](LICENSE)
