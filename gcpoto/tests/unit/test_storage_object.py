"""Tests for Storage Object models and services."""

import io
import os
import json
from unittest import mock
from datetime import datetime

import pytest

from gcpoto.models.storage_object import StorageObject, ObjectAclEntry
from gcpoto.schemas.storage_object import get_schema
from gcpoto.services.storage import StorageService


@pytest.fixture
def sample_object_response():
    """Return a sample storage object response."""
    return {
        "id": "test-object-id",
        "name": "test-object.txt",
        "bucket": "test-bucket",
        "contentType": "text/plain",
        "size": "256",
        "etag": "abc123",
        "generation": "123456789",
        "md5Hash": "md5hashvalue",
        "crc32c": "crc32cvalue",
        "timeCreated": "2023-04-05T12:00:00Z",
        "updated": "2023-04-05T13:00:00Z",
        "storageClass": "STANDARD",
        "contentEncoding": "identity",
        "contentDisposition": "inline",
        "cacheControl": "public, max-age=3600",
        "metadata": {"key1": "value1", "key2": "value2"},
        "acl": [
            {"entity": "allUsers", "role": "READER"},
            {"entity": "project-owners-123", "role": "OWNER"},
        ],
    }


@pytest.fixture
def mock_storage_service():
    """Create a mock storage service for testing."""
    mock_service = mock.MagicMock()
    # Mock the underlying Google API client
    mock_objects = mock.MagicMock()
    mock_service.service.objects.return_value = mock_objects
    mock_service.service._http = mock.MagicMock()
    return mock_service


def test_storage_object_schema():
    """Test that the Storage Object schema is valid."""
    schema = get_schema()
    assert schema["title"] == "GCP Storage Object"
    assert schema["type"] == "object"
    assert "name" in schema["required"]
    assert "bucket" in schema["required"]
    assert "name" in schema["properties"]
    assert "bucket" in schema["properties"]
    assert "size" in schema["properties"]
    assert "contentType" in schema["properties"]


def test_storage_object_model_creation():
    """Test creating a storage object model."""
    # Create a storage object with minimal fields
    obj = StorageObject(
        id="test-id",
        name="test.txt",
        bucket="test-bucket",
        type="storage.object",
        project="test-project",
    )
    assert obj.name == "test.txt"
    assert obj.bucket == "test-bucket"
    assert obj.type == "storage.object"

    # Create a storage object with all fields
    acl_entries = [
        ObjectAclEntry(entity="allUsers", role="READER"),
        ObjectAclEntry(entity="project-owners-123", role="OWNER"),
    ]
    obj = StorageObject(
        id="12345",
        name="test.txt",
        bucket="test-bucket",
        type="storage.object",
        project="test-project",  # Add project field
        content_type="text/plain",
        size=256,
        etag="abc123",
        generation="123456789",
        md5_hash="md5hashvalue",
        crc32c="crc32cvalue",
        created="2023-04-05T12:00:00Z",
        updated="2023-04-05T13:00:00Z",
        storage_class="STANDARD",
        content_encoding="identity",
        content_disposition="inline",
        cache_control="public, max-age=3600",
        metadata={"key1": "value1", "key2": "value2"},
        acl=acl_entries,
    )
    assert obj.name == "test.txt"
    assert obj.bucket == "test-bucket"
    assert obj.content_type == "text/plain"
    assert obj.size == 256
    assert obj.etag == "abc123"
    assert obj.storage_class == "STANDARD"
    assert obj.acl[0].entity == "allUsers"
    assert obj.acl[0].role == "READER"

    # Test serialization to JSON
    json_data = obj.model_dump_json()
    data = json.loads(json_data)
    assert data["name"] == "test.txt"
    assert data["bucket"] == "test-bucket"
    assert data["size"] == 256
    assert len(data["acl"]) == 2
    assert data["acl"][0]["entity"] == "allUsers"


def test_storage_object_from_api_response(sample_object_response):
    """Test creating a storage object from an API response."""
    obj = StorageObject.from_api_response(sample_object_response)
    assert obj.name == "test-object.txt"
    assert obj.bucket == "test-bucket"
    assert obj.content_type == "text/plain"
    assert obj.size == 256  # Size is converted to int in the model
    assert obj.etag == "abc123"
    # Check for datetime objects instead of strings
    assert obj.created.isoformat().startswith("2023-04-05T12:00")
    assert obj.updated.isoformat().startswith("2023-04-05T13:00")
    assert obj.storage_class == "STANDARD"
    assert obj.md5_hash == "md5hashvalue"
    assert obj.crc32c == "crc32cvalue"
    assert obj.cache_control == "public, max-age=3600"
    assert obj.metadata == {"key1": "value1", "key2": "value2"}
    assert len(obj.acl) == 2
    assert obj.acl[0].entity == "allUsers"
    assert obj.acl[0].role == "READER"
    assert obj.acl[1].entity == "project-owners-123"
    assert obj.acl[1].role == "OWNER"


def test_list_objects(mock_storage_service, sample_object_response):
    """Test listing objects in a bucket."""
    # Setup the mock responses
    mock_list = mock.MagicMock()
    mock_storage_service.service.objects().list.return_value = mock_list
    mock_list.execute.return_value = {
        "items": [sample_object_response, sample_object_response]
    }
    mock_storage_service.service.objects().list_next.return_value = None

    # Create the service with our mock - patch the initialization to avoid auth issues
    with mock.patch("gcpoto.services.base.GCPService.__init__", return_value=None):
        service = StorageService(project_id="test-project")
        service.service = mock_storage_service.service

    # Test listing objects
    objects = service.list_objects("test-bucket")
    assert len(objects) == 2
    assert objects[0].name == "test-object.txt"
    assert objects[0].bucket == "test-bucket"
    assert objects[0].content_type == "text/plain"

    # Verify the correct parameters were used in the API call
    mock_storage_service.service.objects().list.assert_called_with(bucket="test-bucket")

    # Test with prefix
    mock_storage_service.service.objects().list.reset_mock()
    service.list_objects("test-bucket", prefix="test/")
    mock_storage_service.service.objects().list.assert_called_with(
        bucket="test-bucket", prefix="test/"
    )

    # Test with pagination
    mock_storage_service.service.objects().list.reset_mock()
    mock_list.execute.return_value = {"items": [sample_object_response]}
    mock_list2 = mock.MagicMock()
    mock_list2.execute.return_value = {"items": [sample_object_response]}
    mock_storage_service.service.objects().list_next.return_value = mock_list2
    mock_storage_service.service.objects().list_next.side_effect = [mock_list2, None]

    objects = service.list_objects("test-bucket")
    assert len(objects) == 2
    # Verify list_next was called for pagination
    mock_storage_service.service.objects().list_next.assert_called()


def test_get_object(mock_storage_service, sample_object_response):
    """Test getting a single object."""
    # Setup the mock response
    mock_get = mock.MagicMock()
    mock_storage_service.service.objects().get.return_value = mock_get
    mock_get.execute.return_value = sample_object_response

    # Create the service with our mock - patch the initialization to avoid auth issues
    with mock.patch("gcpoto.services.base.GCPService.__init__", return_value=None):
        service = StorageService(project_id="test-project")
        service.service = mock_storage_service.service

    # Test getting an object
    obj = service.get_object("test-bucket", "test-object.txt")
    assert obj.name == "test-object.txt"
    assert obj.bucket == "test-bucket"
    assert obj.content_type == "text/plain"

    # Verify the correct parameters were used in the API call
    mock_storage_service.service.objects().get.assert_called_with(
        bucket="test-bucket", object="test-object.txt"
    )

    # Test with additional parameters
    mock_storage_service.service.objects().get.reset_mock()
    service.get_object("test-bucket", "test-object.txt", generation="12345")
    mock_storage_service.service.objects().get.assert_called_with(
        bucket="test-bucket", object="test-object.txt", generation="12345"
    )


def test_download_object(mock_storage_service, tmp_path):
    """Test downloading an object."""
    # Setup the mock response
    mock_get_media = mock.MagicMock()
    mock_storage_service.service.objects().get_media.return_value = mock_get_media

    # Create a mock downloader
    mock_downloader = mock.MagicMock()
    mock_storage_service.service._http.MediaIoBaseDownload.return_value = (
        mock_downloader
    )
    mock_downloader.next_chunk.return_value = (None, True)  # (progress, done)

    # Create test content
    test_content = b"This is test content"

    def side_effect(buffer, *args, **kwargs):
        buffer.write(test_content)
        return mock_downloader

    mock_storage_service.service._http.MediaIoBaseDownload.side_effect = side_effect

    # Create the service with our mock - patch the initialization to avoid auth issues
    with mock.patch("gcpoto.services.base.GCPService.__init__", return_value=None):
        service = StorageService(project_id="test-project")
        service.service = mock_storage_service.service

    # Test downloading an object to bytes (no destination)
    content = service.download_object("test-bucket", "test-object.txt")
    assert content == test_content

    # Verify the correct parameters were used in the API call
    mock_storage_service.service.objects().get_media.assert_called_with(
        bucket="test-bucket", object="test-object.txt"
    )

    # Test downloading to a file path
    destination = tmp_path / "downloaded.txt"
    mock_storage_service.service.objects().get_media.reset_mock()
    result = service.download_object("test-bucket", "test-object.txt", str(destination))
    assert result == str(destination)
    assert destination.read_bytes() == test_content

    # Test downloading to a file-like object
    file_obj = io.BytesIO()
    mock_storage_service.service.objects().get_media.reset_mock()
    result = service.download_object("test-bucket", "test-object.txt", file_obj)
    assert result == file_obj
    assert file_obj.getvalue() == test_content

    # Test with additional parameters
    mock_storage_service.service.objects().get_media.reset_mock()
    service.download_object("test-bucket", "test-object.txt", generation="12345")
    mock_storage_service.service.objects().get_media.assert_called_with(
        bucket="test-bucket", object="test-object.txt", generation="12345"
    )


def test_upload_object(mock_storage_service, sample_object_response, tmp_path):
    """Test uploading an object."""
    # Setup the mock response
    mock_insert = mock.MagicMock()
    mock_storage_service.service.objects().insert.return_value = mock_insert
    mock_insert.execute.return_value = sample_object_response

    # Create the service with our mock - patch the initialization to avoid auth issues
    with mock.patch("gcpoto.services.base.GCPService.__init__", return_value=None):
        service = StorageService(project_id="test-project")
        service.service = mock_storage_service.service

    # Test uploading bytes
    with mock.patch("googleapiclient.http.MediaInMemoryUpload") as mock_upload:
        content = b"This is test content"
        obj = service.upload_object("test-bucket", "test-object.txt", content)
        assert obj.name == "test-object.txt"
        assert obj.bucket == "test-bucket"

        # Verify MediaInMemoryUpload was called with the right parameters
        mock_upload.assert_called_with(content, mimetype="application/octet-stream")

        # Verify the insert call had the right parameters
        mock_storage_service.service.objects().insert.assert_called_with(
            bucket="test-bucket",
            body={"name": "test-object.txt"},
            media_body=mock_upload.return_value,
        )

    # Test uploading a string
    with mock.patch("googleapiclient.http.MediaInMemoryUpload") as mock_upload:
        content = "This is test content"
        mock_storage_service.service.objects().insert.reset_mock()
        obj = service.upload_object(
            "test-bucket", "test-object.txt", content, "text/plain"
        )

        # Verify MediaInMemoryUpload was called with the right parameters
        mock_upload.assert_called_with(content.encode("utf-8"), mimetype="text/plain")

        # Verify the insert call had the right parameters
        mock_storage_service.service.objects().insert.assert_called_with(
            bucket="test-bucket",
            body={"name": "test-object.txt", "contentType": "text/plain"},
            media_body=mock_upload.return_value,
        )

    # Test uploading a file
    with mock.patch("googleapiclient.http.MediaFileUpload") as mock_upload:
        with mock.patch("os.path.isfile", return_value=True):
            mock_storage_service.service.objects().insert.reset_mock()
            filepath = "/path/to/file.txt"
            obj = service.upload_object("test-bucket", "test-object.txt", filepath)

            # Verify MediaFileUpload was called with the right parameters
            mock_upload.assert_called_with(filepath, mimetype=None)

            # Verify the insert call had the right parameters
            mock_storage_service.service.objects().insert.assert_called_with(
                bucket="test-bucket",
                body={"name": "test-object.txt"},
                media_body=mock_upload.return_value,
            )

    # Test uploading from a file-like object
    with mock.patch("googleapiclient.http.MediaInMemoryUpload") as mock_upload:
        file_obj = io.BytesIO(b"This is test content")
        mock_storage_service.service.objects().insert.reset_mock()
        obj = service.upload_object("test-bucket", "test-object.txt", file_obj)

        # Verify the insert call had the right parameters
        mock_storage_service.service.objects().insert.assert_called_with(
            bucket="test-bucket",
            body={"name": "test-object.txt"},
            media_body=mock_upload.return_value,
        )

    # Test with additional metadata
    with mock.patch("googleapiclient.http.MediaInMemoryUpload") as mock_upload:
        content = b"This is test content"
        mock_storage_service.service.objects().insert.reset_mock()
        obj = service.upload_object(
            "test-bucket",
            "test-object.txt",
            content,
            metadata={"key1": "value1"},
            cacheControl="public, max-age=3600",
        )

        # Verify the insert call included the additional metadata
        mock_storage_service.service.objects().insert.assert_called_with(
            bucket="test-bucket",
            body={
                "name": "test-object.txt",
                "metadata": {"key1": "value1"},
                "cacheControl": "public, max-age=3600",
            },
            media_body=mock_upload.return_value,
        )


def test_delete_object(mock_storage_service):
    """Test deleting an object."""
    # Setup the mock response
    mock_delete = mock.MagicMock()
    mock_storage_service.service.objects().delete.return_value = mock_delete

    # Create the service with our mock - patch the initialization to avoid auth issues
    with mock.patch("gcpoto.services.base.GCPService.__init__", return_value=None):
        service = StorageService(project_id="test-project")
        service.service = mock_storage_service.service

    # Test deleting an object
    result = service.delete_object("test-bucket", "test-object.txt")
    assert result is True

    # Verify the correct parameters were used in the API call
    mock_storage_service.service.objects().delete.assert_called_with(
        bucket="test-bucket", object="test-object.txt"
    )

    # Test with additional parameters
    mock_storage_service.service.objects().delete.reset_mock()
    service.delete_object("test-bucket", "test-object.txt", generation="12345")
    mock_storage_service.service.objects().delete.assert_called_with(
        bucket="test-bucket", object="test-object.txt", generation="12345"
    )
