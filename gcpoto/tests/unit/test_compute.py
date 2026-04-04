"""Tests for the compute service implementation."""

import unittest.mock as mock
import pytest
from googleapiclient import discovery

from gcpoto.services.compute import ComputeService, ComputeInstance
from gcpoto.models.base import GCPResource


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


def test_compute_service_initialization(mock_discovery):
    """Test initializing a ComputeService."""
    mock_build, _ = mock_discovery

    service = ComputeService(project_id="test-project", credentials_file=None)

    assert service.project_id == "test-project"
    assert service.service_name == "compute"
    assert service.version == "v1"
    assert service.credentials_file is None
    assert service.resource_model == ComputeInstance

    # Verify the service was created with the expected parameters
    mock_build.assert_called_once_with("compute", "v1", credentials=None)


def test_compute_instance_from_api_response():
    """Test creating a ComputeInstance from an API response."""
    api_response = {
        "id": "123456789",
        "name": "test-instance",
        "projectId": "test-project",
        "machineType": "zones/us-central1-a/machineTypes/n1-standard-1",
        "status": "RUNNING",
        "zone": "projects/test-project/zones/us-central1-a",
        "labels": {"env": "test"},
        "creationTimestamp": "2023-01-01T00:00:00Z",
        "lastStartTimestamp": "2023-01-02T00:00:00Z",
    }

    instance = ComputeInstance.from_api_response(api_response)

    assert instance.id == "123456789"
    assert instance.name == "test-instance"
    assert instance.type == "compute.instance"
    assert instance.project == "test-project"
    assert instance.machine_type == "n1-standard-1"
    assert instance.status == "RUNNING"
    assert instance.zone == "us-central1-a"
    assert instance.labels == {"env": "test"}
    assert instance.created.isoformat().startswith("2023-01-01T00:00:00")
    assert instance.updated.isoformat().startswith("2023-01-02T00:00:00")


def test_compute_service_list_resources(mock_discovery):
    """Test the list_resources method of ComputeService."""
    _, mock_service = mock_discovery

    # Set up the mock response
    mock_instances_api = mock.MagicMock()
    mock_service.instances.return_value = mock_instances_api

    mock_list = mock.MagicMock()
    mock_instances_api.list.return_value = mock_list

    mock_response = {
        "items": [
            {
                "id": "123456789",
                "name": "test-instance-1",
                "projectId": "test-project",
                "machineType": "zones/us-central1-a/machineTypes/n1-standard-1",
                "status": "RUNNING",
                "zone": "projects/test-project/zones/us-central1-a",
            },
            {
                "id": "987654321",
                "name": "test-instance-2",
                "projectId": "test-project",
                "machineType": "zones/us-central1-a/machineTypes/n1-standard-2",
                "status": "STOPPED",
                "zone": "projects/test-project/zones/us-central1-a",
            },
        ]
    }
    mock_list.execute.return_value = mock_response

    # Create the service and call list_resources
    service = ComputeService(project_id="test-project")
    instances = service.list_resources(zone="us-central1-a")

    # Verify the API was called correctly
    mock_instances_api.list.assert_called_once_with(
        project="test-project", zone="us-central1-a"
    )

    # Verify the results
    assert len(instances) == 2
    assert isinstance(instances[0], ComputeInstance)
    assert instances[0].id == "123456789"
    assert instances[0].name == "test-instance-1"
    assert instances[0].type == "compute.instance"
    assert instances[0].machine_type == "n1-standard-1"
    assert instances[0].status == "RUNNING"
    assert instances[0].zone == "us-central1-a"

    assert isinstance(instances[1], ComputeInstance)
    assert instances[1].id == "987654321"
    assert instances[1].name == "test-instance-2"
    assert instances[1].machine_type == "n1-standard-2"
    assert instances[1].status == "STOPPED"


def test_compute_service_get_resource(mock_discovery):
    """Test the get_resource method of ComputeService."""
    _, mock_service = mock_discovery

    # Set up the mock response
    mock_instances_api = mock.MagicMock()
    mock_service.instances.return_value = mock_instances_api

    mock_get = mock.MagicMock()
    mock_instances_api.get.return_value = mock_get

    mock_response = {
        "id": "123456789",
        "name": "test-instance",
        "projectId": "test-project",
        "machineType": "zones/us-central1-a/machineTypes/n1-standard-1",
        "status": "RUNNING",
        "zone": "projects/test-project/zones/us-central1-a",
    }
    mock_get.execute.return_value = mock_response

    # Create the service and call get_resource
    service = ComputeService(project_id="test-project")
    instance = service.get_resource("test-instance", zone="us-central1-a")

    # Verify the API was called correctly
    mock_instances_api.get.assert_called_once_with(
        project="test-project", zone="us-central1-a", instance="test-instance"
    )

    # Verify the result
    assert isinstance(instance, ComputeInstance)
    assert instance.id == "123456789"
    assert instance.name == "test-instance"
    assert instance.type == "compute.instance"
    assert instance.machine_type == "n1-standard-1"
    assert instance.status == "RUNNING"
    assert instance.zone == "us-central1-a"


def test_compute_service_create_resource(mock_discovery):
    """Test the create_resource method of ComputeService."""
    _, mock_service = mock_discovery

    # Set up the mock response
    mock_instances_api = mock.MagicMock()
    mock_service.instances.return_value = mock_instances_api

    mock_insert = mock.MagicMock()
    mock_instances_api.insert.return_value = mock_insert

    mock_response = {
        "id": "123456789",
        "name": "new-instance",
        "projectId": "test-project",
        "machineType": "zones/us-central1-a/machineTypes/n1-standard-1",
        "status": "PROVISIONING",
        "zone": "projects/test-project/zones/us-central1-a",
    }
    mock_insert.execute.return_value = mock_response

    # Create the resource to insert
    instance = ComputeInstance(
        id="",  # ID will be assigned by the API
        name="new-instance",
        type="compute.instance",
        project="test-project",
        machine_type="n1-standard-1",
        status="",  # Status will be determined by the API
        zone="us-central1-a",
        labels={"env": "test"},
    )

    # Create the service and call create_resource
    service = ComputeService(project_id="test-project")
    result = service.create_resource(instance, zone="us-central1-a")

    # Verify the API was called correctly
    mock_instances_api.insert.assert_called_once_with(
        project="test-project",
        zone="us-central1-a",
        body={
            "name": "new-instance",
            "machineType": "zones/us-central1-a/machineTypes/n1-standard-1",
            "labels": {"env": "test"},
        },
    )

    # Verify the result
    assert isinstance(result, ComputeInstance)
    assert result.id == "123456789"
    assert result.name == "new-instance"
    assert result.machine_type == "n1-standard-1"
    assert result.status == "PROVISIONING"
    assert result.zone == "us-central1-a"


def test_compute_service_delete_resource(mock_discovery):
    """Test the delete_resource method of ComputeService."""
    _, mock_service = mock_discovery

    # Set up the mock response
    mock_instances_api = mock.MagicMock()
    mock_service.instances.return_value = mock_instances_api

    mock_delete = mock.MagicMock()
    mock_instances_api.delete.return_value = mock_delete

    # Create the service and call delete_resource
    service = ComputeService(project_id="test-project")
    result = service.delete_resource("test-instance", zone="us-central1-a")

    # Verify the API was called correctly
    mock_instances_api.delete.assert_called_once_with(
        project="test-project", zone="us-central1-a", instance="test-instance"
    )
    mock_delete.execute.assert_called_once()

    # Verify the result
    assert result is True
