"""Tests for the base service class."""

import unittest.mock as mock
import pytest
from googleapiclient import discovery

from gcpoto.services.base import GCPService
from gcpoto.models.base import GCPResource
from gcpoto.services.storage import StorageService, StorageBucket


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


def test_gcp_service_initialization(mock_discovery):
    """Test initializing a GCPService."""
    mock_build, _ = mock_discovery

    service = GCPService(
        project_id="test-project", service_name="test-service", version="v1"
    )

    assert service.project_id == "test-project"
    assert service.service_name == "test-service"
    assert service.version == "v1"
    assert service.credentials_file is None
    assert service.scopes == ["https://www.googleapis.com/auth/test-service"]
    assert service.resource_model == GCPResource

    # Verify the service was created with the expected parameters
    mock_build.assert_called_once_with("test-service", "v1", credentials=None)


def test_gcp_service_with_credentials(mock_discovery):
    """Test initializing a GCPService with credentials."""
    with mock.patch(
        "google.oauth2.service_account.Credentials.from_service_account_file"
    ) as mock_creds:
        mock_build, _ = mock_discovery
        mock_credentials = mock.MagicMock()
        mock_creds.return_value = mock_credentials

        service = GCPService(
            project_id="test-project",
            service_name="test-service",
            version="v1",
            credentials_file="/path/to/credentials.json",
            scopes=["https://www.googleapis.com/auth/test-scope"],
        )

        assert service.credentials_file == "/path/to/credentials.json"
        assert service.scopes == ["https://www.googleapis.com/auth/test-scope"]

        # Verify credentials were loaded with the correct parameters
        mock_creds.assert_called_once_with(
            "/path/to/credentials.json",
            scopes=["https://www.googleapis.com/auth/test-scope"],
        )

        # Verify the service was created with the credentials
        mock_build.assert_called_once_with(
            "test-service", "v1", credentials=mock_credentials
        )


def test_storage_service_list_resources(mock_discovery):
    """Test the list_resources method of StorageService."""
    _, mock_service = mock_discovery

    # Set up the mock response
    mock_bucket_api = mock.MagicMock()
    mock_service.buckets.return_value = mock_bucket_api

    mock_list = mock.MagicMock()
    mock_bucket_api.list.return_value = mock_list

    mock_response = {
        "items": [
            {
                "id": "bucket-1",
                "name": "test-bucket-1",
                "projectNumber": "test-project",
                "location": "us-central1",
                "storageClass": "STANDARD",
                "timeCreated": "2023-01-01T00:00:00Z",
            },
            {
                "id": "bucket-2",
                "name": "test-bucket-2",
                "projectNumber": "test-project",
                "location": "us-west1",
                "storageClass": "NEARLINE",
                "timeCreated": "2023-01-02T00:00:00Z",
            },
        ]
    }
    mock_list.execute.return_value = mock_response

    # Create the service and call list_resources
    service = StorageService(project_id="test-project")
    buckets = service.list_resources()

    # Verify the API was called correctly
    mock_bucket_api.list.assert_called_once_with(project="test-project")

    # Verify the results
    assert len(buckets) == 2
    assert isinstance(buckets[0], StorageBucket)
    assert buckets[0].id == "bucket-1"
    assert buckets[0].name == "test-bucket-1"
    assert buckets[0].type == "storage.bucket"
    assert buckets[0].location == "us-central1"
    assert buckets[0].storage_class == "STANDARD"

    assert isinstance(buckets[1], StorageBucket)
    assert buckets[1].id == "bucket-2"
    assert buckets[1].name == "test-bucket-2"
    assert buckets[1].location == "us-west1"
    assert buckets[1].storage_class == "NEARLINE"


def test_storage_service_get_resource(mock_discovery):
    """Test the get_resource method of StorageService."""
    _, mock_service = mock_discovery

    # Set up the mock response
    mock_bucket_api = mock.MagicMock()
    mock_service.buckets.return_value = mock_bucket_api

    mock_get = mock.MagicMock()
    mock_bucket_api.get.return_value = mock_get

    mock_response = {
        "id": "bucket-1",
        "name": "test-bucket",
        "projectNumber": "test-project",
        "location": "us-central1",
        "storageClass": "STANDARD",
        "timeCreated": "2023-01-01T00:00:00Z",
    }
    mock_get.execute.return_value = mock_response

    # Create the service and call get_resource
    service = StorageService(project_id="test-project")
    bucket = service.get_resource("test-bucket")

    # Verify the API was called correctly
    mock_bucket_api.get.assert_called_once_with(bucket="test-bucket")

    # Verify the result
    assert isinstance(bucket, StorageBucket)
    assert bucket.id == "bucket-1"
    assert bucket.name == "test-bucket"
    assert bucket.type == "storage.bucket"
    assert bucket.location == "us-central1"
    assert bucket.storage_class == "STANDARD"


def test_storage_service_create_resource(mock_discovery):
    """Test the create_resource method of StorageService."""
    _, mock_service = mock_discovery

    # Set up the mock response
    mock_bucket_api = mock.MagicMock()
    mock_service.buckets.return_value = mock_bucket_api

    mock_insert = mock.MagicMock()
    mock_bucket_api.insert.return_value = mock_insert

    mock_response = {
        "id": "bucket-1",
        "name": "new-bucket",
        "projectNumber": "test-project",
        "location": "us-central1",
        "storageClass": "STANDARD",
        "timeCreated": "2023-01-01T00:00:00Z",
    }
    mock_insert.execute.return_value = mock_response

    # Create the resource to insert
    bucket = StorageBucket(
        id="",  # ID will be assigned by the API
        name="new-bucket",
        type="storage.bucket",
        project="test-project",
        location="us-central1",
        storage_class="STANDARD",
        labels={"env": "test"},
    )

    # Create the service and call create_resource
    service = StorageService(project_id="test-project")
    result = service.create_resource(bucket)

    # Verify the API was called correctly
    mock_bucket_api.insert.assert_called_once_with(
        project="test-project",
        body={
            "name": "new-bucket",
            "location": "us-central1",
            "storageClass": "STANDARD",
            "labels": {"env": "test"},
        },
    )

    # Verify the result
    assert isinstance(result, StorageBucket)
    assert result.id == "bucket-1"
    assert result.name == "new-bucket"
    assert result.location == "us-central1"
    assert result.storage_class == "STANDARD"


def test_storage_service_delete_resource(mock_discovery):
    """Test the delete_resource method of StorageService."""
    _, mock_service = mock_discovery

    # Set up the mock response
    mock_bucket_api = mock.MagicMock()
    mock_service.buckets.return_value = mock_bucket_api

    mock_delete = mock.MagicMock()
    mock_bucket_api.delete.return_value = mock_delete

    # Create the service and call delete_resource
    service = StorageService(project_id="test-project")
    result = service.delete_resource("test-bucket")

    # Verify the API was called correctly
    mock_bucket_api.delete.assert_called_once_with(bucket="test-bucket")
    mock_delete.execute.assert_called_once()

    # Verify the result
    assert result is True
