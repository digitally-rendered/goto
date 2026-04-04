# GCPoto Storage Service

The Storage Service allows you to interact with Google Cloud Storage, providing a simplified interface for managing buckets and objects.

## Features

- List, create, get, and delete storage buckets
- List, upload, download, and delete storage objects
- Support for tags and labels on all resources
- Strongly typed models with full validation

## Installation

The Storage Service is included with the GCPoto package:

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
from gcpoto.services.storage import StorageService

# Initialize with project ID and credentials
storage = StorageService(
    project_id="my-project-id",
    credentials_file="path/to/credentials.json"
)

# Or use environment credentials
# Make sure GOOGLE_APPLICATION_CREDENTIALS environment variable is set
storage = StorageService(project_id="my-project-id")
```

## Working with Buckets

### List Buckets

```python
# List all buckets in the project
buckets = storage.list_resources()

# Print bucket details
for bucket in buckets:
    print(f"Bucket: {bucket.name}")
    print(f"  Location: {bucket.location}")
    print(f"  Storage class: {bucket.storage_class}")
    print(f"  Created: {bucket.created}")
    if bucket.tags:
        print(f"  Tags: {bucket.tags}")
```

### Get a Bucket

```python
# Get details for a specific bucket
bucket = storage.get_resource("my-bucket-name")

# Access bucket properties
print(f"Bucket {bucket.name} in {bucket.location}")
print(f"Storage class: {bucket.storage_class}")
```

### Create a Bucket

```python
from gcpoto.services.storage import StorageBucket

# Create a new bucket with tags
new_bucket = StorageBucket(
    id="",  # ID will be assigned by GCP
    name="my-new-bucket",
    type="storage.bucket",
    project="my-project-id",
    location="us-central1",
    storage_class="STANDARD",
    labels={"environment": "production"},
    tags={"team": "data-engineering", "cost-center": "12345"}
)

# Create the bucket
created_bucket = storage.create_resource(new_bucket)

# Alternative direct method
bucket = storage.create_bucket(
    bucket_name="my-other-bucket",
    location="us-west1",
    storage_class="NEARLINE",
    tags={"purpose": "backup", "retention": "1-year"}
)
```

### Delete a Bucket

```python
# Delete a bucket
success = storage.delete_resource("my-bucket-name")
if success:
    print("Bucket deleted successfully")
else:
    print("Failed to delete bucket")

# Alternative direct method
storage.delete_bucket("my-bucket-name")
```

## Working with Objects

### List Objects

```python
# List all objects in a bucket
objects = storage.list_objects(bucket_name="my-bucket")

# List objects with a prefix (folder-like structure)
objects = storage.list_objects(bucket_name="my-bucket", prefix="folder/subfolder/")

# Print object details
for obj in objects:
    print(f"Object: {obj.name}")
    print(f"  Size: {obj.size} bytes")
    print(f"  Content type: {obj.content_type}")
    print(f"  Updated: {obj.updated}")
    if obj.tags:
        print(f"  Tags: {obj.tags}")
```

### Get Object Metadata

```python
# Get metadata for a specific object
object_meta = storage.get_object(bucket_name="my-bucket", object_name="path/to/object.txt")

# Access object properties
print(f"Object: {object_meta.name}")
print(f"Size: {object_meta.size} bytes")
print(f"Content type: {object_meta.content_type}")
print(f"MD5 hash: {object_meta.md5_hash}")
```

### Download an Object

```python
# Download an object to a local file
storage.download(
    bucket_name="my-bucket",
    object_name="path/to/object.txt",
    destination_file="local/path/file.txt"
)

# Or get the object content directly
content = storage.download_as_bytes(bucket_name="my-bucket", object_name="path/to/object.txt")
print(f"Content length: {len(content)}")
```

### Upload an Object

```python
# Upload a file to a bucket with tags
storage.upload(
    bucket_name="my-bucket",
    source_file="local/path/file.txt",
    destination_blob_name="path/in/bucket/file.txt",
    content_type="text/plain",  # Optional, will be auto-detected if not provided
    tags={"type": "log", "source": "application-1", "retention": "90-days"}
)

# Upload content from memory
from io import BytesIO

content = BytesIO(b"Hello, world!")
storage.upload_from_file(
    bucket_name="my-bucket",
    file_obj=content,
    destination_blob_name="hello.txt",
    content_type="text/plain",
    tags={"type": "message"}
)
```

### Delete an Object

```python
# Delete an object
storage.delete_object(bucket_name="my-bucket", object_name="path/to/object.txt")

# Delete multiple objects
storage.delete_objects(
    bucket_name="my-bucket",
    object_names=["path/to/object1.txt", "path/to/object2.txt"]
)
```

## CLI Usage

GCPoto provides a command-line interface for common operations:

```bash
# List buckets
gcpoto --project=my-project-id storage list-buckets

# Create a bucket
gcpoto --project=my-project-id storage create-bucket my-new-bucket --location=us-central1

# List objects in a bucket
gcpoto --project=my-project-id storage list-objects my-bucket --prefix=folder/

# Download an object
gcpoto --project=my-project-id storage download my-bucket path/to/object.txt ./local-file.txt

# Upload an object
gcpoto --project=my-project-id storage upload my-bucket ./local-file.txt path/in/bucket/file.txt

# Delete an object
gcpoto --project=my-project-id storage delete-object my-bucket path/to/object.txt
```

## JSON Schema

The Storage service uses JSON schema validation for all models. The schemas ensure that all data conforms to the expected structure before being sent to the Google Cloud API.

## Testing

All storage service functionality is fully tested with unit tests. The test suite includes tests for bucket and object operations, error conditions, and edge cases.

To run the storage service tests specifically:

```bash
pytest tests/unit/test_storage*.py -v
```

The tests use mocking to avoid actual calls to the Google Cloud API, making them suitable for CI/CD pipelines.
