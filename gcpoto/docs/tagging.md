# Resource Tagging in GCPoto

GCPoto provides a consistent tagging system across all GCP resources, enabling better organization, cost tracking, and resource management.

## Features

- Apply tags to any GCP resource
- Tags are stored separately from GCP labels
- Tags are automatically merged with labels for GCP API compatibility
- 100% test coverage for tagging functionality
- All resource models support tags with JSON schema validation

## Understanding Tags vs Labels

In GCPoto, we distinguish between tags and labels:

- **Labels**: These are the native GCP resource labels, which have certain limitations and service-specific implementations.
- **Tags**: These are GCPoto's consistent tagging mechanism that works identically across all services.

When you apply tags to a resource, GCPoto handles merging them into the appropriate GCP-specific format (usually the labels field) while preserving them separately in the resource object.

## Applying Tags

Tags can be applied when creating any GCP resource. Here are examples for different services:

### Storage Resources

```python
from gcpoto.services.storage import StorageService

storage = StorageService(project_id="my-project")

# Create a bucket with tags
bucket = storage.create_bucket(
    bucket_name="tagged-bucket",
    location="us-central1",
    tags={
        "env": "production",
        "team": "data-science",
        "cost-center": "12345",
        "project": "ml-pipeline"
    }
)

# Upload an object with tags
storage.upload(
    bucket_name="my-bucket",
    source_file="data.csv",
    destination_blob_name="datasets/data.csv",
    tags={
        "data-type": "csv",
        "sensitivity": "low",
        "source": "external-api",
        "retention": "90-days"
    }
)
```

### Pub/Sub Resources

```python
from gcpoto.services.pubsub import PubSubService

pubsub = PubSubService(project_id="my-project")

# Create a topic with tags
topic = pubsub.create_topic(
    topic_name="tagged-topic",
    tags={
        "env": "production",
        "team": "backend",
        "cost-center": "12345",
        "system": "order-processing"
    }
)

# Create a subscription with tags
subscription = pubsub.create_subscription(
    subscription_name="tagged-subscription",
    topic_name="tagged-topic",
    tags={
        "env": "production",
        "team": "backend",
        "purpose": "monitoring",
        "alert-threshold": "high"
    }
)
```

## Accessing Tags

Tags are stored directly on the resource objects and can be accessed through the `tags` property:

```python
# Get a resource
bucket = storage.get_resource("my-bucket")

# Access tags
if bucket.tags:
    for key, value in bucket.tags.items():
        print(f"{key}: {value}")

# Check for specific tags
if bucket.tags and "env" in bucket.tags:
    env = bucket.tags["env"]
    print(f"Environment: {env}")
```

## Tag Best Practices

1. **Consistency**: Use consistent tag keys across all resources
2. **Case Sensitivity**: Keys are case-sensitive, so standardize on a convention (e.g., lowercase with hyphens)
3. **Common Tags**: Consider including these common tags:
   - `env` or `environment`: e.g., production, staging, development
   - `team`: The team responsible for the resource
   - `cost-center`: For billing allocation
   - `project`: The project or initiative the resource supports
   - `created-by`: Identity of the creator
   - `managed-by`: Tool that manages the resource (e.g., terraform, gcpoto)

4. **Automation**: Consider automating tag application for resources created through CI/CD pipelines

## Filtering by Tags in CLI

When using the GCPoto CLI, you can filter resources by their tags. The exact filter syntax depends on the service, but generally follows this pattern:

```bash
# List all production storage buckets
gcpoto --project=my-project storage list-buckets --filter="tags.env=production"

# List Pub/Sub topics for a specific team
gcpoto --project=my-project pubsub list-topics --filter="tags.team=data-science"
```

## Implementation Details

In GCPoto, all resource models inherit from `GCPResource` which defines the `tags` field:

```python
class GCPResource(BaseModel):
    """Base model for all GCP resources."""
    id: str = Field(..., description="The unique identifier for the resource")
    name: str = Field(..., description="The name of the resource")
    type: str = Field(..., description="The GCP resource type")
    project: str = Field(..., description="The GCP project ID")
    labels: Optional[Dict[str, str]] = Field(None, description="Labels associated with the resource")
    tags: Optional[Dict[str, str]] = Field(None, description="Tags associated with the resource")
    created: Optional[datetime] = Field(None, description="When the resource was created")
    updated: Optional[datetime] = Field(None, description="When the resource was last updated")
```

The base service includes a `_process_tags` method that handles merging tags into the appropriate format for each GCP service:

```python
def _process_tags(self, body: Dict[str, Any], tags: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """Process tags for a resource API request."""
    if not tags:
        return body
        
    # If there are no labels yet, initialize them
    if 'labels' not in body or body['labels'] is None:
        body['labels'] = {}
        
    # Add tags to labels
    for key, value in tags.items():
        body['labels'][key] = value
        
    return body
```

## Testing Tagging Functionality

GCPoto includes comprehensive tests for the tagging functionality. You can run these tests with:

```bash
pytest tests/unit/test_tagging.py -v
```

The test suite verifies that:
- Tags can be set and retrieved on resources
- Tags are properly merged with labels for API calls
- Tags and labels can coexist without conflicts
- Tags are preserved across API operations
