"""Tests for the GKE service implementation."""

import unittest.mock as mock
import pytest

from gcpoto.services.gke import GKEService
from gcpoto.models.gke import GKECluster, NodePool


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


SAMPLE_CLUSTER_RESPONSE = {
    "id": "abc123",
    "name": "my-cluster",
    "projectId": "test-project",
    "location": "us-central1-a",
    "description": "A test cluster",
    "initialNodeCount": 3,
    "nodeConfig": {
        "machineType": "e2-medium",
        "diskSizeGb": 100,
    },
    "masterAuth": {
        "clusterCaCertificate": "LS0tLS1CRUdJTi...",
    },
    "network": "default",
    "subnetwork": "default",
    "clusterIpv4Cidr": "10.4.0.0/14",
    "endpoint": "35.192.0.1",
    "status": "RUNNING",
    "currentMasterVersion": "1.28.3-gke.1286000",
    "currentNodeVersion": "1.28.3-gke.1286000",
    "nodePools": [
        {
            "name": "default-pool",
            "initialNodeCount": 3,
            "config": {"machineType": "e2-medium"},
            "status": "RUNNING",
        },
    ],
    "resourceLabels": {"env": "test", "team": "platform"},
    "createTime": "2025-01-01T00:00:00Z",
    "updateTime": "2025-01-02T00:00:00Z",
}

SAMPLE_NODE_POOL_RESPONSE = {
    "name": "custom-pool",
    "projectId": "test-project",
    "clusterName": "my-cluster",
    "location": "us-central1-a",
    "config": {
        "machineType": "e2-standard-4",
        "diskSizeGb": 200,
        "labels": {"pool-type": "compute"},
    },
    "initialNodeCount": 5,
    "autoscaling": {
        "enabled": True,
        "minNodeCount": 1,
        "maxNodeCount": 10,
    },
    "management": {
        "autoUpgrade": True,
        "autoRepair": True,
    },
    "status": "RUNNING",
    "version": "1.28.3-gke.1286000",
    "instanceGroupUrls": [
        "https://www.googleapis.com/compute/v1/projects/test-project/zones/us-central1-a/instanceGroupManagers/gke-my-cluster-custom-pool-abc123",
    ],
}


class TestGKEServiceInit:
    """Tests for GKEService initialization."""

    def test_initialization(self, mock_discovery):
        mock_build, _ = mock_discovery
        service = GKEService(
            project_id="test-project", credentials_file=None
        )

        assert service.project_id == "test-project"
        assert service.service_name == "container"
        assert service.version == "v1"
        assert service.credentials_file is None
        assert service.resource_model == GKECluster
        mock_build.assert_called_once_with("container", "v1", credentials=None)


class TestGKEClusterModel:
    """Tests for the GKECluster model."""

    def test_from_api_response(self):
        cluster = GKECluster.from_api_response(SAMPLE_CLUSTER_RESPONSE)

        assert cluster.id == "abc123"
        assert cluster.name == "my-cluster"
        assert cluster.type == "container.cluster"
        assert cluster.project == "test-project"
        assert cluster.location == "us-central1-a"
        assert cluster.description == "A test cluster"
        assert cluster.initial_node_count == 3
        assert cluster.node_config["machineType"] == "e2-medium"
        assert cluster.master_auth is not None
        assert cluster.network == "default"
        assert cluster.subnetwork == "default"
        assert cluster.cluster_ipv4_cidr == "10.4.0.0/14"
        assert cluster.endpoint == "35.192.0.1"
        assert cluster.status == "RUNNING"
        assert cluster.current_master_version == "1.28.3-gke.1286000"
        assert cluster.current_node_version == "1.28.3-gke.1286000"
        assert cluster.node_pools is not None
        assert len(cluster.node_pools) == 1
        assert cluster.labels == {"env": "test", "team": "platform"}
        assert cluster.created.isoformat().startswith("2025-01-01T00:00:00")
        assert cluster.updated.isoformat().startswith("2025-01-02T00:00:00")

    def test_from_api_response_minimal(self):
        response = {"name": "bare-cluster", "projectId": "p"}
        cluster = GKECluster.from_api_response(response)

        assert cluster.name == "bare-cluster"
        assert cluster.id == ""
        assert cluster.location == ""
        assert cluster.description is None
        assert cluster.initial_node_count is None
        assert cluster.node_config is None
        assert cluster.master_auth is None
        assert cluster.network is None
        assert cluster.subnetwork is None
        assert cluster.cluster_ipv4_cidr is None
        assert cluster.endpoint is None
        assert cluster.status == ""
        assert cluster.current_master_version is None
        assert cluster.current_node_version is None
        assert cluster.node_pools is None

    def test_get_tag(self):
        cluster = GKECluster.from_api_response(SAMPLE_CLUSTER_RESPONSE)
        assert cluster.get_tag("env") == "test"
        assert cluster.get_tag("team") == "platform"
        assert cluster.get_tag("missing") == ""
        assert cluster.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        response = {"name": "bare", "projectId": "p"}
        cluster = GKECluster.from_api_response(response)
        assert cluster.get_tag("env") == ""
        assert cluster.get_tag("env", "fallback") == "fallback"


class TestNodePoolModel:
    """Tests for the NodePool model."""

    def test_from_api_response(self):
        pool = NodePool.from_api_response(SAMPLE_NODE_POOL_RESPONSE)

        assert pool.id == "custom-pool"
        assert pool.name == "custom-pool"
        assert pool.type == "container.nodePool"
        assert pool.project == "test-project"
        assert pool.cluster_name == "my-cluster"
        assert pool.location == "us-central1-a"
        assert pool.config["machineType"] == "e2-standard-4"
        assert pool.initial_node_count == 5
        assert pool.autoscaling["enabled"] is True
        assert pool.autoscaling["minNodeCount"] == 1
        assert pool.autoscaling["maxNodeCount"] == 10
        assert pool.management["autoUpgrade"] is True
        assert pool.management["autoRepair"] is True
        assert pool.status == "RUNNING"
        assert pool.version == "1.28.3-gke.1286000"
        assert pool.instance_group_urls is not None
        assert len(pool.instance_group_urls) == 1

    def test_from_api_response_minimal(self):
        response = {"name": "basic-pool", "projectId": "p"}
        pool = NodePool.from_api_response(response)

        assert pool.name == "basic-pool"
        assert pool.cluster_name == ""
        assert pool.location == ""
        assert pool.config is None
        assert pool.initial_node_count == 0
        assert pool.autoscaling is None
        assert pool.management is None
        assert pool.status == ""
        assert pool.version is None
        assert pool.instance_group_urls is None

    def test_get_tag(self):
        pool = NodePool.from_api_response(SAMPLE_NODE_POOL_RESPONSE)
        assert pool.get_tag("pool-type") == "compute"
        assert pool.get_tag("missing") == ""
        assert pool.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        response = {"name": "bare", "projectId": "p"}
        pool = NodePool.from_api_response(response)
        assert pool.get_tag("key") == ""
        assert pool.get_tag("key", "fallback") == "fallback"


def _setup_cluster_mock(mock_service):
    """Helper to set up the nested mock chain for cluster operations."""
    mock_projects = mock.MagicMock()
    mock_service.projects.return_value = mock_projects
    mock_locations = mock.MagicMock()
    mock_projects.locations.return_value = mock_locations
    mock_clusters = mock.MagicMock()
    mock_locations.clusters.return_value = mock_clusters
    return mock_clusters


def _setup_node_pool_mock(mock_service):
    """Helper to set up the nested mock chain for node pool operations."""
    mock_clusters = _setup_cluster_mock(mock_service)
    mock_node_pools = mock.MagicMock()
    mock_clusters.nodePools.return_value = mock_node_pools
    return mock_clusters, mock_node_pools


class TestGKEServiceClusters:
    """Tests for cluster-related methods."""

    def test_list_clusters(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = _setup_cluster_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {
            "clusters": [SAMPLE_CLUSTER_RESPONSE],
        }

        service = GKEService(project_id="test-project")
        results = service.list_clusters()

        mock_clusters.list.assert_called_once_with(
            parent="projects/test-project/locations/-"
        )
        assert len(results) == 1
        assert isinstance(results[0], GKECluster)
        assert results[0].name == "my-cluster"
        assert results[0].status == "RUNNING"

    def test_list_clusters_with_location(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = _setup_cluster_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {"clusters": []}

        service = GKEService(project_id="test-project")
        service.list_clusters(location="us-central1-a")

        mock_clusters.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1-a"
        )

    def test_list_clusters_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = _setup_cluster_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = GKEService(project_id="test-project")
        results = service.list_clusters()

        assert results == []

    def test_get_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = _setup_cluster_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_clusters.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = GKEService(project_id="test-project")
        result = service.get_cluster("us-central1-a", "my-cluster")

        mock_clusters.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1-a/clusters/my-cluster"
        )
        assert isinstance(result, GKECluster)
        assert result.name == "my-cluster"
        assert result.endpoint == "35.192.0.1"

    def test_create_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = _setup_cluster_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_clusters.create.return_value = mock_create
        operation_response = {"name": "operation-123", "status": "RUNNING"}
        mock_create.execute.return_value = operation_response

        service = GKEService(project_id="test-project")
        result = service.create_cluster(
            location="us-central1-a",
            cluster_name="new-cluster",
            node_count=5,
            machine_type="e2-standard-4",
            labels={"env": "prod"},
        )

        mock_clusters.create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1-a",
            body={
                "cluster": {
                    "name": "new-cluster",
                    "initialNodeCount": 5,
                    "nodeConfig": {
                        "machineType": "e2-standard-4",
                    },
                    "resourceLabels": {"env": "prod"},
                },
            },
        )
        assert result == operation_response

    def test_create_cluster_defaults(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = _setup_cluster_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_clusters.create.return_value = mock_create
        mock_create.execute.return_value = {"name": "op-1"}

        service = GKEService(project_id="test-project")
        service.create_cluster(
            location="us-central1-a",
            cluster_name="default-cluster",
        )

        call_args = mock_clusters.create.call_args
        body = call_args[1]["body"]["cluster"]
        assert body["initialNodeCount"] == 3
        assert body["nodeConfig"]["machineType"] == "e2-medium"
        assert "resourceLabels" not in body
        assert "network" not in body
        assert "subnetwork" not in body

    def test_create_cluster_with_network(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = _setup_cluster_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_clusters.create.return_value = mock_create
        mock_create.execute.return_value = {"name": "op-1"}

        service = GKEService(project_id="test-project")
        service.create_cluster(
            location="us-central1",
            cluster_name="net-cluster",
            network="my-vpc",
            subnetwork="my-subnet",
        )

        call_args = mock_clusters.create.call_args
        body = call_args[1]["body"]["cluster"]
        assert body["network"] == "my-vpc"
        assert body["subnetwork"] == "my-subnet"

    def test_delete_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = _setup_cluster_mock(mock_service)
        mock_delete = mock.MagicMock()
        mock_clusters.delete.return_value = mock_delete
        operation_response = {"name": "operation-456", "status": "RUNNING"}
        mock_delete.execute.return_value = operation_response

        service = GKEService(project_id="test-project")
        result = service.delete_cluster("us-central1-a", "my-cluster")

        mock_clusters.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1-a/clusters/my-cluster"
        )
        assert result == operation_response

    def test_update_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = _setup_cluster_mock(mock_service)
        mock_update = mock.MagicMock()
        mock_clusters.update.return_value = mock_update
        operation_response = {"name": "operation-789", "status": "RUNNING"}
        mock_update.execute.return_value = operation_response

        update_body = {
            "update": {
                "desiredNodePoolId": "default-pool",
                "desiredNodeVersion": "1.29.0-gke.1",
            }
        }

        service = GKEService(project_id="test-project")
        result = service.update_cluster(
            "us-central1-a", "my-cluster", update_body
        )

        mock_clusters.update.assert_called_once_with(
            name="projects/test-project/locations/us-central1-a/clusters/my-cluster",
            body=update_body,
        )
        assert result == operation_response


class TestGKEServiceNodePools:
    """Tests for node pool-related methods."""

    def test_list_node_pools(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_node_pools = _setup_node_pool_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_node_pools.list.return_value = mock_list
        mock_list.execute.return_value = {
            "nodePools": [SAMPLE_NODE_POOL_RESPONSE],
        }

        service = GKEService(project_id="test-project")
        results = service.list_node_pools("us-central1-a", "my-cluster")

        mock_node_pools.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1-a/clusters/my-cluster"
        )
        assert len(results) == 1
        assert isinstance(results[0], NodePool)
        assert results[0].name == "custom-pool"
        assert results[0].status == "RUNNING"

    def test_list_node_pools_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_node_pools = _setup_node_pool_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_node_pools.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = GKEService(project_id="test-project")
        results = service.list_node_pools("us-central1-a", "my-cluster")

        assert results == []

    def test_get_node_pool(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_node_pools = _setup_node_pool_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_node_pools.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_NODE_POOL_RESPONSE

        service = GKEService(project_id="test-project")
        result = service.get_node_pool(
            "us-central1-a", "my-cluster", "custom-pool"
        )

        mock_node_pools.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1-a/clusters/my-cluster/nodePools/custom-pool"
        )
        assert isinstance(result, NodePool)
        assert result.name == "custom-pool"
        assert result.initial_node_count == 5

    def test_create_node_pool(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_node_pools = _setup_node_pool_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_node_pools.create.return_value = mock_create
        operation_response = {"name": "operation-np-1", "status": "RUNNING"}
        mock_create.execute.return_value = operation_response

        service = GKEService(project_id="test-project")
        result = service.create_node_pool(
            location="us-central1-a",
            cluster_name="my-cluster",
            pool_name="gpu-pool",
            node_count=2,
            machine_type="n1-standard-8",
            autoscaling={"enabled": True, "minNodeCount": 1, "maxNodeCount": 5},
        )

        mock_node_pools.create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1-a/clusters/my-cluster",
            body={
                "nodePool": {
                    "name": "gpu-pool",
                    "initialNodeCount": 2,
                    "config": {
                        "machineType": "n1-standard-8",
                    },
                    "autoscaling": {
                        "enabled": True,
                        "minNodeCount": 1,
                        "maxNodeCount": 5,
                    },
                },
            },
        )
        assert result == operation_response

    def test_create_node_pool_no_autoscaling(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_node_pools = _setup_node_pool_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_node_pools.create.return_value = mock_create
        mock_create.execute.return_value = {"name": "op-1"}

        service = GKEService(project_id="test-project")
        service.create_node_pool(
            location="us-central1-a",
            cluster_name="my-cluster",
            pool_name="simple-pool",
            node_count=3,
            machine_type="e2-medium",
        )

        call_args = mock_node_pools.create.call_args
        body = call_args[1]["body"]["nodePool"]
        assert "autoscaling" not in body
        assert body["initialNodeCount"] == 3
        assert body["config"]["machineType"] == "e2-medium"

    def test_delete_node_pool(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_node_pools = _setup_node_pool_mock(mock_service)
        mock_delete = mock.MagicMock()
        mock_node_pools.delete.return_value = mock_delete
        operation_response = {"name": "operation-np-del", "status": "RUNNING"}
        mock_delete.execute.return_value = operation_response

        service = GKEService(project_id="test-project")
        result = service.delete_node_pool(
            "us-central1-a", "my-cluster", "custom-pool"
        )

        mock_node_pools.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1-a/clusters/my-cluster/nodePools/custom-pool"
        )
        assert result == operation_response

    def test_set_node_pool_size(self, mock_discovery):
        _, mock_service = mock_discovery
        _, mock_node_pools = _setup_node_pool_mock(mock_service)
        mock_set_size = mock.MagicMock()
        mock_node_pools.setSize.return_value = mock_set_size
        operation_response = {"name": "operation-resize", "status": "RUNNING"}
        mock_set_size.execute.return_value = operation_response

        service = GKEService(project_id="test-project")
        result = service.set_node_pool_size(
            "us-central1-a", "my-cluster", "custom-pool", 10
        )

        mock_node_pools.setSize.assert_called_once_with(
            name="projects/test-project/locations/us-central1-a/clusters/my-cluster/nodePools/custom-pool",
            body={"nodeCount": 10},
        )
        assert result == operation_response


class TestGKEServiceMultipleClusters:
    """Tests for listing multiple clusters."""

    def test_list_multiple_clusters(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = _setup_cluster_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list

        second_cluster = {
            "id": "def456",
            "name": "staging-cluster",
            "projectId": "test-project",
            "location": "europe-west1",
            "status": "PROVISIONING",
        }
        mock_list.execute.return_value = {
            "clusters": [SAMPLE_CLUSTER_RESPONSE, second_cluster],
        }

        service = GKEService(project_id="test-project")
        results = service.list_clusters()

        assert len(results) == 2
        assert results[0].name == "my-cluster"
        assert results[0].status == "RUNNING"
        assert results[1].name == "staging-cluster"
        assert results[1].status == "PROVISIONING"
        assert results[1].location == "europe-west1"
