"""Tests for the AlloyDB service implementation."""

import unittest.mock as mock
import pytest

from gcpoto.services.alloydb import AlloyDBService
from gcpoto.models.alloydb import AlloyDBCluster, AlloyDBInstance


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


SAMPLE_CLUSTER_RESPONSE = {
    "name": "projects/test-project/locations/us-central1/clusters/my-cluster",
    "network": "projects/test-project/global/networks/default",
    "state": "READY",
    "databaseVersion": "POSTGRES_14",
    "automatedBackupPolicy": {"enabled": True},
    "continuousBackupConfig": {"enabled": True},
    "labels": {"env": "test", "team": "backend"},
    "createTime": "2025-01-01T00:00:00Z",
    "updateTime": "2025-01-02T00:00:00Z",
}

SAMPLE_CLUSTER_RESPONSE_MINIMAL = {
    "name": "projects/test-project/locations/us-central1/clusters/bare-cluster",
}

SAMPLE_INSTANCE_RESPONSE = {
    "name": "projects/test-project/locations/us-central1/clusters/my-cluster/instances/my-instance",
    "instanceType": "PRIMARY",
    "state": "READY",
    "machineConfig": {"cpuCount": 4},
    "availabilityType": "REGIONAL",
    "createTime": "2025-01-01T00:00:00Z",
    "updateTime": "2025-01-02T00:00:00Z",
}

SAMPLE_INSTANCE_RESPONSE_MINIMAL = {
    "name": "projects/test-project/locations/us-central1/clusters/my-cluster/instances/bare-instance",
}


class TestAlloyDBServiceInit:
    """Tests for AlloyDBService initialization."""

    def test_initialization(self, mock_discovery):
        mock_build, _ = mock_discovery
        service = AlloyDBService(
            project_id="test-project", credentials_file=None
        )

        assert service.project_id == "test-project"
        assert service.service_name == "alloydb"
        assert service.version == "v1"
        assert service.credentials_file is None
        assert service.resource_model == AlloyDBCluster
        mock_build.assert_called_once_with(
            "alloydb", "v1", credentials=None
        )


class TestAlloyDBClusterModel:
    """Tests for the AlloyDBCluster model."""

    def test_from_api_response(self):
        cluster = AlloyDBCluster.from_api_response(SAMPLE_CLUSTER_RESPONSE)

        assert cluster.id == "my-cluster"
        assert cluster.name == "my-cluster"
        assert cluster.type == "alloydb.cluster"
        assert cluster.project == "test-project"
        assert cluster.location == "us-central1"
        assert cluster.network == "projects/test-project/global/networks/default"
        assert cluster.state == "READY"
        assert cluster.database_version == "POSTGRES_14"
        assert cluster.automated_backup_policy == {"enabled": True}
        assert cluster.continuous_backup_config == {"enabled": True}
        assert cluster.labels == {"env": "test", "team": "backend"}
        assert cluster.created.isoformat().startswith("2025-01-01T00:00:00")
        assert cluster.updated.isoformat().startswith("2025-01-02T00:00:00")

    def test_from_api_response_minimal(self):
        cluster = AlloyDBCluster.from_api_response(
            SAMPLE_CLUSTER_RESPONSE_MINIMAL
        )

        assert cluster.name == "bare-cluster"
        assert cluster.location == "us-central1"
        assert cluster.network == ""
        assert cluster.state == ""
        assert cluster.database_version is None
        assert cluster.automated_backup_policy is None
        assert cluster.continuous_backup_config is None
        assert cluster.created is None
        assert cluster.updated is None

    def test_get_tag(self):
        cluster = AlloyDBCluster.from_api_response(SAMPLE_CLUSTER_RESPONSE)
        assert cluster.get_tag("env") == "test"
        assert cluster.get_tag("team") == "backend"
        assert cluster.get_tag("missing") == ""
        assert cluster.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        cluster = AlloyDBCluster.from_api_response(
            SAMPLE_CLUSTER_RESPONSE_MINIMAL
        )
        assert cluster.get_tag("env") == ""
        assert cluster.get_tag("env", "fallback") == "fallback"


class TestAlloyDBInstanceModel:
    """Tests for the AlloyDBInstance model."""

    def test_from_api_response(self):
        instance = AlloyDBInstance.from_api_response(
            SAMPLE_INSTANCE_RESPONSE
        )

        assert instance.id == "my-instance"
        assert instance.name == "my-instance"
        assert instance.type == "alloydb.instance"
        assert instance.project == "test-project"
        assert instance.cluster_name == "my-cluster"
        assert instance.location == "us-central1"
        assert instance.instance_type == "PRIMARY"
        assert instance.state == "READY"
        assert instance.machine_config == {"cpuCount": 4}
        assert instance.availability_type == "REGIONAL"
        assert instance.created.isoformat().startswith("2025-01-01T00:00:00")
        assert instance.updated.isoformat().startswith("2025-01-02T00:00:00")

    def test_from_api_response_minimal(self):
        instance = AlloyDBInstance.from_api_response(
            SAMPLE_INSTANCE_RESPONSE_MINIMAL
        )

        assert instance.name == "bare-instance"
        assert instance.cluster_name == "my-cluster"
        assert instance.location == "us-central1"
        assert instance.instance_type == ""
        assert instance.state == ""
        assert instance.machine_config is None
        assert instance.availability_type is None
        assert instance.created is None
        assert instance.updated is None


class TestAlloyDBServiceClusters:
    """Tests for cluster-related methods."""

    def test_list_clusters(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {
            "clusters": [SAMPLE_CLUSTER_RESPONSE],
        }
        mock_clusters.list_next.return_value = None

        service = AlloyDBService(project_id="test-project")
        results = service.list_clusters("us-central1")

        mock_clusters.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )
        assert len(results) == 1
        assert isinstance(results[0], AlloyDBCluster)
        assert results[0].name == "my-cluster"

    def test_list_clusters_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {}
        mock_clusters.list_next.return_value = None

        service = AlloyDBService(project_id="test-project")
        results = service.list_clusters("us-central1")

        assert results == []

    def test_list_clusters_pagination(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list

        page1_response = {
            "clusters": [SAMPLE_CLUSTER_RESPONSE],
        }
        second_cluster = {
            "name": "projects/test-project/locations/us-central1/clusters/second-cluster",
            "state": "READY",
        }
        page2_response = {
            "clusters": [second_cluster],
        }

        mock_list.execute.return_value = page1_response

        mock_list_page2 = mock.MagicMock()
        mock_list_page2.execute.return_value = page2_response
        mock_clusters.list_next.side_effect = [mock_list_page2, None]

        service = AlloyDBService(project_id="test-project")
        results = service.list_clusters("us-central1")

        assert len(results) == 2
        assert results[0].name == "my-cluster"
        assert results[1].name == "second-cluster"

    def test_get_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_get = mock.MagicMock()
        mock_clusters.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = AlloyDBService(project_id="test-project")
        result = service.get_cluster("us-central1", "my-cluster")

        mock_clusters.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/clusters/my-cluster"
        )
        assert isinstance(result, AlloyDBCluster)
        assert result.name == "my-cluster"
        assert result.state == "READY"

    def test_create_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_create = mock.MagicMock()
        mock_clusters.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = AlloyDBService(project_id="test-project")
        result = service.create_cluster(
            location="us-central1",
            cluster_id="my-cluster",
            network="projects/test-project/global/networks/default",
            database_version="POSTGRES_14",
            labels={"env": "test"},
        )

        mock_clusters.create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1",
            clusterId="my-cluster",
            body={
                "network": "projects/test-project/global/networks/default",
                "databaseVersion": "POSTGRES_14",
                "labels": {"env": "test"},
            },
        )
        assert isinstance(result, AlloyDBCluster)
        assert result.name == "my-cluster"

    def test_create_cluster_minimal(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_create = mock.MagicMock()
        mock_clusters.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = AlloyDBService(project_id="test-project")
        service.create_cluster(
            location="us-central1",
            cluster_id="my-cluster",
            network="projects/test-project/global/networks/default",
        )

        call_args = mock_clusters.create.call_args
        body = call_args[1]["body"]
        assert "databaseVersion" not in body
        assert "labels" not in body
        assert "automatedBackupPolicy" not in body

    def test_create_cluster_with_backup_policy(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_create = mock.MagicMock()
        mock_clusters.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        backup_policy = {"enabled": True}
        service = AlloyDBService(project_id="test-project")
        service.create_cluster(
            location="us-central1",
            cluster_id="my-cluster",
            network="projects/test-project/global/networks/default",
            automated_backup_policy=backup_policy,
        )

        call_args = mock_clusters.create.call_args
        body = call_args[1]["body"]
        assert body["automatedBackupPolicy"] == backup_policy

    def test_update_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_patch = mock.MagicMock()
        mock_clusters.patch.return_value = mock_patch
        mock_patch.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = AlloyDBService(project_id="test-project")
        result = service.update_cluster(
            location="us-central1",
            cluster_id="my-cluster",
            update_mask="labels",
            update_fields={"labels": {"env": "prod"}},
        )

        mock_clusters.patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/clusters/my-cluster",
            updateMask="labels",
            body={"labels": {"env": "prod"}},
        )
        assert isinstance(result, AlloyDBCluster)

    def test_delete_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_delete = mock.MagicMock()
        mock_clusters.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = AlloyDBService(project_id="test-project")
        result = service.delete_cluster("us-central1", "my-cluster")

        mock_clusters.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/clusters/my-cluster"
        )
        mock_delete.execute.assert_called_once()
        assert result is True


class TestAlloyDBServiceInstances:
    """Tests for instance-related methods."""

    def test_list_instances(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_instances = mock.MagicMock()
        mock_clusters.instances.return_value = mock_instances
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {
            "instances": [SAMPLE_INSTANCE_RESPONSE],
        }
        mock_instances.list_next.return_value = None

        service = AlloyDBService(project_id="test-project")
        results = service.list_instances("us-central1", "my-cluster")

        mock_instances.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1/clusters/my-cluster"
        )
        assert len(results) == 1
        assert isinstance(results[0], AlloyDBInstance)
        assert results[0].name == "my-instance"

    def test_list_instances_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_instances = mock.MagicMock()
        mock_clusters.instances.return_value = mock_instances
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {}
        mock_instances.list_next.return_value = None

        service = AlloyDBService(project_id="test-project")
        results = service.list_instances("us-central1", "my-cluster")

        assert results == []

    def test_get_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_instances = mock.MagicMock()
        mock_clusters.instances.return_value = mock_instances
        mock_get = mock.MagicMock()
        mock_instances.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = AlloyDBService(project_id="test-project")
        result = service.get_instance(
            "us-central1", "my-cluster", "my-instance"
        )

        mock_instances.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/clusters/my-cluster/instances/my-instance"
        )
        assert isinstance(result, AlloyDBInstance)
        assert result.name == "my-instance"
        assert result.instance_type == "PRIMARY"

    def test_create_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_instances = mock.MagicMock()
        mock_clusters.instances.return_value = mock_instances
        mock_create = mock.MagicMock()
        mock_instances.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = AlloyDBService(project_id="test-project")
        result = service.create_instance(
            location="us-central1",
            cluster_id="my-cluster",
            instance_id="my-instance",
            instance_type="PRIMARY",
            machine_config={"cpuCount": 4},
            availability_type="REGIONAL",
        )

        mock_instances.create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1/clusters/my-cluster",
            instanceId="my-instance",
            body={
                "instanceType": "PRIMARY",
                "machineConfig": {"cpuCount": 4},
                "availabilityType": "REGIONAL",
            },
        )
        assert isinstance(result, AlloyDBInstance)
        assert result.name == "my-instance"

    def test_create_instance_minimal(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_instances = mock.MagicMock()
        mock_clusters.instances.return_value = mock_instances
        mock_create = mock.MagicMock()
        mock_instances.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = AlloyDBService(project_id="test-project")
        service.create_instance(
            location="us-central1",
            cluster_id="my-cluster",
            instance_id="my-instance",
            instance_type="PRIMARY",
        )

        call_args = mock_instances.create.call_args
        body = call_args[1]["body"]
        assert "machineConfig" not in body
        assert "availabilityType" not in body

    def test_update_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_instances = mock.MagicMock()
        mock_clusters.instances.return_value = mock_instances
        mock_patch = mock.MagicMock()
        mock_instances.patch.return_value = mock_patch
        mock_patch.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = AlloyDBService(project_id="test-project")
        result = service.update_instance(
            location="us-central1",
            cluster_id="my-cluster",
            instance_id="my-instance",
            update_mask="machineConfig",
            update_fields={"machineConfig": {"cpuCount": 8}},
        )

        mock_instances.patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/clusters/my-cluster/instances/my-instance",
            updateMask="machineConfig",
            body={"machineConfig": {"cpuCount": 8}},
        )
        assert isinstance(result, AlloyDBInstance)

    def test_delete_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations
        mock_clusters = mock.MagicMock()
        mock_locations.clusters.return_value = mock_clusters
        mock_instances = mock.MagicMock()
        mock_clusters.instances.return_value = mock_instances
        mock_delete = mock.MagicMock()
        mock_instances.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = AlloyDBService(project_id="test-project")
        result = service.delete_instance(
            "us-central1", "my-cluster", "my-instance"
        )

        mock_instances.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/clusters/my-cluster/instances/my-instance"
        )
        mock_delete.execute.assert_called_once()
        assert result is True


class TestAlloyDBServicePathHelpers:
    """Tests for internal path formatting helpers."""

    def test_cluster_path(self, mock_discovery):
        _, _ = mock_discovery
        service = AlloyDBService(project_id="test-project")
        assert service._cluster_path("us-central1", "my-cluster") == (
            "projects/test-project/locations/us-central1/clusters/my-cluster"
        )

    def test_instance_path(self, mock_discovery):
        _, _ = mock_discovery
        service = AlloyDBService(project_id="test-project")
        assert service._instance_path(
            "us-central1", "my-cluster", "my-instance"
        ) == (
            "projects/test-project/locations/us-central1"
            "/clusters/my-cluster/instances/my-instance"
        )
