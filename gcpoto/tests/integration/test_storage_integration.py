"""Integration tests for the Storage service."""

import os
import tempfile
import time
import uuid
import pytest
from typing import Dict, Any, List
import hashlib
import random
import string

from gcpoto.services.storage import StorageService, StorageBucket, StorageObject


pytest.mark.integration = pytest.mark.skipif(
    "GCPOTO_RUN_INTEGRATION_TESTS" not in os.environ,
    reason="Integration tests are skipped unless GCPOTO_RUN_INTEGRATION_TESTS is set",
)


@pytest.fixture(scope="module")
def test_bucket_name(test_resource_prefix: str) -> str:
    """Generate a unique bucket name for testing.

    Args:
        test_resource_prefix: Prefix for test resources.

    Returns:
        str: A unique bucket name.
    """
    # Bucket names must be globally unique across all of GCP
    # Use lowercase letters, numbers, dashes and must start with letter/number
    return f"{test_resource_prefix}-bucket-{uuid.uuid4().hex[:8]}".lower()


@pytest.fixture(scope="module")
def test_object_name() -> str:
    """Generate a unique object name for testing.

    Returns:
        str: A unique object name.
    """
    return f"test-object-{uuid.uuid4().hex}.txt"


@pytest.fixture(scope="module")
def test_object_content() -> bytes:
    """Generate random content for test objects.

    Returns:
        bytes: Random content as bytes.
    """
    # Generate 10KB of random data
    return "".join(random.choice(string.ascii_letters) for _ in range(10240)).encode(
        "utf-8"
    )


@pytest.fixture(scope="module")
def test_file(test_object_content: bytes) -> str:
    """Create a temporary file with test content.

    Args:
        test_object_content: Content to write to the file.

    Returns:
        str: Path to the temporary file.

    Yields:
        str: Path to the temporary file.
    """
    fd, path = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(test_object_content)
        yield path
    finally:
        if os.path.exists(path):
            os.unlink(path)


@pytest.fixture(scope="module")
def test_bucket(
    storage_service: StorageService,
    test_bucket_name: str,
    common_tags: Dict[str, str],
    request,
) -> StorageBucket:
    """Create a test bucket and clean it up after tests.

    Args:
        storage_service: The storage service to use.
        test_bucket_name: Name for the test bucket.
        common_tags: Tags to apply to the bucket.
        request: The pytest request fixture.

    Returns:
        StorageBucket: The created bucket.

    Yields:
        StorageBucket: The created bucket.
    """
    # Create a new bucket for testing
    bucket = storage_service.create_bucket(
        bucket_name=test_bucket_name,
        location="us-central1",
        storage_class="STANDARD",
        labels={"purpose": "integration-testing"},
        tags=common_tags,
    )

    # Register finalizer to clean up the bucket after tests
    def cleanup():
        try:
            # Delete all objects in the bucket first
            objects = storage_service.list_objects(bucket_name=test_bucket_name)
            for obj in objects:
                storage_service.delete_object(
                    bucket_name=test_bucket_name, object_name=obj.name
                )

            # Then delete the bucket
            storage_service.delete_bucket(test_bucket_name)
            print(f"Cleaned up test bucket: {test_bucket_name}")
        except Exception as e:
            print(f"Error cleaning up test bucket: {e}")

    request.addfinalizer(cleanup)

    return bucket


@pytest.mark.integration
class TestStorageIntegration:
    """Integration tests for the Storage service."""

    def test_list_buckets(self, storage_service: StorageService):
        """Test listing buckets in the project."""
        buckets = storage_service.list_resources()
        # Just verify we can get a list without error
        assert isinstance(buckets, list)
        # Print some info for debugging
        print(f"Found {len(buckets)} buckets in the project")

    def test_create_get_bucket_with_tags(
        self,
        storage_service: StorageService,
        test_bucket: StorageBucket,
        test_bucket_name: str,
        common_tags: Dict[str, str],
    ):
        """Test creating a bucket with tags and retrieving it."""
        # Verify the bucket was created
        assert test_bucket.name == test_bucket_name
        assert test_bucket.storage_class == "STANDARD"
        # Check location case-insensitively since GCP API may return location in different case
        assert test_bucket.location.lower() == "us-central1".lower()

        # Verify tags were applied
        # Note: Using get_tag method instead of tags property
        for key, value in common_tags.items():
            assert test_bucket.get_tag(key) == value

        # Verify we can retrieve the bucket
        retrieved_bucket = storage_service.get_resource(test_bucket_name)
        assert retrieved_bucket.name == test_bucket.name
        assert retrieved_bucket.storage_class == test_bucket.storage_class

        # Verify retrieved bucket has the tags
        # Note: Using get_tag method instead of tags property
        for key, value in common_tags.items():
            assert retrieved_bucket.get_tag(key) == value

    def test_object_upload_download(
        self,
        storage_service: StorageService,
        test_bucket: StorageBucket,
        test_bucket_name: str,
        test_object_name: str,
        test_file: str,
        test_object_content: bytes,
        common_tags: Dict[str, str],
    ):
        """Test uploading and downloading objects with tags."""
        # Calculate content hash for verification
        content_hash = hashlib.md5(test_object_content).hexdigest()

        # Upload the test file with tags
        object_tags = {
            **common_tags,
            "content-type": "text/plain",
            "test-case": "upload-download",
        }
        storage_service.upload(
            bucket_name=test_bucket_name,
            source_file=test_file,
            destination_blob_name=test_object_name,
            content_type="text/plain",
            tags=object_tags,
        )

        # Verify the object exists
        objects = storage_service.list_objects(bucket_name=test_bucket_name)
        assert any(obj.name == test_object_name for obj in objects)

        # Get the object metadata
        obj_meta = storage_service.get_object(
            bucket_name=test_bucket_name, object_name=test_object_name
        )
        assert obj_meta.name == test_object_name
        assert obj_meta.content_type == "text/plain"
        assert obj_meta.size == len(test_object_content)

        # Verify object has tags
        # Use get_tag method instead of tags property
        for key, value in object_tags.items():
            assert obj_meta.get_tag(key) == value

        # Download the object
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            download_path = temp_file.name

        try:
            storage_service.download(
                bucket_name=test_bucket_name,
                object_name=test_object_name,
                destination_file=download_path,
            )

            # Verify the content matches
            with open(download_path, "rb") as f:
                downloaded_content = f.read()

            assert hashlib.md5(downloaded_content).hexdigest() == content_hash
            assert len(downloaded_content) == len(test_object_content)
        finally:
            if os.path.exists(download_path):
                os.unlink(download_path)

    def test_object_delete(
        self,
        storage_service: StorageService,
        test_bucket_name: str,
        test_object_name: str,
    ):
        """Test deleting an object."""
        # Delete the test object
        storage_service.delete_object(
            bucket_name=test_bucket_name, object_name=test_object_name
        )

        # Verify it's gone
        objects = storage_service.list_objects(bucket_name=test_bucket_name)
        assert not any(obj.name == test_object_name for obj in objects)

    def test_upload_with_metadata(
        self,
        storage_service: StorageService,
        test_bucket_name: str,
        test_file: str,
        common_tags: Dict[str, str],
    ):
        """Test uploading an object with custom metadata and tags."""
        object_name = f"metadata-test-{uuid.uuid4().hex}.txt"
        custom_metadata = {
            "description": "Test file with custom metadata",
            "created-by": "integration-test",
            "sensitivity": "low",
        }

        # Upload with custom metadata and tags
        tags = {**common_tags, "purpose": "metadata-test"}
        storage_service.upload(
            bucket_name=test_bucket_name,
            source_file=test_file,
            destination_blob_name=object_name,
            metadata=custom_metadata,
            tags=tags,
        )

        # Verify metadata was applied
        obj = storage_service.get_object(
            bucket_name=test_bucket_name, object_name=object_name
        )
        assert obj.metadata is not None
        for key, value in custom_metadata.items():
            assert obj.metadata.get(key) == value

        # Verify tags were applied
        for key, value in tags.items():
            assert obj.get_tag(key) == value

        # Clean up
        storage_service.delete_object(
            bucket_name=test_bucket_name, object_name=object_name
        )

    def test_list_objects_with_prefix(
        self,
        storage_service: StorageService,
        test_bucket_name: str,
        test_file: str,
        common_tags: Dict[str, str],
    ):
        """Test listing objects with a prefix filter."""
        # Create a folder structure
        prefix = f"test-folder-{uuid.uuid4().hex[:8]}"
        object_names = [
            f"{prefix}/file1.txt",
            f"{prefix}/file2.txt",
            f"{prefix}/subfolder/file3.txt",
            f"{prefix}/subfolder/file4.txt",
        ]

        # Upload multiple files
        for obj_name in object_names:
            storage_service.upload(
                bucket_name=test_bucket_name,
                source_file=test_file,
                destination_blob_name=obj_name,
                tags=common_tags,
            )

        # List all objects with the prefix
        all_objects = storage_service.list_objects(
            bucket_name=test_bucket_name, prefix=prefix
        )
        assert len(all_objects) == 4
        assert all(obj.name in object_names for obj in all_objects)

        # List only objects in the subfolder
        subfolder_objects = storage_service.list_objects(
            bucket_name=test_bucket_name, prefix=f"{prefix}/subfolder/"
        )
        assert len(subfolder_objects) == 2
        assert all(
            obj.name.startswith(f"{prefix}/subfolder/") for obj in subfolder_objects
        )

        # Clean up
        for obj_name in object_names:
            storage_service.delete_object(
                bucket_name=test_bucket_name, object_name=obj_name
            )
