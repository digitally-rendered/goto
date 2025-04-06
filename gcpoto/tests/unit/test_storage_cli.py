"""Tests for Storage CLI commands."""

import os
import json
from unittest import mock
import io

import pytest
from click.testing import CliRunner

from gcpoto.cli.main import cli
from gcpoto.models.storage_object import StorageObject


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def sample_storage_object():
    """Return a sample storage object."""
    return StorageObject(
        id="test-object-id",
        name="test-object.txt",
        bucket="test-bucket",
        type="storage.object",
        project="test-project",  # Add required project field
        content_type="text/plain",
        size=256,
        etag="abc123",
        storage_class="STANDARD",
        created="2023-04-05T12:00:00Z",
        updated="2023-04-05T13:00:00Z"
    )


def test_list_objects_cli(cli_runner):
    """Test listing objects using the CLI."""
    with mock.patch("gcpoto.services.storage.StorageService", autospec=True) as mock_service_cls:
        # Setup the mock service
        mock_service = mock_service_cls.return_value
        mock_service.list_objects.return_value = [
            StorageObject(id="id1", name="object1.txt", bucket="test-bucket", type="storage.object", project="test-project"),
            StorageObject(id="id2", name="object2.txt", bucket="test-bucket", type="storage.object", project="test-project")
        ]
        
        # Run the CLI command
        result = cli_runner.invoke(
            cli, ["--project", "test-project", "storage", "list-objects", "test-bucket"]
        )
        
        # Print debug information
        print("Exit code:", result.exit_code)
        print("Exception:", result.exception)
        print("Output:", result.output)
        
        # Assert the result
        assert result.exit_code == 0
        assert "object1.txt" in result.output
        assert "object2.txt" in result.output
        
        # Verify the service was called with the right parameters
        mock_service.list_objects.assert_called_with("test-bucket", None)
        
        # Test with prefix
        result = cli_runner.invoke(
            cli, ["--project", "test-project", "storage", "list-objects", "test-bucket", "--prefix", "test/"]
        )
        
        assert result.exit_code == 0
        mock_service.list_objects.assert_called_with("test-bucket", "test/")


def test_get_object_cli(cli_runner, sample_storage_object):
    """Test getting an object's metadata using the CLI."""
    with mock.patch("gcpoto.services.storage.StorageService", autospec=True) as mock_service_cls, \
         mock.patch("gcpoto.cli.main._output_result") as mock_output_result:
        # Setup the mock service
        mock_service = mock_service_cls.return_value
        mock_service.get_object.return_value = sample_storage_object
        
        # Run the CLI command
        result = cli_runner.invoke(
            cli, ["--project", "test-project", "storage", "get-object", "test-bucket", "test-object.txt"]
        )
        
        # Assert the result
        assert result.exit_code == 0
        
        # Verify _output_result was called with the right parameters
        mock_output_result.assert_called_once()
        args, kwargs = mock_output_result.call_args
        assert args[0] == sample_storage_object  # First arg should be our object
        assert kwargs.get("output_format", args[1] if len(args) > 1 else "json") == "json"  # Default format
        
        # Verify the service was called with the right parameters
        mock_service.get_object.assert_called_with("test-bucket", "test-object.txt")


def test_download_object_cli(cli_runner):
    """Test downloading an object using the CLI."""
    with mock.patch("gcpoto.services.storage.StorageService", autospec=True) as mock_service_cls:
        # Setup the mock service
        mock_service = mock_service_cls.return_value
        mock_service.download_object.return_value = "downloaded.txt"
        
        # Run the CLI command without destination
        result = cli_runner.invoke(
            cli, ["--project", "test-project", "storage", "download", "test-bucket", "test-object.txt"]
        )
        
        # Assert the result
        assert result.exit_code == 0
        assert "Downloaded test-object.txt to" in result.output
        
        # Verify the service was called with the right parameters
        mock_service.download_object.assert_called_with("test-bucket", "test-object.txt", "test-object.txt")
        
        # Test with destination
        mock_service.download_object.reset_mock()
        result = cli_runner.invoke(
            cli, ["--project", "test-project", "storage", "download", "test-bucket", "test-object.txt", "custom-path.txt"]
        )
        
        assert result.exit_code == 0
        assert "Downloaded test-object.txt to custom-path.txt" in result.output
        mock_service.download_object.assert_called_with("test-bucket", "test-object.txt", "custom-path.txt")


def test_upload_object_cli(cli_runner, sample_storage_object):
    """Test uploading an object using the CLI."""
    with mock.patch("gcpoto.services.storage.StorageService", autospec=True) as mock_service_cls, \
         mock.patch("gcpoto.cli.main._output_result") as mock_output_result, \
            mock.patch("os.path.basename", return_value="test-file.txt"):
        # Setup the mock service
        mock_service = mock_service_cls.return_value
        mock_service.upload_object.return_value = sample_storage_object
        
        # Run the CLI command without object name
        result = cli_runner.invoke(
            cli, ["--project", "test-project", "storage", "upload", "test-bucket", "local-file.txt"]
        )
        
        # Assert the result
        assert result.exit_code == 0
        assert "Uploaded local-file.txt to test-bucket/test-file.txt" in result.output
        
        # Verify the service was called with the right parameters
        mock_service.upload_object.assert_called_with("test-bucket", "test-file.txt", "local-file.txt", None)
        
        # Test with object name and content type
        mock_service.upload_object.reset_mock()
        result = cli_runner.invoke(
            cli, [
                "--project", "test-project", "storage", "upload", "test-bucket", "local-file.txt",
                "--object-name", "custom-name.txt", "--content-type", "text/plain"
            ]
        )
        
        assert result.exit_code == 0
        assert "Uploaded local-file.txt to test-bucket/custom-name.txt" in result.output
        mock_service.upload_object.assert_called_with(
            "test-bucket", "custom-name.txt", "local-file.txt", "text/plain"
        )


def test_delete_object_cli(cli_runner):
    """Test deleting an object using the CLI."""
    with mock.patch("gcpoto.services.storage.StorageService", autospec=True) as mock_service_cls:
        # Setup the mock service
        mock_service = mock_service_cls.return_value
        mock_service.delete_object.return_value = True
        
        # Run the CLI command with auto-confirmation (--yes flag)
        result = cli_runner.invoke(
            cli, ["--project", "test-project", "storage", "delete-object", "test-bucket", "test-object.txt", "--yes"]
        )
        
        # Assert the result
        assert result.exit_code == 0
        assert "Deleted test-bucket/test-object.txt" in result.output
        
        # Verify the service was called with the right parameters
        mock_service.delete_object.assert_called_with("test-bucket", "test-object.txt")
