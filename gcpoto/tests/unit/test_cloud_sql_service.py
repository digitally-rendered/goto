"""Tests for the Cloud SQL service implementation."""

import unittest.mock as mock
import pytest

from gcpoto.services.cloud_sql import CloudSQLService
from gcpoto.models.cloud_sql import (
    SQLInstance,
    SQLDatabase,
    SQLUser,
    SQLBackupRun,
)


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


SAMPLE_INSTANCE_RESPONSE = {
    "name": "my-instance",
    "project": "test-project",
    "databaseVersion": "POSTGRES_15",
    "region": "us-central1",
    "state": "RUNNABLE",
    "connectionName": "test-project:us-central1:my-instance",
    "gceZone": "us-central1-a",
    "ipAddresses": [
        {"type": "PRIMARY", "ipAddress": "10.0.0.1"},
    ],
    "settings": {
        "tier": "db-n1-standard-1",
        "availabilityType": "ZONAL",
        "userLabels": {"env": "test"},
    },
    "createTime": "2025-01-01T00:00:00Z",
    "updateTime": "2025-01-02T00:00:00Z",
}

SAMPLE_DATABASE_RESPONSE = {
    "name": "mydb",
    "instance": "my-instance",
    "project": "test-project",
    "charset": "UTF8",
    "collation": "en_US.UTF8",
    "selfLink": "https://sqladmin.googleapis.com/v1/projects/test-project/instances/my-instance/databases/mydb",
}

SAMPLE_USER_RESPONSE = {
    "name": "admin",
    "instance": "my-instance",
    "project": "test-project",
    "host": "%",
    "passwordSet": True,
}

SAMPLE_BACKUP_RUN_RESPONSE = {
    "id": "1234567890",
    "instance": "my-instance",
    "project": "test-project",
    "status": "SUCCESSFUL",
    "startTime": "2025-01-01T02:00:00Z",
    "endTime": "2025-01-01T02:15:00Z",
    "backupKind": "SNAPSHOT",
    "location": "us",
    "diskEncryptionStatus": {
        "kmsKeyVersionName": "projects/test-project/locations/us/keyRings/my-ring/cryptoKeys/my-key/cryptoKeyVersions/1",
    },
}


class TestCloudSQLServiceInit:
    """Tests for CloudSQLService initialization."""

    def test_initialization(self, mock_discovery):
        mock_build, _ = mock_discovery
        service = CloudSQLService(
            project_id="test-project", credentials_file=None
        )

        assert service.project_id == "test-project"
        assert service.service_name == "sqladmin"
        assert service.version == "v1"
        assert service.credentials_file is None
        assert service.resource_model == SQLInstance
        mock_build.assert_called_once_with("sqladmin", "v1", credentials=None)


class TestSQLInstanceModel:
    """Tests for the SQLInstance model."""

    def test_from_api_response(self):
        instance = SQLInstance.from_api_response(SAMPLE_INSTANCE_RESPONSE)

        assert instance.id == "my-instance"
        assert instance.name == "my-instance"
        assert instance.type == "sqladmin.instance"
        assert instance.project == "test-project"
        assert instance.database_version == "POSTGRES_15"
        assert instance.region == "us-central1"
        assert instance.tier == "db-n1-standard-1"
        assert instance.state == "RUNNABLE"
        assert instance.connection_name == "test-project:us-central1:my-instance"
        assert instance.gce_zone == "us-central1-a"
        assert len(instance.ip_addresses) == 1
        assert instance.ip_addresses[0]["ipAddress"] == "10.0.0.1"
        assert instance.settings["tier"] == "db-n1-standard-1"
        assert instance.labels == {"env": "test"}
        assert instance.created.isoformat().startswith("2025-01-01T00:00:00")
        assert instance.updated.isoformat().startswith("2025-01-02T00:00:00")

    def test_from_api_response_minimal(self):
        response = {"name": "bare-instance", "project": "p"}
        instance = SQLInstance.from_api_response(response)

        assert instance.name == "bare-instance"
        assert instance.database_version == ""
        assert instance.tier == ""
        assert instance.state == ""
        assert instance.ip_addresses == []
        assert instance.settings == {}
        assert instance.connection_name is None
        assert instance.gce_zone is None

    def test_get_tag(self):
        instance = SQLInstance.from_api_response(SAMPLE_INSTANCE_RESPONSE)
        assert instance.get_tag("env") == "test"
        assert instance.get_tag("missing") == ""
        assert instance.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        response = {"name": "bare", "project": "p"}
        instance = SQLInstance.from_api_response(response)
        assert instance.get_tag("env") == ""
        assert instance.get_tag("env", "fallback") == "fallback"


class TestSQLDatabaseModel:
    """Tests for the SQLDatabase model."""

    def test_from_api_response(self):
        db = SQLDatabase.from_api_response(SAMPLE_DATABASE_RESPONSE)

        assert db.id == "mydb"
        assert db.name == "mydb"
        assert db.type == "sqladmin.database"
        assert db.project == "test-project"
        assert db.instance_name == "my-instance"
        assert db.charset == "UTF8"
        assert db.collation == "en_US.UTF8"
        assert db.self_link is not None

    def test_from_api_response_minimal(self):
        response = {"name": "testdb", "project": "p"}
        db = SQLDatabase.from_api_response(response)

        assert db.name == "testdb"
        assert db.instance_name == ""
        assert db.charset == ""
        assert db.collation == ""
        assert db.self_link is None


class TestSQLUserModel:
    """Tests for the SQLUser model."""

    def test_from_api_response(self):
        user = SQLUser.from_api_response(SAMPLE_USER_RESPONSE)

        assert user.id == "admin@%"
        assert user.name == "admin"
        assert user.type == "sqladmin.user"
        assert user.project == "test-project"
        assert user.instance_name == "my-instance"
        assert user.host == "%"
        assert user.password_set is True

    def test_from_api_response_minimal(self):
        response = {"name": "root", "project": "p"}
        user = SQLUser.from_api_response(response)

        assert user.name == "root"
        assert user.id == "root@"
        assert user.host == ""
        assert user.password_set is False


class TestSQLBackupRunModel:
    """Tests for the SQLBackupRun model."""

    def test_from_api_response(self):
        backup = SQLBackupRun.from_api_response(SAMPLE_BACKUP_RUN_RESPONSE)

        assert backup.id == "1234567890"
        assert backup.name == "1234567890"
        assert backup.type == "sqladmin.backupRun"
        assert backup.project == "test-project"
        assert backup.instance_name == "my-instance"
        assert backup.status == "SUCCESSFUL"
        assert backup.start_time.isoformat().startswith("2025-01-01T02:00:00")
        assert backup.end_time.isoformat().startswith("2025-01-01T02:15:00")
        assert backup.backup_kind == "SNAPSHOT"
        assert backup.location == "us"
        assert backup.disk_encryption_status is not None

    def test_from_api_response_minimal(self):
        response = {"id": "999", "project": "p"}
        backup = SQLBackupRun.from_api_response(response)

        assert backup.id == "999"
        assert backup.status == ""
        assert backup.start_time is None
        assert backup.end_time is None
        assert backup.disk_encryption_status is None
        assert backup.location is None


class TestCloudSQLServiceInstances:
    """Tests for instance-related methods."""

    def test_list_instances(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.instances.return_value = mock_instances
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {
            "items": [SAMPLE_INSTANCE_RESPONSE],
        }

        service = CloudSQLService(project_id="test-project")
        results = service.list_instances()

        mock_instances.list.assert_called_once_with(project="test-project")
        assert len(results) == 1
        assert isinstance(results[0], SQLInstance)
        assert results[0].name == "my-instance"
        assert results[0].database_version == "POSTGRES_15"

    def test_list_instances_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.instances.return_value = mock_instances
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = CloudSQLService(project_id="test-project")
        results = service.list_instances()

        assert results == []

    def test_list_instances_with_kwargs(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.instances.return_value = mock_instances
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {"items": []}

        service = CloudSQLService(project_id="test-project")
        service.list_instances(filter="state:RUNNABLE")

        mock_instances.list.assert_called_once_with(
            project="test-project", filter="state:RUNNABLE"
        )

    def test_get_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.instances.return_value = mock_instances
        mock_get = mock.MagicMock()
        mock_instances.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = CloudSQLService(project_id="test-project")
        result = service.get_instance("my-instance")

        mock_instances.get.assert_called_once_with(
            project="test-project", instance="my-instance"
        )
        assert isinstance(result, SQLInstance)
        assert result.name == "my-instance"
        assert result.state == "RUNNABLE"

    def test_create_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.instances.return_value = mock_instances
        mock_insert = mock.MagicMock()
        mock_instances.insert.return_value = mock_insert
        mock_insert.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = CloudSQLService(project_id="test-project")
        result = service.create_instance(
            instance_name="my-instance",
            database_version="POSTGRES_15",
            tier="db-n1-standard-1",
            region="us-central1",
            labels={"env": "test"},
        )

        mock_instances.insert.assert_called_once_with(
            project="test-project",
            body={
                "name": "my-instance",
                "databaseVersion": "POSTGRES_15",
                "region": "us-central1",
                "settings": {
                    "tier": "db-n1-standard-1",
                    "userLabels": {"env": "test"},
                },
            },
        )
        assert isinstance(result, SQLInstance)
        assert result.name == "my-instance"

    def test_create_instance_with_settings(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.instances.return_value = mock_instances
        mock_insert = mock.MagicMock()
        mock_instances.insert.return_value = mock_insert
        mock_insert.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = CloudSQLService(project_id="test-project")
        service.create_instance(
            instance_name="my-instance",
            database_version="POSTGRES_15",
            tier="db-n1-standard-1",
            region="us-central1",
            settings={"availabilityType": "REGIONAL"},
        )

        call_args = mock_instances.insert.call_args
        body = call_args[1]["body"]
        assert body["settings"]["availabilityType"] == "REGIONAL"
        assert body["settings"]["tier"] == "db-n1-standard-1"

    def test_create_instance_no_labels(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.instances.return_value = mock_instances
        mock_insert = mock.MagicMock()
        mock_instances.insert.return_value = mock_insert
        mock_insert.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = CloudSQLService(project_id="test-project")
        service.create_instance(
            instance_name="my-instance",
            database_version="MYSQL_8_0",
            tier="db-f1-micro",
            region="us-central1",
        )

        call_args = mock_instances.insert.call_args
        body = call_args[1]["body"]
        assert "userLabels" not in body["settings"]

    def test_delete_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.instances.return_value = mock_instances
        mock_delete = mock.MagicMock()
        mock_instances.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = CloudSQLService(project_id="test-project")
        result = service.delete_instance("my-instance")

        mock_instances.delete.assert_called_once_with(
            project="test-project", instance="my-instance"
        )
        mock_delete.execute.assert_called_once()
        assert result is True

    def test_restart_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = mock.MagicMock()
        mock_service.instances.return_value = mock_instances
        mock_restart = mock.MagicMock()
        mock_instances.restart.return_value = mock_restart
        operation_response = {"name": "operation-123", "status": "PENDING"}
        mock_restart.execute.return_value = operation_response

        service = CloudSQLService(project_id="test-project")
        result = service.restart_instance("my-instance")

        mock_instances.restart.assert_called_once_with(
            project="test-project", instance="my-instance"
        )
        assert result == operation_response


class TestCloudSQLServiceDatabases:
    """Tests for database-related methods."""

    def test_list_databases(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_databases = mock.MagicMock()
        mock_service.databases.return_value = mock_databases
        mock_list = mock.MagicMock()
        mock_databases.list.return_value = mock_list
        mock_list.execute.return_value = {
            "items": [SAMPLE_DATABASE_RESPONSE],
        }

        service = CloudSQLService(project_id="test-project")
        results = service.list_databases("my-instance")

        mock_databases.list.assert_called_once_with(
            project="test-project", instance="my-instance"
        )
        assert len(results) == 1
        assert isinstance(results[0], SQLDatabase)
        assert results[0].name == "mydb"
        assert results[0].charset == "UTF8"

    def test_list_databases_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_databases = mock.MagicMock()
        mock_service.databases.return_value = mock_databases
        mock_list = mock.MagicMock()
        mock_databases.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = CloudSQLService(project_id="test-project")
        results = service.list_databases("my-instance")

        assert results == []

    def test_get_database(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_databases = mock.MagicMock()
        mock_service.databases.return_value = mock_databases
        mock_get = mock.MagicMock()
        mock_databases.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_DATABASE_RESPONSE

        service = CloudSQLService(project_id="test-project")
        result = service.get_database("my-instance", "mydb")

        mock_databases.get.assert_called_once_with(
            project="test-project",
            instance="my-instance",
            database="mydb",
        )
        assert isinstance(result, SQLDatabase)
        assert result.name == "mydb"
        assert result.instance_name == "my-instance"

    def test_create_database(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_databases = mock.MagicMock()
        mock_service.databases.return_value = mock_databases
        mock_insert = mock.MagicMock()
        mock_databases.insert.return_value = mock_insert
        mock_insert.execute.return_value = SAMPLE_DATABASE_RESPONSE

        service = CloudSQLService(project_id="test-project")
        result = service.create_database(
            "my-instance", "mydb", charset="UTF8", collation="en_US.UTF8"
        )

        mock_databases.insert.assert_called_once_with(
            project="test-project",
            instance="my-instance",
            body={
                "name": "mydb",
                "instance": "my-instance",
                "charset": "UTF8",
                "collation": "en_US.UTF8",
            },
        )
        assert isinstance(result, SQLDatabase)
        assert result.name == "mydb"

    def test_create_database_defaults(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_databases = mock.MagicMock()
        mock_service.databases.return_value = mock_databases
        mock_insert = mock.MagicMock()
        mock_databases.insert.return_value = mock_insert
        mock_insert.execute.return_value = SAMPLE_DATABASE_RESPONSE

        service = CloudSQLService(project_id="test-project")
        service.create_database("my-instance", "mydb")

        call_args = mock_databases.insert.call_args
        body = call_args[1]["body"]
        assert body["charset"] == "UTF8"
        assert body["collation"] == ""

    def test_delete_database(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_databases = mock.MagicMock()
        mock_service.databases.return_value = mock_databases
        mock_delete = mock.MagicMock()
        mock_databases.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = CloudSQLService(project_id="test-project")
        result = service.delete_database("my-instance", "mydb")

        mock_databases.delete.assert_called_once_with(
            project="test-project",
            instance="my-instance",
            database="mydb",
        )
        mock_delete.execute.assert_called_once()
        assert result is True


class TestCloudSQLServiceUsers:
    """Tests for user-related methods."""

    def test_list_users(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_users = mock.MagicMock()
        mock_service.users.return_value = mock_users
        mock_list = mock.MagicMock()
        mock_users.list.return_value = mock_list
        mock_list.execute.return_value = {
            "items": [SAMPLE_USER_RESPONSE],
        }

        service = CloudSQLService(project_id="test-project")
        results = service.list_users("my-instance")

        mock_users.list.assert_called_once_with(
            project="test-project", instance="my-instance"
        )
        assert len(results) == 1
        assert isinstance(results[0], SQLUser)
        assert results[0].name == "admin"
        assert results[0].password_set is True

    def test_list_users_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_users = mock.MagicMock()
        mock_service.users.return_value = mock_users
        mock_list = mock.MagicMock()
        mock_users.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = CloudSQLService(project_id="test-project")
        results = service.list_users("my-instance")

        assert results == []

    def test_create_user(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_users = mock.MagicMock()
        mock_service.users.return_value = mock_users
        mock_insert = mock.MagicMock()
        mock_users.insert.return_value = mock_insert
        mock_insert.execute.return_value = SAMPLE_USER_RESPONSE

        service = CloudSQLService(project_id="test-project")
        result = service.create_user(
            "my-instance", "admin", "secret123", host="%"
        )

        mock_users.insert.assert_called_once_with(
            project="test-project",
            instance="my-instance",
            body={
                "name": "admin",
                "instance": "my-instance",
                "password": "secret123",
                "host": "%",
            },
        )
        assert isinstance(result, SQLUser)
        assert result.name == "admin"

    def test_create_user_default_host(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_users = mock.MagicMock()
        mock_service.users.return_value = mock_users
        mock_insert = mock.MagicMock()
        mock_users.insert.return_value = mock_insert
        mock_insert.execute.return_value = SAMPLE_USER_RESPONSE

        service = CloudSQLService(project_id="test-project")
        service.create_user("my-instance", "admin", "secret123")

        call_args = mock_users.insert.call_args
        body = call_args[1]["body"]
        assert body["host"] == "%"

    def test_delete_user(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_users = mock.MagicMock()
        mock_service.users.return_value = mock_users
        mock_delete = mock.MagicMock()
        mock_users.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = CloudSQLService(project_id="test-project")
        result = service.delete_user("my-instance", "admin")

        mock_users.delete.assert_called_once_with(
            project="test-project",
            instance="my-instance",
            name="admin",
            host="%",
        )
        mock_delete.execute.assert_called_once()
        assert result is True

    def test_delete_user_custom_host(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_users = mock.MagicMock()
        mock_service.users.return_value = mock_users
        mock_delete = mock.MagicMock()
        mock_users.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = CloudSQLService(project_id="test-project")
        service.delete_user("my-instance", "admin", host="localhost")

        mock_users.delete.assert_called_once_with(
            project="test-project",
            instance="my-instance",
            name="admin",
            host="localhost",
        )


class TestCloudSQLServiceBackups:
    """Tests for backup-related methods."""

    def test_list_backup_runs(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_backups = mock.MagicMock()
        mock_service.backupRuns.return_value = mock_backups
        mock_list = mock.MagicMock()
        mock_backups.list.return_value = mock_list
        mock_list.execute.return_value = {
            "items": [SAMPLE_BACKUP_RUN_RESPONSE],
        }

        service = CloudSQLService(project_id="test-project")
        results = service.list_backup_runs("my-instance")

        mock_backups.list.assert_called_once_with(
            project="test-project", instance="my-instance"
        )
        assert len(results) == 1
        assert isinstance(results[0], SQLBackupRun)
        assert results[0].status == "SUCCESSFUL"
        assert results[0].backup_kind == "SNAPSHOT"
        assert results[0].location == "us"

    def test_list_backup_runs_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_backups = mock.MagicMock()
        mock_service.backupRuns.return_value = mock_backups
        mock_list = mock.MagicMock()
        mock_backups.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = CloudSQLService(project_id="test-project")
        results = service.list_backup_runs("my-instance")

        assert results == []

    def test_list_backup_runs_multiple(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_backups = mock.MagicMock()
        mock_service.backupRuns.return_value = mock_backups
        mock_list = mock.MagicMock()
        mock_backups.list.return_value = mock_list

        second_backup = {
            "id": "9999999",
            "instance": "my-instance",
            "project": "test-project",
            "status": "FAILED",
            "backupKind": "SNAPSHOT",
        }
        mock_list.execute.return_value = {
            "items": [SAMPLE_BACKUP_RUN_RESPONSE, second_backup],
        }

        service = CloudSQLService(project_id="test-project")
        results = service.list_backup_runs("my-instance")

        assert len(results) == 2
        assert results[0].status == "SUCCESSFUL"
        assert results[1].status == "FAILED"
