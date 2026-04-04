"""Tests for the Cloud Bigtable service implementation."""

import unittest.mock as mock
import pytest

from googleapiclient.errors import HttpError

from gcpoto.services.bigtable import BigtableService
from gcpoto.models.bigtable import (
    BigtableInstance,
    BigtableCluster,
    BigtableTable,
)
from gcpoto.exceptions import ResourceNotFoundError, APIError


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


SAMPLE_INSTANCE_RESPONSE = {
    "name": "projects/test-project/instances/my-instance",
    "displayName": "My Instance",
    "type": "PRODUCTION",
    "state": "READY",
    "labels": {"env": "test", "team": "backend"},
    "createTime": "2025-01-01T00:00:00Z",
    "updateTime": "2025-01-02T00:00:00Z",
}

SAMPLE_CLUSTER_RESPONSE = {
    "name": "projects/test-project/instances/my-instance/clusters/my-cluster",
    "location": "projects/test-project/locations/us-central1-b",
    "serveNodes": 3,
    "defaultStorageType": "SSD",
    "state": "READY",
    "createTime": "2025-01-01T00:00:00Z",
    "updateTime": "2025-01-02T00:00:00Z",
}

SAMPLE_TABLE_RESPONSE = {
    "name": "projects/test-project/instances/my-instance/tables/my-table",
    "columnFamilies": {
        "cf1": {"gcRule": {"maxNumVersions": 1}},
        "cf2": {"gcRule": {"maxAge": "86400s"}},
    },
    "granularity": "MILLIS",
}


class TestBigtableServiceInit:
    """Tests for BigtableService initialization."""

    def test_initialization(self, mock_discovery):
        mock_build, _ = mock_discovery
        service = BigtableService(
            project_id="test-project", credentials_file=None
        )

        assert service.project_id == "test-project"
        assert service.service_name == "bigtableadmin"
        assert service.version == "v2"
        assert service.credentials_file is None
        assert service.resource_model == BigtableInstance
        mock_build.assert_called_once_with(
            "bigtableadmin", "v2", credentials=None
        )


class TestBigtableInstanceModel:
    """Tests for the BigtableInstance model."""

    def test_from_api_response(self):
        instance = BigtableInstance.from_api_response(SAMPLE_INSTANCE_RESPONSE)

        assert instance.id == "my-instance"
        assert instance.name == "my-instance"
        assert instance.type == "bigtable.instance"
        assert instance.project == "test-project"
        assert instance.display_name == "My Instance"
        assert instance.instance_type == "PRODUCTION"
        assert instance.state == "READY"
        assert instance.labels == {"env": "test", "team": "backend"}
        assert instance.created.isoformat().startswith("2025-01-01T00:00:00")
        assert instance.updated.isoformat().startswith("2025-01-02T00:00:00")

    def test_from_api_response_minimal(self):
        response = {"name": "projects/p/instances/bare"}
        instance = BigtableInstance.from_api_response(response)

        assert instance.name == "bare"
        assert instance.project == "p"
        assert instance.display_name == ""
        assert instance.instance_type == ""
        assert instance.state == ""
        assert instance.labels is None

    def test_get_tag(self):
        instance = BigtableInstance.from_api_response(SAMPLE_INSTANCE_RESPONSE)
        assert instance.get_tag("env") == "test"
        assert instance.get_tag("team") == "backend"
        assert instance.get_tag("missing") == ""
        assert instance.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        response = {"name": "projects/p/instances/bare"}
        instance = BigtableInstance.from_api_response(response)
        assert instance.get_tag("env") == ""
        assert instance.get_tag("env", "fallback") == "fallback"


class TestBigtableClusterModel:
    """Tests for the BigtableCluster model."""

    def test_from_api_response(self):
        cluster = BigtableCluster.from_api_response(SAMPLE_CLUSTER_RESPONSE)

        assert cluster.id == "my-cluster"
        assert cluster.name == "my-cluster"
        assert cluster.type == "bigtable.cluster"
        assert cluster.project == "test-project"
        assert cluster.instance_name == "my-instance"
        assert cluster.location == "us-central1-b"
        assert cluster.serve_nodes == 3
        assert cluster.default_storage_type == "SSD"
        assert cluster.state == "READY"

    def test_from_api_response_minimal(self):
        response = {
            "name": "projects/p/instances/inst/clusters/c",
        }
        cluster = BigtableCluster.from_api_response(response)

        assert cluster.name == "c"
        assert cluster.project == "p"
        assert cluster.instance_name == "inst"
        assert cluster.location == ""
        assert cluster.serve_nodes == 0
        assert cluster.default_storage_type == ""
        assert cluster.state == ""


class TestBigtableTableModel:
    """Tests for the BigtableTable model."""

    def test_from_api_response(self):
        table = BigtableTable.from_api_response(SAMPLE_TABLE_RESPONSE)

        assert table.id == "my-table"
        assert table.name == "my-table"
        assert table.type == "bigtable.table"
        assert table.project == "test-project"
        assert table.instance_name == "my-instance"
        assert "cf1" in table.column_families
        assert "cf2" in table.column_families
        assert table.column_families["cf1"]["gcRule"]["maxNumVersions"] == 1
        assert table.granularity == "MILLIS"

    def test_from_api_response_minimal(self):
        response = {"name": "projects/p/instances/inst/tables/t"}
        table = BigtableTable.from_api_response(response)

        assert table.name == "t"
        assert table.project == "p"
        assert table.instance_name == "inst"
        assert table.column_families == {}
        assert table.granularity is None


class TestBigtableServiceInstances:
    """Tests for instance-related methods."""

    def test_list_instances(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value = (
            mock_instances
        )
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {
            "instances": [SAMPLE_INSTANCE_RESPONSE],
        }

        service = BigtableService(project_id="test-project")
        results = service.list_instances()

        mock_instances.list.assert_called_once_with(
            parent="projects/test-project"
        )
        assert len(results) == 1
        assert isinstance(results[0], BigtableInstance)
        assert results[0].name == "my-instance"
        assert results[0].display_name == "My Instance"

    def test_list_instances_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value = (
            mock_instances
        )
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = BigtableService(project_id="test-project")
        results = service.list_instances()

        assert results == []

    def test_get_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value = (
            mock_instances
        )
        mock_get = mock.MagicMock()
        mock_instances.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = BigtableService(project_id="test-project")
        result = service.get_instance("my-instance")

        mock_instances.get.assert_called_once_with(
            name="projects/test-project/instances/my-instance"
        )
        assert isinstance(result, BigtableInstance)
        assert result.name == "my-instance"
        assert result.state == "READY"

    def test_get_instance_not_found(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value = (
            mock_instances
        )
        mock_get = mock.MagicMock()
        mock_instances.get.return_value = mock_get
        mock_get.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigtableService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.get_instance("nonexistent")

    def test_get_instance_api_error(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value = (
            mock_instances
        )
        mock_get = mock.MagicMock()
        mock_instances.get.return_value = mock_get
        mock_get.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Server error"
        )

        service = BigtableService(project_id="test-project")
        with pytest.raises(APIError):
            service.get_instance("my-instance")

    def test_create_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value = (
            mock_instances
        )
        mock_create = mock.MagicMock()
        mock_instances.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = BigtableService(project_id="test-project")
        result = service.create_instance(
            instance_id="my-instance",
            display_name="My Instance",
            instance_type="PRODUCTION",
            clusters={
                "my-cluster": {
                    "location": "us-central1-b",
                    "serveNodes": 3,
                    "defaultStorageType": "SSD",
                }
            },
            labels={"env": "test"},
        )

        mock_instances.create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "instanceId": "my-instance",
                "instance": {
                    "displayName": "My Instance",
                    "type": "PRODUCTION",
                    "labels": {"env": "test"},
                },
                "clusters": {
                    "my-cluster": {
                        "location": "projects/test-project/locations/us-central1-b",
                        "serveNodes": 3,
                        "defaultStorageType": "SSD",
                    }
                },
            },
        )
        assert isinstance(result, BigtableInstance)
        assert result.name == "my-instance"

    def test_create_instance_no_clusters(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value = (
            mock_instances
        )
        mock_create = mock.MagicMock()
        mock_instances.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = BigtableService(project_id="test-project")
        service.create_instance(
            instance_id="my-instance",
            display_name="My Instance",
        )

        call_args = mock_instances.create.call_args
        body = call_args[1]["body"]
        assert body["clusters"] == {}

    def test_update_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value = (
            mock_instances
        )
        mock_update = mock.MagicMock()
        mock_instances.partialUpdateInstance.return_value = mock_update
        mock_update.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = BigtableService(project_id="test-project")
        result = service.update_instance(
            instance_id="my-instance",
            display_name="Updated Name",
            labels={"env": "prod"},
        )

        mock_instances.partialUpdateInstance.assert_called_once_with(
            name="projects/test-project/instances/my-instance",
            body={
                "name": "projects/test-project/instances/my-instance",
                "displayName": "Updated Name",
                "labels": {"env": "prod"},
            },
            updateMask="displayName,labels",
        )
        assert isinstance(result, BigtableInstance)

    def test_delete_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value = (
            mock_instances
        )
        mock_delete = mock.MagicMock()
        mock_instances.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = BigtableService(project_id="test-project")
        result = service.delete_instance("my-instance")

        mock_instances.delete.assert_called_once_with(
            name="projects/test-project/instances/my-instance"
        )
        mock_delete.execute.assert_called_once()
        assert result is True

    def test_delete_instance_not_found(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value = (
            mock_instances
        )
        mock_delete = mock.MagicMock()
        mock_instances.delete.return_value = mock_delete
        mock_delete.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigtableService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.delete_instance("nonexistent")


class TestBigtableServiceClusters:
    """Tests for cluster-related methods."""

    def test_list_clusters(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.clusters.return_value = (
            mock_clusters
        )
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {
            "clusters": [SAMPLE_CLUSTER_RESPONSE],
        }

        service = BigtableService(project_id="test-project")
        results = service.list_clusters("my-instance")

        mock_clusters.list.assert_called_once_with(
            parent="projects/test-project/instances/my-instance"
        )
        assert len(results) == 1
        assert isinstance(results[0], BigtableCluster)
        assert results[0].name == "my-cluster"
        assert results[0].serve_nodes == 3

    def test_list_clusters_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.clusters.return_value = (
            mock_clusters
        )
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = BigtableService(project_id="test-project")
        results = service.list_clusters("my-instance")

        assert results == []

    def test_get_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.clusters.return_value = (
            mock_clusters
        )
        mock_get = mock.MagicMock()
        mock_clusters.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = BigtableService(project_id="test-project")
        result = service.get_cluster("my-instance", "my-cluster")

        mock_clusters.get.assert_called_once_with(
            name="projects/test-project/instances/my-instance/clusters/my-cluster"
        )
        assert isinstance(result, BigtableCluster)
        assert result.name == "my-cluster"
        assert result.location == "us-central1-b"

    def test_get_cluster_not_found(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.clusters.return_value = (
            mock_clusters
        )
        mock_get = mock.MagicMock()
        mock_clusters.get.return_value = mock_get
        mock_get.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigtableService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.get_cluster("my-instance", "nonexistent")

    def test_create_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.clusters.return_value = (
            mock_clusters
        )
        mock_create = mock.MagicMock()
        mock_clusters.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = BigtableService(project_id="test-project")
        result = service.create_cluster(
            instance_id="my-instance",
            cluster_id="my-cluster",
            location="us-central1-b",
            serve_nodes=3,
            storage_type="SSD",
        )

        mock_clusters.create.assert_called_once_with(
            parent="projects/test-project/instances/my-instance",
            clusterId="my-cluster",
            body={
                "location": "projects/test-project/locations/us-central1-b",
                "serveNodes": 3,
                "defaultStorageType": "SSD",
            },
        )
        assert isinstance(result, BigtableCluster)
        assert result.name == "my-cluster"

    def test_create_cluster_default_storage(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.clusters.return_value = (
            mock_clusters
        )
        mock_create = mock.MagicMock()
        mock_clusters.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = BigtableService(project_id="test-project")
        service.create_cluster(
            instance_id="my-instance",
            cluster_id="my-cluster",
            location="us-central1-b",
            serve_nodes=3,
        )

        call_args = mock_clusters.create.call_args
        body = call_args[1]["body"]
        assert body["defaultStorageType"] == "SSD"

    def test_update_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.clusters.return_value = (
            mock_clusters
        )
        mock_update = mock.MagicMock()
        mock_clusters.update.return_value = mock_update
        mock_update.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = BigtableService(project_id="test-project")
        result = service.update_cluster(
            instance_id="my-instance",
            cluster_id="my-cluster",
            serve_nodes=5,
        )

        mock_clusters.update.assert_called_once_with(
            name="projects/test-project/instances/my-instance/clusters/my-cluster",
            body={"serveNodes": 5},
        )
        assert isinstance(result, BigtableCluster)

    def test_delete_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.clusters.return_value = (
            mock_clusters
        )
        mock_delete = mock.MagicMock()
        mock_clusters.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = BigtableService(project_id="test-project")
        result = service.delete_cluster("my-instance", "my-cluster")

        mock_clusters.delete.assert_called_once_with(
            name="projects/test-project/instances/my-instance/clusters/my-cluster"
        )
        mock_delete.execute.assert_called_once()
        assert result is True

    def test_delete_cluster_not_found(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.clusters.return_value = (
            mock_clusters
        )
        mock_delete = mock.MagicMock()
        mock_clusters.delete.return_value = mock_delete
        mock_delete.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigtableService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.delete_cluster("my-instance", "nonexistent")


class TestBigtableServiceTables:
    """Tests for table-related methods."""

    def test_list_tables(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_tables = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.tables.return_value = (
            mock_tables
        )
        mock_list = mock.MagicMock()
        mock_tables.list.return_value = mock_list
        mock_list.execute.return_value = {
            "tables": [SAMPLE_TABLE_RESPONSE],
        }
        # No pagination
        mock_tables.list_next.return_value = None

        service = BigtableService(project_id="test-project")
        results = service.list_tables("my-instance")

        mock_tables.list.assert_called_once_with(
            parent="projects/test-project/instances/my-instance"
        )
        assert len(results) == 1
        assert isinstance(results[0], BigtableTable)
        assert results[0].name == "my-table"
        assert "cf1" in results[0].column_families

    def test_list_tables_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_tables = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.tables.return_value = (
            mock_tables
        )
        mock_list = mock.MagicMock()
        mock_tables.list.return_value = mock_list
        mock_list.execute.return_value = {}
        mock_tables.list_next.return_value = None

        service = BigtableService(project_id="test-project")
        results = service.list_tables("my-instance")

        assert results == []

    def test_list_tables_pagination(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_tables = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.tables.return_value = (
            mock_tables
        )

        # First page
        mock_list = mock.MagicMock()
        mock_tables.list.return_value = mock_list
        mock_list.execute.return_value = {
            "tables": [SAMPLE_TABLE_RESPONSE],
        }

        # Second page
        second_table = {
            "name": "projects/test-project/instances/my-instance/tables/table-2",
            "columnFamilies": {"cf_a": {}},
        }
        mock_next_request = mock.MagicMock()
        mock_next_request.execute.return_value = {
            "tables": [second_table],
        }
        mock_tables.list_next.side_effect = [mock_next_request, None]

        service = BigtableService(project_id="test-project")
        results = service.list_tables("my-instance")

        assert len(results) == 2
        assert results[0].name == "my-table"
        assert results[1].name == "table-2"

    def test_get_table(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_tables = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.tables.return_value = (
            mock_tables
        )
        mock_get = mock.MagicMock()
        mock_tables.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_TABLE_RESPONSE

        service = BigtableService(project_id="test-project")
        result = service.get_table("my-instance", "my-table")

        mock_tables.get.assert_called_once_with(
            name="projects/test-project/instances/my-instance/tables/my-table"
        )
        assert isinstance(result, BigtableTable)
        assert result.name == "my-table"
        assert result.granularity == "MILLIS"

    def test_get_table_not_found(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_tables = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.tables.return_value = (
            mock_tables
        )
        mock_get = mock.MagicMock()
        mock_tables.get.return_value = mock_get
        mock_get.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigtableService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.get_table("my-instance", "nonexistent")

    def test_create_table(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_tables = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.tables.return_value = (
            mock_tables
        )
        mock_create = mock.MagicMock()
        mock_tables.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_TABLE_RESPONSE

        column_families = {
            "cf1": {"gcRule": {"maxNumVersions": 1}},
            "cf2": {"gcRule": {"maxAge": "86400s"}},
        }

        service = BigtableService(project_id="test-project")
        result = service.create_table(
            instance_id="my-instance",
            table_id="my-table",
            column_families=column_families,
        )

        mock_tables.create.assert_called_once_with(
            parent="projects/test-project/instances/my-instance",
            body={
                "tableId": "my-table",
                "table": {"columnFamilies": column_families},
            },
        )
        assert isinstance(result, BigtableTable)
        assert result.name == "my-table"

    def test_create_table_no_column_families(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_tables = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.tables.return_value = (
            mock_tables
        )
        mock_create = mock.MagicMock()
        mock_tables.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_TABLE_RESPONSE

        service = BigtableService(project_id="test-project")
        service.create_table(
            instance_id="my-instance",
            table_id="my-table",
        )

        call_args = mock_tables.create.call_args
        body = call_args[1]["body"]
        assert body["table"] == {}

    def test_delete_table(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_tables = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.tables.return_value = (
            mock_tables
        )
        mock_delete = mock.MagicMock()
        mock_tables.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = BigtableService(project_id="test-project")
        result = service.delete_table("my-instance", "my-table")

        mock_tables.delete.assert_called_once_with(
            name="projects/test-project/instances/my-instance/tables/my-table"
        )
        mock_delete.execute.assert_called_once()
        assert result is True

    def test_delete_table_not_found(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_tables = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.tables.return_value = (
            mock_tables
        )
        mock_delete = mock.MagicMock()
        mock_tables.delete.return_value = mock_delete
        mock_delete.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigtableService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.delete_table("my-instance", "nonexistent")

    def test_delete_table_api_error(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_tables = mock.MagicMock()
        mock_service.projects.return_value.instances.return_value.tables.return_value = (
            mock_tables
        )
        mock_delete = mock.MagicMock()
        mock_tables.delete.return_value = mock_delete
        mock_delete.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Server error"
        )

        service = BigtableService(project_id="test-project")
        with pytest.raises(APIError):
            service.delete_table("my-instance", "my-table")
