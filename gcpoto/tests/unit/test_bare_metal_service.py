"""Tests for the Bare Metal Solution service implementation."""

import unittest.mock as mock
import pytest

from gcpoto.services.bare_metal import BareMetalService
from gcpoto.models.bare_metal import BareMetalInstance, BareMetalVolume


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


SAMPLE_INSTANCE_RESPONSE = {
    "id": "inst-abc123",
    "name": "projects/test-project/locations/us-central1/instances/my-instance",
    "projectId": "test-project",
    "location": "us-central1",
    "machineType": "o2-standard-32-metal",
    "state": "RUNNING",
    "osImage": "ubuntu-2204-lts",
    "networkTemplate": "projects/test-project/locations/us-central1/networkTemplates/default",
    "networks": [
        {"network": "my-network", "ipAddress": "10.0.0.5"},
    ],
    "luns": [
        {"name": "boot-lun", "sizeGb": 200},
    ],
    "labels": {"env": "test", "team": "infra"},
    "createTime": "2025-05-01T00:00:00Z",
    "updateTime": "2025-05-02T00:00:00Z",
}

SAMPLE_VOLUME_RESPONSE = {
    "id": "vol-abc123",
    "name": "projects/test-project/locations/us-central1/volumes/my-volume",
    "projectId": "test-project",
    "location": "us-central1",
    "storageType": "SSD",
    "sizeGib": 500,
    "state": "READY",
    "snapshotAutoDeleteBehavior": "OLDEST_FIRST",
    "labels": {"tier": "premium"},
    "createTime": "2025-05-01T00:00:00Z",
    "updateTime": "2025-05-02T00:00:00Z",
}


class TestBareMetalServiceInit:
    """Tests for BareMetalService initialization."""

    def test_initialization(self, mock_discovery):
        mock_build, _ = mock_discovery
        service = BareMetalService(
            project_id="test-project", credentials_file=None
        )

        assert service.project_id == "test-project"
        assert service.service_name == "baremetalsolution"
        assert service.version == "v2"
        assert service.credentials_file is None
        assert service.resource_model == BareMetalInstance
        mock_build.assert_called_once_with(
            "baremetalsolution", "v2", credentials=None
        )


class TestBareMetalInstanceModel:
    """Tests for the BareMetalInstance model."""

    def test_from_api_response(self):
        instance = BareMetalInstance.from_api_response(SAMPLE_INSTANCE_RESPONSE)

        assert instance.id == "inst-abc123"
        assert instance.name == "projects/test-project/locations/us-central1/instances/my-instance"
        assert instance.type == "baremetalsolution.instance"
        assert instance.project == "test-project"
        assert instance.location == "us-central1"
        assert instance.machine_type == "o2-standard-32-metal"
        assert instance.state == "RUNNING"
        assert instance.os_image == "ubuntu-2204-lts"
        assert instance.network_template is not None
        assert instance.networks is not None
        assert len(instance.networks) == 1
        assert instance.luns is not None
        assert len(instance.luns) == 1
        assert instance.labels == {"env": "test", "team": "infra"}
        assert instance.created.isoformat().startswith("2025-05-01T00:00:00")

    def test_from_api_response_minimal(self):
        response = {"name": "bare-instance", "projectId": "p"}
        instance = BareMetalInstance.from_api_response(response)

        assert instance.name == "bare-instance"
        assert instance.id == ""
        assert instance.location == ""
        assert instance.machine_type == ""
        assert instance.state == ""
        assert instance.os_image is None
        assert instance.network_template is None
        assert instance.networks is None
        assert instance.luns is None

    def test_get_tag(self):
        instance = BareMetalInstance.from_api_response(SAMPLE_INSTANCE_RESPONSE)
        assert instance.get_tag("env") == "test"
        assert instance.get_tag("team") == "infra"
        assert instance.get_tag("missing") == ""
        assert instance.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        response = {"name": "bare", "projectId": "p"}
        instance = BareMetalInstance.from_api_response(response)
        assert instance.get_tag("env") == ""
        assert instance.get_tag("env", "fallback") == "fallback"


class TestBareMetalVolumeModel:
    """Tests for the BareMetalVolume model."""

    def test_from_api_response(self):
        volume = BareMetalVolume.from_api_response(SAMPLE_VOLUME_RESPONSE)

        assert volume.id == "vol-abc123"
        assert volume.name == "projects/test-project/locations/us-central1/volumes/my-volume"
        assert volume.type == "baremetalsolution.volume"
        assert volume.project == "test-project"
        assert volume.location == "us-central1"
        assert volume.storage_type == "SSD"
        assert volume.size_gib == 500
        assert volume.state == "READY"
        assert volume.snapshot_auto_delete_behavior == "OLDEST_FIRST"

    def test_from_api_response_minimal(self):
        response = {"name": "bare-volume", "projectId": "p"}
        volume = BareMetalVolume.from_api_response(response)

        assert volume.name == "bare-volume"
        assert volume.id == ""
        assert volume.location == ""
        assert volume.storage_type == ""
        assert volume.size_gib == 0
        assert volume.state == ""
        assert volume.snapshot_auto_delete_behavior is None


def _setup_instance_mock(mock_service):
    """Helper to set up the nested mock chain for instance operations."""
    mock_projects = mock.MagicMock()
    mock_service.projects.return_value = mock_projects
    mock_locations = mock.MagicMock()
    mock_projects.locations.return_value = mock_locations
    mock_instances = mock.MagicMock()
    mock_locations.instances.return_value = mock_instances
    return mock_instances


def _setup_volume_mock(mock_service):
    """Helper to set up the nested mock chain for volume operations."""
    mock_projects = mock.MagicMock()
    mock_service.projects.return_value = mock_projects
    mock_locations = mock.MagicMock()
    mock_projects.locations.return_value = mock_locations
    mock_volumes = mock.MagicMock()
    mock_locations.volumes.return_value = mock_volumes
    return mock_volumes


class TestBareMetalServiceInstances:
    """Tests for instance-related methods."""

    def test_list_instances(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _setup_instance_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {
            "instances": [SAMPLE_INSTANCE_RESPONSE],
        }

        service = BareMetalService(project_id="test-project")
        results = service.list_instances("us-central1")

        mock_instances.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )
        assert len(results) == 1
        assert isinstance(results[0], BareMetalInstance)
        assert results[0].state == "RUNNING"

    def test_list_instances_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _setup_instance_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = BareMetalService(project_id="test-project")
        results = service.list_instances("us-central1")

        assert results == []

    def test_get_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _setup_instance_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_instances.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = BareMetalService(project_id="test-project")
        result = service.get_instance("us-central1", "my-instance")

        mock_instances.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/instances/my-instance"
        )
        assert isinstance(result, BareMetalInstance)
        assert result.state == "RUNNING"

    def test_update_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _setup_instance_mock(mock_service)
        mock_patch = mock.MagicMock()
        mock_instances.patch.return_value = mock_patch
        operation_response = {"name": "operation-123", "done": False}
        mock_patch.execute.return_value = operation_response

        service = BareMetalService(project_id="test-project")
        result = service.update_instance(
            location="us-central1",
            instance_name="my-instance",
            update_mask="labels",
            update_fields={"labels": {"env": "prod"}},
        )

        mock_instances.patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/instances/my-instance",
            updateMask="labels",
            body={"labels": {"env": "prod"}},
        )
        assert result == operation_response

    def test_reset_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _setup_instance_mock(mock_service)
        mock_reset = mock.MagicMock()
        mock_instances.reset.return_value = mock_reset
        operation_response = {"name": "operation-456", "done": False}
        mock_reset.execute.return_value = operation_response

        service = BareMetalService(project_id="test-project")
        result = service.reset_instance("us-central1", "my-instance")

        mock_instances.reset.assert_called_once_with(
            name="projects/test-project/locations/us-central1/instances/my-instance"
        )
        assert result == operation_response

    def test_start_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _setup_instance_mock(mock_service)
        mock_start = mock.MagicMock()
        mock_instances.start.return_value = mock_start
        operation_response = {"name": "operation-789", "done": False}
        mock_start.execute.return_value = operation_response

        service = BareMetalService(project_id="test-project")
        result = service.start_instance("us-central1", "my-instance")

        mock_instances.start.assert_called_once_with(
            name="projects/test-project/locations/us-central1/instances/my-instance"
        )
        assert result == operation_response

    def test_stop_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _setup_instance_mock(mock_service)
        mock_stop = mock.MagicMock()
        mock_instances.stop.return_value = mock_stop
        operation_response = {"name": "operation-stop", "done": False}
        mock_stop.execute.return_value = operation_response

        service = BareMetalService(project_id="test-project")
        result = service.stop_instance("us-central1", "my-instance")

        mock_instances.stop.assert_called_once_with(
            name="projects/test-project/locations/us-central1/instances/my-instance"
        )
        assert result == operation_response


class TestBareMetalServiceVolumes:
    """Tests for volume-related methods."""

    def test_list_volumes(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_volumes = _setup_volume_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_volumes.list.return_value = mock_list
        mock_list.execute.return_value = {
            "volumes": [SAMPLE_VOLUME_RESPONSE],
        }

        service = BareMetalService(project_id="test-project")
        results = service.list_volumes("us-central1")

        mock_volumes.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )
        assert len(results) == 1
        assert isinstance(results[0], BareMetalVolume)
        assert results[0].state == "READY"

    def test_list_volumes_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_volumes = _setup_volume_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_volumes.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = BareMetalService(project_id="test-project")
        results = service.list_volumes("us-central1")

        assert results == []

    def test_get_volume(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_volumes = _setup_volume_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_volumes.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_VOLUME_RESPONSE

        service = BareMetalService(project_id="test-project")
        result = service.get_volume("us-central1", "my-volume")

        mock_volumes.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/volumes/my-volume"
        )
        assert isinstance(result, BareMetalVolume)
        assert result.storage_type == "SSD"
        assert result.size_gib == 500

    def test_update_volume(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_volumes = _setup_volume_mock(mock_service)
        mock_patch = mock.MagicMock()
        mock_volumes.patch.return_value = mock_patch
        operation_response = {"name": "operation-vol-1", "done": False}
        mock_patch.execute.return_value = operation_response

        service = BareMetalService(project_id="test-project")
        result = service.update_volume(
            location="us-central1",
            volume_name="my-volume",
            update_mask="snapshotAutoDeleteBehavior",
            update_fields={
                "snapshotAutoDeleteBehavior": "NEWEST_FIRST",
            },
        )

        mock_volumes.patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/volumes/my-volume",
            updateMask="snapshotAutoDeleteBehavior",
            body={"snapshotAutoDeleteBehavior": "NEWEST_FIRST"},
        )
        assert result == operation_response
