"""Tests for the Cloud Spanner service implementation."""

import unittest.mock as mock
import pytest

from gcpoto.services.spanner import SpannerService
from gcpoto.models.spanner import SpannerInstance, SpannerDatabase


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


SAMPLE_INSTANCE_RESPONSE = {
    "name": "projects/test-project/instances/my-instance",
    "config": "projects/test-project/instanceConfigs/regional-us-central1",
    "displayName": "My Instance",
    "nodeCount": 3,
    "processingUnits": 3000,
    "state": "READY",
    "labels": {"env": "test", "team": "backend"},
    "createTime": "2025-01-01T00:00:00Z",
    "updateTime": "2025-01-02T00:00:00Z",
}

SAMPLE_INSTANCE_RESPONSE_MINIMAL = {
    "name": "projects/test-project/instances/bare-instance",
}

SAMPLE_DATABASE_RESPONSE = {
    "name": "projects/test-project/instances/my-instance/databases/mydb",
    "state": "READY",
    "versionRetentionPeriod": "1h",
    "earliestVersionTime": "2025-01-01T00:00:00Z",
    "encryptionConfig": {
        "kmsKeyName": "projects/test-project/locations/us/keyRings/ring/cryptoKeys/key",
    },
    "databaseDialect": "GOOGLE_STANDARD_SQL",
    "createTime": "2025-01-01T00:00:00Z",
}

SAMPLE_DATABASE_RESPONSE_MINIMAL = {
    "name": "projects/test-project/instances/my-instance/databases/baredb",
}


class TestSpannerServiceInit:
    """Tests for SpannerService initialization."""

    def test_initialization(self, mock_discovery):
        mock_build, _ = mock_discovery
        service = SpannerService(
            project_id="test-project", credentials_file=None
        )

        assert service.project_id == "test-project"
        assert service.service_name == "spanner"
        assert service.version == "v1"
        assert service.credentials_file is None
        assert service.resource_model == SpannerInstance
        mock_build.assert_called_once_with("spanner", "v1", credentials=None)


class TestSpannerInstanceModel:
    """Tests for the SpannerInstance model."""

    def test_from_api_response(self):
        instance = SpannerInstance.from_api_response(SAMPLE_INSTANCE_RESPONSE)

        assert instance.id == "my-instance"
        assert instance.name == "my-instance"
        assert instance.type == "spanner.instance"
        assert instance.project == "test-project"
        assert instance.display_name == "My Instance"
        assert instance.config == "projects/test-project/instanceConfigs/regional-us-central1"
        assert instance.node_count == 3
        assert instance.processing_units == 3000
        assert instance.state == "READY"
        assert instance.labels == {"env": "test", "team": "backend"}
        assert instance.created.isoformat().startswith("2025-01-01T00:00:00")
        assert instance.updated.isoformat().startswith("2025-01-02T00:00:00")

    def test_from_api_response_minimal(self):
        instance = SpannerInstance.from_api_response(
            SAMPLE_INSTANCE_RESPONSE_MINIMAL
        )

        assert instance.name == "bare-instance"
        assert instance.display_name == ""
        assert instance.config == ""
        assert instance.node_count == 0
        assert instance.processing_units is None
        assert instance.state == ""
        assert instance.created is None
        assert instance.updated is None

    def test_get_tag(self):
        instance = SpannerInstance.from_api_response(SAMPLE_INSTANCE_RESPONSE)
        assert instance.get_tag("env") == "test"
        assert instance.get_tag("team") == "backend"
        assert instance.get_tag("missing") == ""
        assert instance.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        instance = SpannerInstance.from_api_response(
            SAMPLE_INSTANCE_RESPONSE_MINIMAL
        )
        assert instance.get_tag("env") == ""
        assert instance.get_tag("env", "fallback") == "fallback"


class TestSpannerDatabaseModel:
    """Tests for the SpannerDatabase model."""

    def test_from_api_response(self):
        db = SpannerDatabase.from_api_response(SAMPLE_DATABASE_RESPONSE)

        assert db.id == "mydb"
        assert db.name == "mydb"
        assert db.type == "spanner.database"
        assert db.project == "test-project"
        assert db.instance_name == "my-instance"
        assert db.state == "READY"
        assert db.version_retention_period == "1h"
        assert db.earliest_version_time is not None
        assert db.encryption_config is not None
        assert db.encryption_config["kmsKeyName"].endswith("/key")
        assert db.database_dialect == "GOOGLE_STANDARD_SQL"
        assert db.created.isoformat().startswith("2025-01-01T00:00:00")

    def test_from_api_response_minimal(self):
        db = SpannerDatabase.from_api_response(SAMPLE_DATABASE_RESPONSE_MINIMAL)

        assert db.name == "baredb"
        assert db.instance_name == "my-instance"
        assert db.state == ""
        assert db.version_retention_period is None
        assert db.earliest_version_time is None
        assert db.encryption_config is None
        assert db.database_dialect is None
        assert db.created is None


class TestSpannerServiceInstances:
    """Tests for instance-related methods."""

    def test_list_instances(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {
            "instances": [SAMPLE_INSTANCE_RESPONSE],
        }
        mock_instances.list_next.return_value = None

        service = SpannerService(project_id="test-project")
        results = service.list_instances()

        mock_instances.list.assert_called_once_with(
            parent="projects/test-project"
        )
        assert len(results) == 1
        assert isinstance(results[0], SpannerInstance)
        assert results[0].name == "my-instance"
        assert results[0].display_name == "My Instance"

    def test_list_instances_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {}
        mock_instances.list_next.return_value = None

        service = SpannerService(project_id="test-project")
        results = service.list_instances()

        assert results == []

    def test_list_instances_pagination(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list

        page1_response = {
            "instances": [SAMPLE_INSTANCE_RESPONSE],
        }
        second_instance = {
            "name": "projects/test-project/instances/second-instance",
            "displayName": "Second",
            "state": "READY",
        }
        page2_response = {
            "instances": [second_instance],
        }

        mock_list.execute.return_value = page1_response

        mock_list_page2 = mock.MagicMock()
        mock_list_page2.execute.return_value = page2_response
        mock_instances.list_next.side_effect = [mock_list_page2, None]

        service = SpannerService(project_id="test-project")
        results = service.list_instances()

        assert len(results) == 2
        assert results[0].name == "my-instance"
        assert results[1].name == "second-instance"

    def test_get_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_get = mock.MagicMock()
        mock_instances.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = SpannerService(project_id="test-project")
        result = service.get_instance("my-instance")

        mock_instances.get.assert_called_once_with(
            name="projects/test-project/instances/my-instance"
        )
        assert isinstance(result, SpannerInstance)
        assert result.name == "my-instance"
        assert result.state == "READY"

    def test_create_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_create = mock.MagicMock()
        mock_instances.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = SpannerService(project_id="test-project")
        result = service.create_instance(
            instance_id="my-instance",
            display_name="My Instance",
            config="projects/test-project/instanceConfigs/regional-us-central1",
            node_count=3,
            labels={"env": "test"},
        )

        mock_instances.create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "instanceId": "my-instance",
                "instance": {
                    "displayName": "My Instance",
                    "config": "projects/test-project/instanceConfigs/regional-us-central1",
                    "nodeCount": 3,
                    "labels": {"env": "test"},
                },
            },
        )
        assert isinstance(result, SpannerInstance)
        assert result.name == "my-instance"

    def test_create_instance_with_processing_units(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_create = mock.MagicMock()
        mock_instances.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = SpannerService(project_id="test-project")
        service.create_instance(
            instance_id="my-instance",
            display_name="My Instance",
            config="projects/test-project/instanceConfigs/regional-us-central1",
            processing_units=500,
        )

        call_args = mock_instances.create.call_args
        body = call_args[1]["body"]
        assert "nodeCount" not in body["instance"]
        assert body["instance"]["processingUnits"] == 500

    def test_create_instance_no_labels(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_create = mock.MagicMock()
        mock_instances.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = SpannerService(project_id="test-project")
        service.create_instance(
            instance_id="my-instance",
            display_name="My Instance",
            config="projects/test-project/instanceConfigs/regional-us-central1",
        )

        call_args = mock_instances.create.call_args
        body = call_args[1]["body"]
        assert "labels" not in body["instance"]

    def test_update_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_patch = mock.MagicMock()
        mock_instances.patch.return_value = mock_patch
        mock_patch.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = SpannerService(project_id="test-project")
        result = service.update_instance(
            instance_id="my-instance",
            display_name="Updated Name",
            node_count=5,
        )

        mock_instances.patch.assert_called_once_with(
            name="projects/test-project/instances/my-instance",
            body={
                "instance": {
                    "name": "projects/test-project/instances/my-instance",
                    "displayName": "Updated Name",
                    "nodeCount": 5,
                },
                "fieldMask": "displayName,nodeCount",
            },
        )
        assert isinstance(result, SpannerInstance)

    def test_update_instance_labels_only(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_patch = mock.MagicMock()
        mock_instances.patch.return_value = mock_patch
        mock_patch.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = SpannerService(project_id="test-project")
        service.update_instance(
            instance_id="my-instance",
            labels={"env": "prod"},
        )

        call_args = mock_instances.patch.call_args
        body = call_args[1]["body"]
        assert body["instance"]["labels"] == {"env": "prod"}
        assert body["fieldMask"] == "labels"

    def test_update_instance_processing_units(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_patch = mock.MagicMock()
        mock_instances.patch.return_value = mock_patch
        mock_patch.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = SpannerService(project_id="test-project")
        service.update_instance(
            instance_id="my-instance",
            processing_units=1000,
        )

        call_args = mock_instances.patch.call_args
        body = call_args[1]["body"]
        assert body["instance"]["processingUnits"] == 1000
        assert body["fieldMask"] == "processingUnits"

    def test_delete_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_delete = mock.MagicMock()
        mock_instances.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = SpannerService(project_id="test-project")
        result = service.delete_instance("my-instance")

        mock_instances.delete.assert_called_once_with(
            name="projects/test-project/instances/my-instance"
        )
        mock_delete.execute.assert_called_once()
        assert result is True


class TestSpannerServiceDatabases:
    """Tests for database-related methods."""

    def test_list_databases(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_list = mock.MagicMock()
        mock_databases.list.return_value = mock_list
        mock_list.execute.return_value = {
            "databases": [SAMPLE_DATABASE_RESPONSE],
        }
        mock_databases.list_next.return_value = None

        service = SpannerService(project_id="test-project")
        results = service.list_databases("my-instance")

        mock_databases.list.assert_called_once_with(
            parent="projects/test-project/instances/my-instance"
        )
        assert len(results) == 1
        assert isinstance(results[0], SpannerDatabase)
        assert results[0].name == "mydb"
        assert results[0].state == "READY"

    def test_list_databases_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_list = mock.MagicMock()
        mock_databases.list.return_value = mock_list
        mock_list.execute.return_value = {}
        mock_databases.list_next.return_value = None

        service = SpannerService(project_id="test-project")
        results = service.list_databases("my-instance")

        assert results == []

    def test_get_database(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_get = mock.MagicMock()
        mock_databases.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_DATABASE_RESPONSE

        service = SpannerService(project_id="test-project")
        result = service.get_database("my-instance", "mydb")

        mock_databases.get.assert_called_once_with(
            name="projects/test-project/instances/my-instance/databases/mydb"
        )
        assert isinstance(result, SpannerDatabase)
        assert result.name == "mydb"
        assert result.instance_name == "my-instance"

    def test_create_database(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_create = mock.MagicMock()
        mock_databases.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_DATABASE_RESPONSE

        service = SpannerService(project_id="test-project")
        result = service.create_database("my-instance", "mydb")

        mock_databases.create.assert_called_once_with(
            parent="projects/test-project/instances/my-instance",
            body={
                "createStatement": "CREATE DATABASE `mydb`",
            },
        )
        assert isinstance(result, SpannerDatabase)
        assert result.name == "mydb"

    def test_create_database_with_extra_statements(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_create = mock.MagicMock()
        mock_databases.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_DATABASE_RESPONSE

        extra = [
            "CREATE TABLE Users (Id INT64 NOT NULL) PRIMARY KEY (Id)",
        ]
        service = SpannerService(project_id="test-project")
        service.create_database(
            "my-instance", "mydb", extra_statements=extra
        )

        call_args = mock_databases.create.call_args
        body = call_args[1]["body"]
        assert body["extraStatements"] == extra

    def test_drop_database(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_drop = mock.MagicMock()
        mock_databases.dropDatabase.return_value = mock_drop
        mock_drop.execute.return_value = {}

        service = SpannerService(project_id="test-project")
        result = service.drop_database("my-instance", "mydb")

        mock_databases.dropDatabase.assert_called_once_with(
            database="projects/test-project/instances/my-instance/databases/mydb"
        )
        mock_drop.execute.assert_called_once()
        assert result is True

    def test_get_database_ddl(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_get_ddl = mock.MagicMock()
        mock_databases.getDdl.return_value = mock_get_ddl
        ddl_statements = [
            "CREATE TABLE Users (Id INT64 NOT NULL) PRIMARY KEY (Id)",
            "CREATE TABLE Orders (Id INT64 NOT NULL) PRIMARY KEY (Id)",
        ]
        mock_get_ddl.execute.return_value = {
            "statements": ddl_statements,
        }

        service = SpannerService(project_id="test-project")
        result = service.get_database_ddl("my-instance", "mydb")

        mock_databases.getDdl.assert_called_once_with(
            database="projects/test-project/instances/my-instance/databases/mydb"
        )
        assert result == ddl_statements

    def test_get_database_ddl_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_get_ddl = mock.MagicMock()
        mock_databases.getDdl.return_value = mock_get_ddl
        mock_get_ddl.execute.return_value = {}

        service = SpannerService(project_id="test-project")
        result = service.get_database_ddl("my-instance", "mydb")

        assert result == []

    def test_update_database_ddl(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_update_ddl = mock.MagicMock()
        mock_databases.updateDdl.return_value = mock_update_ddl
        operation_response = {"name": "operation-123", "done": False}
        mock_update_ddl.execute.return_value = operation_response

        statements = [
            "ALTER TABLE Users ADD COLUMN Email STRING(MAX)",
        ]

        service = SpannerService(project_id="test-project")
        result = service.update_database_ddl(
            "my-instance", "mydb", statements
        )

        mock_databases.updateDdl.assert_called_once_with(
            database="projects/test-project/instances/my-instance/databases/mydb",
            body={"statements": statements},
        )
        assert result == operation_response


class TestSpannerServiceExecuteSQL:
    """Tests for execute_sql method."""

    def test_execute_sql(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_sessions = mock.MagicMock()
        mock_databases.sessions.return_value = mock_sessions

        # Mock session creation
        mock_create_session = mock.MagicMock()
        mock_sessions.create.return_value = mock_create_session
        mock_create_session.execute.return_value = {
            "name": "projects/test-project/instances/my-instance/databases/mydb/sessions/session1",
        }

        # Mock SQL execution
        mock_execute_sql = mock.MagicMock()
        mock_sessions.executeSql.return_value = mock_execute_sql
        query_result = {
            "metadata": {"rowType": {"fields": [{"name": "Id"}]}},
            "rows": [["1"], ["2"]],
        }
        mock_execute_sql.execute.return_value = query_result

        # Mock session deletion
        mock_delete_session = mock.MagicMock()
        mock_sessions.delete.return_value = mock_delete_session
        mock_delete_session.execute.return_value = {}

        service = SpannerService(project_id="test-project")
        result = service.execute_sql(
            "my-instance", "mydb", "SELECT Id FROM Users"
        )

        mock_sessions.create.assert_called_once_with(
            database="projects/test-project/instances/my-instance/databases/mydb",
            body={},
        )
        mock_sessions.executeSql.assert_called_once_with(
            session="projects/test-project/instances/my-instance/databases/mydb/sessions/session1",
            body={
                "sql": "SELECT Id FROM Users",
                "transaction": {
                    "singleUse": {"readOnly": {"strong": True}},
                },
            },
        )
        assert result == query_result

    def test_execute_sql_with_params(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_sessions = mock.MagicMock()
        mock_databases.sessions.return_value = mock_sessions

        mock_create_session = mock.MagicMock()
        mock_sessions.create.return_value = mock_create_session
        mock_create_session.execute.return_value = {
            "name": "projects/test-project/instances/my-instance/databases/mydb/sessions/s1",
        }

        mock_execute_sql = mock.MagicMock()
        mock_sessions.executeSql.return_value = mock_execute_sql
        mock_execute_sql.execute.return_value = {"rows": []}

        mock_delete_session = mock.MagicMock()
        mock_sessions.delete.return_value = mock_delete_session
        mock_delete_session.execute.return_value = {}

        params = {"id": "123"}
        service = SpannerService(project_id="test-project")
        service.execute_sql(
            "my-instance",
            "mydb",
            "SELECT * FROM Users WHERE Id = @id",
            params=params,
        )

        call_args = mock_sessions.executeSql.call_args
        body = call_args[1]["body"]
        assert body["params"] == params

    def test_execute_sql_cleans_up_session_on_error(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_instances = mock.MagicMock()
        mock_projects.instances.return_value = mock_instances
        mock_databases = mock.MagicMock()
        mock_instances.databases.return_value = mock_databases
        mock_sessions = mock.MagicMock()
        mock_databases.sessions.return_value = mock_sessions

        mock_create_session = mock.MagicMock()
        mock_sessions.create.return_value = mock_create_session
        mock_create_session.execute.return_value = {
            "name": "projects/test-project/instances/my-instance/databases/mydb/sessions/s1",
        }

        # SQL execution fails
        mock_execute_sql = mock.MagicMock()
        mock_sessions.executeSql.return_value = mock_execute_sql
        mock_execute_sql.execute.side_effect = Exception("SQL error")

        mock_delete_session = mock.MagicMock()
        mock_sessions.delete.return_value = mock_delete_session
        mock_delete_session.execute.return_value = {}

        service = SpannerService(project_id="test-project")

        with pytest.raises(Exception, match="SQL error"):
            service.execute_sql(
                "my-instance", "mydb", "SELECT * FROM BadTable"
            )

        # Session should still be deleted despite the error
        mock_sessions.delete.assert_called_once_with(
            name="projects/test-project/instances/my-instance/databases/mydb/sessions/s1"
        )


class TestSpannerServicePathHelpers:
    """Tests for internal path formatting helpers."""

    def test_instance_path(self, mock_discovery):
        _, _ = mock_discovery
        service = SpannerService(project_id="test-project")
        assert service._instance_path("my-instance") == (
            "projects/test-project/instances/my-instance"
        )

    def test_database_path(self, mock_discovery):
        _, _ = mock_discovery
        service = SpannerService(project_id="test-project")
        assert service._database_path("my-instance", "mydb") == (
            "projects/test-project/instances/my-instance/databases/mydb"
        )
