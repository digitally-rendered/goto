"""Tests for the VMware Engine service implementation."""

import unittest.mock as mock
import pytest

from gcpoto.services.vmware_engine import VMwareEngineService
from gcpoto.models.vmware_engine import PrivateCloud, Cluster


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


SAMPLE_PRIVATE_CLOUD_RESPONSE = {
    "uid": "pc-abc123",
    "name": "projects/test-project/locations/us-west1-a/privateClouds/my-cloud",
    "projectId": "test-project",
    "location": "us-west1-a",
    "description": "A test private cloud",
    "state": "ACTIVE",
    "networkConfig": {
        "managementCidr": "192.168.0.0/24",
        "vmwareEngineNetwork": "projects/test-project/locations/us-west1/vmwareEngineNetworks/my-network",
    },
    "managementCluster": {
        "clusterId": "mgmt-cluster",
        "nodeTypeConfigs": {
            "standard-72": {"nodeCount": 3},
        },
    },
    "hcx": {"internalIp": "10.0.0.1", "version": "4.5.0"},
    "nsx": {"internalIp": "10.0.0.2", "version": "3.2.1"},
    "vcenter": {"internalIp": "10.0.0.3", "version": "7.0.3"},
    "labels": {"env": "test", "team": "infra"},
    "createTime": "2025-06-01T00:00:00Z",
    "updateTime": "2025-06-02T00:00:00Z",
}

SAMPLE_CLUSTER_RESPONSE = {
    "uid": "cl-abc123",
    "name": "projects/test-project/locations/us-west1-a/privateClouds/my-cloud/clusters/my-cluster",
    "projectId": "test-project",
    "privateCloudName": "my-cloud",
    "location": "us-west1-a",
    "nodeTypeConfigs": {
        "standard-72": {"nodeCount": 3},
    },
    "state": "ACTIVE",
    "labels": {"tier": "compute"},
    "createTime": "2025-06-01T00:00:00Z",
    "updateTime": "2025-06-02T00:00:00Z",
}


class TestVMwareEngineServiceInit:
    """Tests for VMwareEngineService initialization."""

    def test_initialization(self, mock_discovery):
        mock_build, _ = mock_discovery
        service = VMwareEngineService(
            project_id="test-project", credentials_file=None
        )

        assert service.project_id == "test-project"
        assert service.service_name == "vmwareengine"
        assert service.version == "v1"
        assert service.credentials_file is None
        assert service.resource_model == PrivateCloud
        mock_build.assert_called_once_with(
            "vmwareengine", "v1", credentials=None
        )


class TestPrivateCloudModel:
    """Tests for the PrivateCloud model."""

    def test_from_api_response(self):
        cloud = PrivateCloud.from_api_response(SAMPLE_PRIVATE_CLOUD_RESPONSE)

        assert cloud.id == "pc-abc123"
        assert cloud.name == "projects/test-project/locations/us-west1-a/privateClouds/my-cloud"
        assert cloud.type == "vmwareengine.privateCloud"
        assert cloud.project == "test-project"
        assert cloud.location == "us-west1-a"
        assert cloud.description == "A test private cloud"
        assert cloud.state == "ACTIVE"
        assert cloud.network_config["managementCidr"] == "192.168.0.0/24"
        assert cloud.management_cluster is not None
        assert cloud.hcx["version"] == "4.5.0"
        assert cloud.nsx["version"] == "3.2.1"
        assert cloud.vcenter["version"] == "7.0.3"
        assert cloud.labels == {"env": "test", "team": "infra"}
        assert cloud.created.isoformat().startswith("2025-06-01T00:00:00")
        assert cloud.updated.isoformat().startswith("2025-06-02T00:00:00")

    def test_from_api_response_minimal(self):
        response = {"name": "bare-cloud", "projectId": "p"}
        cloud = PrivateCloud.from_api_response(response)

        assert cloud.name == "bare-cloud"
        assert cloud.id == ""
        assert cloud.location == ""
        assert cloud.description is None
        assert cloud.state == ""
        assert cloud.network_config is None
        assert cloud.management_cluster is None
        assert cloud.hcx is None
        assert cloud.nsx is None
        assert cloud.vcenter is None

    def test_get_tag(self):
        cloud = PrivateCloud.from_api_response(SAMPLE_PRIVATE_CLOUD_RESPONSE)
        assert cloud.get_tag("env") == "test"
        assert cloud.get_tag("team") == "infra"
        assert cloud.get_tag("missing") == ""
        assert cloud.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        response = {"name": "bare", "projectId": "p"}
        cloud = PrivateCloud.from_api_response(response)
        assert cloud.get_tag("env") == ""
        assert cloud.get_tag("env", "fallback") == "fallback"


class TestClusterModel:
    """Tests for the Cluster model."""

    def test_from_api_response(self):
        cluster = Cluster.from_api_response(SAMPLE_CLUSTER_RESPONSE)

        assert cluster.id == "cl-abc123"
        assert cluster.name == "projects/test-project/locations/us-west1-a/privateClouds/my-cloud/clusters/my-cluster"
        assert cluster.type == "vmwareengine.cluster"
        assert cluster.project == "test-project"
        assert cluster.private_cloud_name == "my-cloud"
        assert cluster.location == "us-west1-a"
        assert cluster.node_type_configs["standard-72"]["nodeCount"] == 3
        assert cluster.state == "ACTIVE"

    def test_from_api_response_minimal(self):
        response = {"name": "bare-cluster", "projectId": "p"}
        cluster = Cluster.from_api_response(response)

        assert cluster.name == "bare-cluster"
        assert cluster.private_cloud_name == ""
        assert cluster.location == ""
        assert cluster.node_type_configs is None
        assert cluster.state == ""

    def test_get_tag(self):
        cluster = Cluster.from_api_response(SAMPLE_CLUSTER_RESPONSE)
        assert cluster.get_tag("tier") == "compute"
        assert cluster.get_tag("missing") == ""
        assert cluster.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        response = {"name": "bare", "projectId": "p"}
        cluster = Cluster.from_api_response(response)
        assert cluster.get_tag("key") == ""
        assert cluster.get_tag("key", "fallback") == "fallback"


def _setup_private_cloud_mock(mock_service):
    """Helper to set up the nested mock chain for private cloud operations."""
    mock_projects = mock.MagicMock()
    mock_service.projects.return_value = mock_projects
    mock_locations = mock.MagicMock()
    mock_projects.locations.return_value = mock_locations
    mock_private_clouds = mock.MagicMock()
    mock_locations.privateClouds.return_value = mock_private_clouds
    return mock_private_clouds


def _setup_cluster_mock(mock_service):
    """Helper to set up the nested mock chain for cluster operations."""
    mock_private_clouds = _setup_private_cloud_mock(mock_service)
    mock_clusters = mock.MagicMock()
    mock_private_clouds.clusters.return_value = mock_clusters
    return mock_private_clouds, mock_clusters


class TestVMwareEngineServicePrivateClouds:
    """Tests for private cloud-related methods."""

    def test_list_private_clouds(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_private_clouds = _setup_private_cloud_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_private_clouds.list.return_value = mock_list
        mock_list.execute.return_value = {
            "privateClouds": [SAMPLE_PRIVATE_CLOUD_RESPONSE],
        }

        service = VMwareEngineService(project_id="test-project")
        results = service.list_private_clouds("us-west1-a")

        mock_private_clouds.list.assert_called_once_with(
            parent="projects/test-project/locations/us-west1-a"
        )
        assert len(results) == 1
        assert isinstance(results[0], PrivateCloud)
        assert results[0].state == "ACTIVE"

    def test_list_private_clouds_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_private_clouds = _setup_private_cloud_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_private_clouds.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = VMwareEngineService(project_id="test-project")
        results = service.list_private_clouds("us-west1-a")

        assert results == []

    def test_get_private_cloud(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_private_clouds = _setup_private_cloud_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_private_clouds.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_PRIVATE_CLOUD_RESPONSE

        service = VMwareEngineService(project_id="test-project")
        result = service.get_private_cloud("us-west1-a", "my-cloud")

        mock_private_clouds.get.assert_called_once_with(
            name="projects/test-project/locations/us-west1-a/privateClouds/my-cloud"
        )
        assert isinstance(result, PrivateCloud)
        assert result.state == "ACTIVE"

    def test_create_private_cloud(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_private_clouds = _setup_private_cloud_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_private_clouds.create.return_value = mock_create
        operation_response = {"name": "operation-123", "done": False}
        mock_create.execute.return_value = operation_response

        service = VMwareEngineService(project_id="test-project")
        result = service.create_private_cloud(
            location="us-west1-a",
            cloud_name="new-cloud",
            network_config={"managementCidr": "192.168.0.0/24"},
            management_cluster={
                "clusterId": "mgmt",
                "nodeTypeConfigs": {"standard-72": {"nodeCount": 3}},
            },
            labels={"env": "prod"},
        )

        mock_private_clouds.create.assert_called_once_with(
            parent="projects/test-project/locations/us-west1-a",
            privateCloudId="new-cloud",
            body={
                "networkConfig": {"managementCidr": "192.168.0.0/24"},
                "managementCluster": {
                    "clusterId": "mgmt",
                    "nodeTypeConfigs": {"standard-72": {"nodeCount": 3}},
                },
                "labels": {"env": "prod"},
            },
        )
        assert result == operation_response

    def test_create_private_cloud_no_labels(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_private_clouds = _setup_private_cloud_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_private_clouds.create.return_value = mock_create
        mock_create.execute.return_value = {"name": "op-1"}

        service = VMwareEngineService(project_id="test-project")
        service.create_private_cloud(
            location="us-west1-a",
            cloud_name="new-cloud",
            network_config={"managementCidr": "192.168.0.0/24"},
            management_cluster={"clusterId": "mgmt"},
        )

        call_args = mock_private_clouds.create.call_args
        body = call_args[1]["body"]
        assert "labels" not in body

    def test_delete_private_cloud(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_private_clouds = _setup_private_cloud_mock(mock_service)
        mock_delete = mock.MagicMock()
        mock_private_clouds.delete.return_value = mock_delete
        operation_response = {"name": "operation-456", "done": False}
        mock_delete.execute.return_value = operation_response

        service = VMwareEngineService(project_id="test-project")
        result = service.delete_private_cloud("us-west1-a", "my-cloud")

        mock_private_clouds.delete.assert_called_once_with(
            name="projects/test-project/locations/us-west1-a/privateClouds/my-cloud"
        )
        assert result == operation_response


class TestVMwareEngineServiceClusters:
    """Tests for cluster-related methods."""

    def test_list_clusters(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_clusters = _setup_cluster_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {
            "clusters": [SAMPLE_CLUSTER_RESPONSE],
        }

        service = VMwareEngineService(project_id="test-project")
        results = service.list_clusters("us-west1-a", "my-cloud")

        mock_clusters.list.assert_called_once_with(
            parent="projects/test-project/locations/us-west1-a/privateClouds/my-cloud"
        )
        assert len(results) == 1
        assert isinstance(results[0], Cluster)
        assert results[0].state == "ACTIVE"

    def test_list_clusters_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_clusters = _setup_cluster_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = VMwareEngineService(project_id="test-project")
        results = service.list_clusters("us-west1-a", "my-cloud")

        assert results == []

    def test_get_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_clusters = _setup_cluster_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_clusters.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = VMwareEngineService(project_id="test-project")
        result = service.get_cluster("us-west1-a", "my-cloud", "my-cluster")

        mock_clusters.get.assert_called_once_with(
            name="projects/test-project/locations/us-west1-a/privateClouds/my-cloud/clusters/my-cluster"
        )
        assert isinstance(result, Cluster)
        assert result.state == "ACTIVE"

    def test_create_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_clusters = _setup_cluster_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_clusters.create.return_value = mock_create
        operation_response = {"name": "operation-cl-1", "done": False}
        mock_create.execute.return_value = operation_response

        service = VMwareEngineService(project_id="test-project")
        result = service.create_cluster(
            location="us-west1-a",
            cloud_name="my-cloud",
            cluster_name="new-cluster",
            node_type_configs={"standard-72": {"nodeCount": 3}},
        )

        mock_clusters.create.assert_called_once_with(
            parent="projects/test-project/locations/us-west1-a/privateClouds/my-cloud",
            clusterId="new-cluster",
            body={
                "nodeTypeConfigs": {"standard-72": {"nodeCount": 3}},
            },
        )
        assert result == operation_response

    def test_delete_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_clusters = _setup_cluster_mock(mock_service)
        mock_delete = mock.MagicMock()
        mock_clusters.delete.return_value = mock_delete
        operation_response = {"name": "operation-cl-del", "done": False}
        mock_delete.execute.return_value = operation_response

        service = VMwareEngineService(project_id="test-project")
        result = service.delete_cluster(
            "us-west1-a", "my-cloud", "my-cluster"
        )

        mock_clusters.delete.assert_called_once_with(
            name="projects/test-project/locations/us-west1-a/privateClouds/my-cloud/clusters/my-cluster"
        )
        assert result == operation_response
