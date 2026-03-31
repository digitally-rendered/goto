"""Tests for Cloud Filestore service."""

from unittest import mock

import pytest

from gcpoto.services.filestore import FilestoreService
from gcpoto.models.filestore import FilestoreInstance


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().locations().instances() chain
        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.instances.return_value = (
            mock_instances
        )

        # Set up snapshots chain
        mock_snapshots = mock.MagicMock()
        mock_instances.snapshots.return_value = mock_snapshots

        yield mock_service


@pytest.fixture
def sample_instance_response():
    """Sample Filestore instance API response."""
    return {
        "name": "projects/test-project/locations/us-east1/instances/test-instance",
        "description": "A test Filestore instance",
        "tier": "BASIC_SSD",
        "state": "READY",
        "statusMessage": "Instance is ready",
        "fileShares": [
            {"name": "share1", "capacityGb": "1024"},
        ],
        "networks": [
            {
                "network": "default",
                "modes": ["MODE_IPV4"],
                "reservedIpRange": "10.0.0.0/29",
                "ipAddresses": ["10.0.0.2"],
            },
        ],
        "labels": {"env": "test", "team": "platform"},
        "createTime": "2025-06-15T10:00:00Z",
        "updateTime": "2025-06-15T12:00:00Z",
    }


@pytest.fixture
def sample_snapshot_response():
    """Sample Filestore snapshot API response."""
    return {
        "name": "projects/test-project/locations/us-east1/instances/test-instance/snapshots/snap-1",
        "description": "A test snapshot",
        "state": "READY",
        "createTime": "2025-06-16T10:00:00Z",
    }


class TestFilestoreServiceInit:
    """Tests for FilestoreService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the FilestoreService."""
        from googleapiclient.discovery import build

        service = FilestoreService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "file"
        assert service.version == "v1"
        build.assert_called_once_with("file", "v1", credentials=None)


class TestFilestoreInstanceModel:
    """Tests for FilestoreInstance model."""

    def test_from_api_response(self, sample_instance_response):
        """Test creating a FilestoreInstance from an API response."""
        instance = FilestoreInstance.from_api_response(
            sample_instance_response
        )

        assert instance.name == "test-instance"
        assert instance.project == "test-project"
        assert instance.location == "us-east1"
        assert instance.type == "filestore.instance"
        assert instance.tier == "BASIC_SSD"
        assert instance.state == "READY"
        assert instance.description == "A test Filestore instance"
        assert instance.status_message == "Instance is ready"
        assert len(instance.file_shares) == 1
        assert instance.file_shares[0]["name"] == "share1"
        assert len(instance.networks) == 1
        assert instance.networks[0]["network"] == "default"
        assert instance.labels == {"env": "test", "team": "platform"}
        assert (
            instance.id
            == "projects/test-project/locations/us-east1/instances/test-instance"
        )

    def test_from_api_response_with_project_id(
        self, sample_instance_response
    ):
        """Test creating a FilestoreInstance with an explicit project ID."""
        instance = FilestoreInstance.from_api_response(
            sample_instance_response, project_id="override-project"
        )
        assert instance.project == "override-project"

    def test_from_api_response_minimal(self):
        """Test creating a FilestoreInstance with minimal data."""
        response = {
            "name": "projects/p/locations/l/instances/i",
            "tier": "BASIC_HDD",
            "state": "CREATING",
        }
        instance = FilestoreInstance.from_api_response(response)

        assert instance.name == "i"
        assert instance.tier == "BASIC_HDD"
        assert instance.state == "CREATING"
        assert instance.description is None
        assert instance.status_message is None
        assert instance.file_shares == []
        assert instance.networks == []

    def test_get_tag(self, sample_instance_response):
        """Test get_tag method on FilestoreInstance."""
        instance = FilestoreInstance.from_api_response(
            sample_instance_response
        )

        assert instance.get_tag("env") == "test"
        assert instance.get_tag("team") == "platform"
        assert instance.get_tag("nonexistent") == ""
        assert instance.get_tag("nonexistent", "default") == "default"

    def test_get_tag_no_labels(self):
        """Test get_tag when no labels are present."""
        response = {
            "name": "projects/p/locations/l/instances/i",
            "tier": "BASIC_HDD",
            "state": "READY",
        }
        instance = FilestoreInstance.from_api_response(response)
        assert instance.get_tag("any_key") == ""
        assert instance.get_tag("any_key", "fallback") == "fallback"


class TestListInstances:
    """Tests for listing Filestore instances."""

    def test_list_instances(
        self, mock_google_client, sample_instance_response
    ):
        """Test listing Filestore instances in a location."""
        mock_instances = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
        )
        mock_request = mock.MagicMock()
        mock_instances.list.return_value = mock_request
        mock_request.execute.return_value = {
            "instances": [
                sample_instance_response,
                sample_instance_response,
            ]
        }
        mock_instances.list_next.return_value = None

        service = FilestoreService(project_id="test-project")
        instances = service.list_instances("us-east1")

        mock_instances.list.assert_called_once_with(
            parent="projects/test-project/locations/us-east1"
        )
        assert len(instances) == 2
        assert isinstance(instances[0], FilestoreInstance)
        assert instances[0].name == "test-instance"

    def test_list_instances_all_locations(
        self, mock_google_client, sample_instance_response
    ):
        """Test listing instances across all locations."""
        mock_instances = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
        )
        mock_request = mock.MagicMock()
        mock_instances.list.return_value = mock_request
        mock_request.execute.return_value = {
            "instances": [sample_instance_response]
        }
        mock_instances.list_next.return_value = None

        service = FilestoreService(project_id="test-project")
        instances = service.list_instances()

        mock_instances.list.assert_called_once_with(
            parent="projects/test-project/locations/-"
        )
        assert len(instances) == 1

    def test_list_instances_empty(self, mock_google_client):
        """Test listing instances with no results."""
        mock_instances = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
        )
        mock_request = mock.MagicMock()
        mock_instances.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_instances.list_next.return_value = None

        service = FilestoreService(project_id="test-project")
        instances = service.list_instances("us-east1")

        assert instances == []

    def test_list_instances_pagination(
        self, mock_google_client, sample_instance_response
    ):
        """Test listing instances with pagination."""
        mock_instances = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
        )

        # First page
        mock_request_1 = mock.MagicMock()
        mock_instances.list.return_value = mock_request_1
        mock_request_1.execute.return_value = {
            "instances": [sample_instance_response]
        }

        # Second page
        mock_request_2 = mock.MagicMock()
        mock_request_2.execute.return_value = {
            "instances": [sample_instance_response]
        }
        mock_instances.list_next.side_effect = [mock_request_2, None]

        service = FilestoreService(project_id="test-project")
        instances = service.list_instances("us-east1")

        assert len(instances) == 2


class TestGetInstance:
    """Tests for getting a Filestore instance."""

    def test_get_instance(
        self, mock_google_client, sample_instance_response
    ):
        """Test getting a specific Filestore instance."""
        mock_instances = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
        )
        mock_request = mock.MagicMock()
        mock_instances.get.return_value = mock_request
        mock_request.execute.return_value = sample_instance_response

        service = FilestoreService(project_id="test-project")
        instance = service.get_instance("us-east1", "test-instance")

        mock_instances.get.assert_called_once_with(
            name="projects/test-project/locations/us-east1/instances/test-instance"
        )
        assert isinstance(instance, FilestoreInstance)
        assert instance.name == "test-instance"
        assert instance.tier == "BASIC_SSD"
        assert instance.location == "us-east1"


class TestCreateInstance:
    """Tests for creating a Filestore instance."""

    def test_create_instance_basic(self, mock_google_client):
        """Test creating a Filestore instance with required fields."""
        mock_instances = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
        )
        mock_request = mock.MagicMock()
        mock_instances.create.return_value = mock_request
        mock_request.execute.return_value = {"name": "operations/op-1"}

        service = FilestoreService(project_id="test-project")
        file_shares = [{"name": "share1", "capacityGb": "1024"}]
        networks = [{"network": "default", "modes": ["MODE_IPV4"]}]
        result = service.create_instance(
            "us-east1", "new-instance", "BASIC_SSD", file_shares, networks
        )

        mock_instances.create.assert_called_once_with(
            parent="projects/test-project/locations/us-east1",
            instanceId="new-instance",
            body={
                "tier": "BASIC_SSD",
                "fileShares": file_shares,
                "networks": networks,
            },
        )
        assert result == {"name": "operations/op-1"}

    def test_create_instance_full(self, mock_google_client):
        """Test creating a Filestore instance with all options."""
        mock_instances = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
        )
        mock_request = mock.MagicMock()
        mock_instances.create.return_value = mock_request
        mock_request.execute.return_value = {"name": "operations/op-1"}

        service = FilestoreService(project_id="test-project")
        file_shares = [{"name": "share1", "capacityGb": "2048"}]
        networks = [
            {
                "network": "my-vpc",
                "modes": ["MODE_IPV4"],
                "reservedIpRange": "10.0.0.0/29",
            }
        ]
        result = service.create_instance(
            location="us-east1",
            instance_id="new-instance",
            tier="ENTERPRISE",
            file_shares=file_shares,
            networks=networks,
            description="My enterprise instance",
            labels={"env": "prod"},
        )

        mock_instances.create.assert_called_once_with(
            parent="projects/test-project/locations/us-east1",
            instanceId="new-instance",
            body={
                "tier": "ENTERPRISE",
                "fileShares": file_shares,
                "networks": networks,
                "description": "My enterprise instance",
                "labels": {"env": "prod"},
            },
        )
        assert result == {"name": "operations/op-1"}


class TestUpdateInstance:
    """Tests for updating a Filestore instance."""

    def test_update_instance(self, mock_google_client):
        """Test updating a Filestore instance."""
        mock_instances = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
        )
        mock_request = mock.MagicMock()
        mock_instances.patch.return_value = mock_request
        mock_request.execute.return_value = {"name": "operations/op-2"}

        service = FilestoreService(project_id="test-project")
        result = service.update_instance(
            "us-east1",
            "test-instance",
            "description,labels",
            {"description": "Updated", "labels": {"env": "staging"}},
        )

        mock_instances.patch.assert_called_once_with(
            name="projects/test-project/locations/us-east1/instances/test-instance",
            updateMask="description,labels",
            body={"description": "Updated", "labels": {"env": "staging"}},
        )
        assert result == {"name": "operations/op-2"}


class TestDeleteInstance:
    """Tests for deleting a Filestore instance."""

    def test_delete_instance(self, mock_google_client):
        """Test deleting a Filestore instance."""
        mock_instances = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
        )
        mock_request = mock.MagicMock()
        mock_instances.delete.return_value = mock_request
        mock_request.execute.return_value = {"name": "operations/op-3"}

        service = FilestoreService(project_id="test-project")
        result = service.delete_instance("us-east1", "test-instance")

        mock_instances.delete.assert_called_once_with(
            name="projects/test-project/locations/us-east1/instances/test-instance"
        )
        assert result == {"name": "operations/op-3"}


class TestListSnapshots:
    """Tests for listing Filestore snapshots."""

    def test_list_snapshots(
        self, mock_google_client, sample_snapshot_response
    ):
        """Test listing snapshots for an instance."""
        mock_snapshots = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
            .snapshots.return_value
        )
        mock_request = mock.MagicMock()
        mock_snapshots.list.return_value = mock_request
        mock_request.execute.return_value = {
            "snapshots": [sample_snapshot_response, sample_snapshot_response]
        }
        mock_snapshots.list_next.return_value = None

        service = FilestoreService(project_id="test-project")
        snapshots = service.list_snapshots("us-east1", "test-instance")

        mock_snapshots.list.assert_called_once_with(
            parent="projects/test-project/locations/us-east1/instances/test-instance"
        )
        assert len(snapshots) == 2
        assert snapshots[0]["state"] == "READY"

    def test_list_snapshots_empty(self, mock_google_client):
        """Test listing snapshots with no results."""
        mock_snapshots = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
            .snapshots.return_value
        )
        mock_request = mock.MagicMock()
        mock_snapshots.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_snapshots.list_next.return_value = None

        service = FilestoreService(project_id="test-project")
        snapshots = service.list_snapshots("us-east1", "test-instance")

        assert snapshots == []


class TestCreateSnapshot:
    """Tests for creating a Filestore snapshot."""

    def test_create_snapshot(self, mock_google_client):
        """Test creating a snapshot."""
        mock_snapshots = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
            .snapshots.return_value
        )
        mock_request = mock.MagicMock()
        mock_snapshots.create.return_value = mock_request
        mock_request.execute.return_value = {"name": "operations/op-4"}

        service = FilestoreService(project_id="test-project")
        result = service.create_snapshot(
            "us-east1", "test-instance", "snap-1"
        )

        mock_snapshots.create.assert_called_once_with(
            parent="projects/test-project/locations/us-east1/instances/test-instance",
            snapshotId="snap-1",
            body={},
        )
        assert result == {"name": "operations/op-4"}

    def test_create_snapshot_with_description(self, mock_google_client):
        """Test creating a snapshot with a description."""
        mock_snapshots = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
            .snapshots.return_value
        )
        mock_request = mock.MagicMock()
        mock_snapshots.create.return_value = mock_request
        mock_request.execute.return_value = {"name": "operations/op-5"}

        service = FilestoreService(project_id="test-project")
        result = service.create_snapshot(
            "us-east1",
            "test-instance",
            "snap-2",
            description="Daily backup",
        )

        mock_snapshots.create.assert_called_once_with(
            parent="projects/test-project/locations/us-east1/instances/test-instance",
            snapshotId="snap-2",
            body={"description": "Daily backup"},
        )
        assert result == {"name": "operations/op-5"}


class TestDeleteSnapshot:
    """Tests for deleting a Filestore snapshot."""

    def test_delete_snapshot(self, mock_google_client):
        """Test deleting a snapshot."""
        mock_snapshots = (
            mock_google_client.projects.return_value
            .locations.return_value
            .instances.return_value
            .snapshots.return_value
        )
        mock_request = mock.MagicMock()
        mock_snapshots.delete.return_value = mock_request
        mock_request.execute.return_value = {"name": "operations/op-6"}

        service = FilestoreService(project_id="test-project")
        result = service.delete_snapshot(
            "us-east1", "test-instance", "snap-1"
        )

        mock_snapshots.delete.assert_called_once_with(
            name="projects/test-project/locations/us-east1/instances/test-instance/snapshots/snap-1"
        )
        assert result == {"name": "operations/op-6"}
