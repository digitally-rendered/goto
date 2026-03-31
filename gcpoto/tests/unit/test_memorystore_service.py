"""Tests for the Memorystore (Redis) service implementation."""

import unittest.mock as mock
import pytest

from gcpoto.services.memorystore import MemorystoreService
from gcpoto.models.memorystore import RedisInstance
from gcpoto.exceptions import ResourceNotFoundError, APIError


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


SAMPLE_INSTANCE_RESPONSE = {
    "name": "projects/test-project/locations/us-central1/instances/my-redis",
    "displayName": "My Redis Instance",
    "tier": "STANDARD_HA",
    "memorySizeGb": 4,
    "host": "10.0.0.5",
    "port": 6379,
    "currentLocationId": "us-central1-a",
    "redisVersion": "REDIS_7_0",
    "state": "READY",
    "statusMessage": "Instance is running",
    "redisConfigs": {"maxmemory-policy": "allkeys-lru"},
    "authorizedNetwork": "projects/test-project/global/networks/default",
    "connectMode": "DIRECT_PEERING",
    "authEnabled": True,
    "transitEncryptionMode": "SERVER_AUTHENTICATION",
    "maintenancePolicy": {
        "description": "weekly maintenance",
        "weeklyMaintenanceWindow": [
            {
                "day": "TUESDAY",
                "startTime": {"hours": 2, "minutes": 0},
                "duration": "3600s",
            }
        ],
    },
    "maintenanceSchedule": {
        "startTime": "2026-04-01T02:00:00Z",
        "endTime": "2026-04-01T03:00:00Z",
        "canReschedule": True,
    },
    "labels": {"env": "test", "team": "backend"},
    "createTime": "2026-01-01T00:00:00Z",
    "updateTime": "2026-03-15T12:00:00Z",
}


SAMPLE_OPERATION_RESPONSE = {
    "name": "projects/test-project/locations/us-central1/operations/operation-123",
    "done": False,
}


class TestMemorystoreServiceInit:
    """Tests for MemorystoreService initialization."""

    def test_initialization(self, mock_discovery):
        mock_build, _ = mock_discovery
        service = MemorystoreService(
            project_id="test-project", credentials_file=None
        )

        assert service.project_id == "test-project"
        assert service.service_name == "redis"
        assert service.version == "v1"
        assert service.credentials_file is None
        assert service.resource_model == RedisInstance
        mock_build.assert_called_once_with("redis", "v1", credentials=None)

    def test_initialization_with_credentials(self, mock_discovery):
        mock_build, _ = mock_discovery
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            service = MemorystoreService(
                project_id="test-project",
                credentials_file="/path/to/creds.json",
            )
            assert service.credentials_file == "/path/to/creds.json"


class TestRedisInstanceModel:
    """Tests for the RedisInstance model."""

    def test_from_api_response(self):
        instance = RedisInstance.from_api_response(SAMPLE_INSTANCE_RESPONSE)

        assert instance.id == "my-redis"
        assert instance.name == "projects/test-project/locations/us-central1/instances/my-redis"
        assert instance.type == "redis.instance"
        assert instance.project == "test-project"
        assert instance.location == "us-central1"
        assert instance.display_name == "My Redis Instance"
        assert instance.tier == "STANDARD_HA"
        assert instance.memory_size_gb == 4
        assert instance.host == "10.0.0.5"
        assert instance.port == 6379
        assert instance.current_location_id == "us-central1-a"
        assert instance.redis_version == "REDIS_7_0"
        assert instance.state == "READY"
        assert instance.status_message == "Instance is running"
        assert instance.redis_configs == {"maxmemory-policy": "allkeys-lru"}
        assert instance.authorized_network == "projects/test-project/global/networks/default"
        assert instance.connect_mode == "DIRECT_PEERING"
        assert instance.auth_enabled is True
        assert instance.transit_encryption_mode == "SERVER_AUTHENTICATION"
        assert instance.maintenance_policy is not None
        assert instance.maintenance_schedule is not None
        assert instance.labels == {"env": "test", "team": "backend"}
        assert instance.created.isoformat().startswith("2026-01-01T00:00:00")
        assert instance.updated.isoformat().startswith("2026-03-15T12:00:00")

    def test_from_api_response_minimal(self):
        response = {
            "name": "projects/p/locations/us-east1/instances/bare",
            "tier": "BASIC",
            "memorySizeGb": 1,
            "state": "CREATING",
        }
        instance = RedisInstance.from_api_response(response)

        assert instance.id == "bare"
        assert instance.project == "p"
        assert instance.location == "us-east1"
        assert instance.tier == "BASIC"
        assert instance.memory_size_gb == 1
        assert instance.state == "CREATING"
        assert instance.display_name is None
        assert instance.host is None
        assert instance.port is None
        assert instance.current_location_id is None
        assert instance.redis_version is None
        assert instance.status_message is None
        assert instance.redis_configs is None
        assert instance.authorized_network is None
        assert instance.connect_mode is None
        assert instance.auth_enabled is False
        assert instance.transit_encryption_mode is None
        assert instance.maintenance_policy is None
        assert instance.maintenance_schedule is None

    def test_from_api_response_no_name_slashes(self):
        response = {
            "name": "simple-name",
            "tier": "BASIC",
            "memorySizeGb": 1,
            "state": "READY",
        }
        instance = RedisInstance.from_api_response(response)
        assert instance.id == "simple-name"
        assert instance.location == ""
        assert instance.project == ""

    def test_get_tag(self):
        instance = RedisInstance.from_api_response(SAMPLE_INSTANCE_RESPONSE)
        assert instance.get_tag("env") == "test"
        assert instance.get_tag("team") == "backend"
        assert instance.get_tag("missing") == ""
        assert instance.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        response = {
            "name": "projects/p/locations/us-east1/instances/bare",
            "tier": "BASIC",
            "memorySizeGb": 1,
            "state": "READY",
        }
        instance = RedisInstance.from_api_response(response)
        assert instance.get_tag("env") == ""
        assert instance.get_tag("env", "fallback") == "fallback"

    def test_to_dict(self):
        instance = RedisInstance.from_api_response(SAMPLE_INSTANCE_RESPONSE)
        d = instance.to_dict()
        assert d["id"] == "my-redis"
        assert d["tier"] == "STANDARD_HA"
        assert d["memory_size_gb"] == 4
        assert d["auth_enabled"] is True


def _get_instances_mock(mock_service):
    """Helper to set up the chained mock for instances()."""
    mock_projects = mock.MagicMock()
    mock_service.projects.return_value = mock_projects
    mock_locations = mock.MagicMock()
    mock_projects.locations.return_value = mock_locations
    mock_instances = mock.MagicMock()
    mock_locations.instances.return_value = mock_instances
    return mock_instances


class TestMemorystoreServiceListInstances:
    """Tests for listing Redis instances."""

    def test_list_instances(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {
            "instances": [SAMPLE_INSTANCE_RESPONSE],
        }

        service = MemorystoreService(project_id="test-project")
        results = service.list_instances()

        mock_instances.list.assert_called_once_with(
            parent="projects/test-project/locations/-"
        )
        assert len(results) == 1
        assert isinstance(results[0], RedisInstance)
        assert results[0].id == "my-redis"
        assert results[0].tier == "STANDARD_HA"

    def test_list_instances_specific_location(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {"instances": []}

        service = MemorystoreService(project_id="test-project")
        results = service.list_instances(location="us-central1")

        mock_instances.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )
        assert results == []

    def test_list_instances_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list
        mock_list.execute.return_value = {}

        service = MemorystoreService(project_id="test-project")
        results = service.list_instances()

        assert results == []

    def test_list_instances_multiple(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_instances.list.return_value = mock_list

        second_instance = {
            "name": "projects/test-project/locations/us-east1/instances/redis-2",
            "tier": "BASIC",
            "memorySizeGb": 1,
            "state": "READY",
        }
        mock_list.execute.return_value = {
            "instances": [SAMPLE_INSTANCE_RESPONSE, second_instance],
        }

        service = MemorystoreService(project_id="test-project")
        results = service.list_instances()

        assert len(results) == 2
        assert results[0].id == "my-redis"
        assert results[1].id == "redis-2"
        assert results[1].tier == "BASIC"


class TestMemorystoreServiceGetInstance:
    """Tests for getting a specific Redis instance."""

    def test_get_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_instances.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_INSTANCE_RESPONSE

        service = MemorystoreService(project_id="test-project")
        result = service.get_instance("us-central1", "my-redis")

        mock_instances.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/instances/my-redis"
        )
        assert isinstance(result, RedisInstance)
        assert result.id == "my-redis"
        assert result.state == "READY"
        assert result.memory_size_gb == 4

    def test_get_instance_not_found(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_instances.get.return_value = mock_get
        mock_get.execute.side_effect = Exception(
            "HttpError 404: Resource not found"
        )

        service = MemorystoreService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError) as exc_info:
            service.get_instance("us-central1", "nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_get_instance_api_error(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_instances.get.return_value = mock_get
        mock_get.execute.side_effect = Exception("Internal server error")

        service = MemorystoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.get_instance("us-central1", "my-redis")


class TestMemorystoreServiceCreateInstance:
    """Tests for creating a Redis instance."""

    def test_create_instance_minimal(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_instances.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_OPERATION_RESPONSE

        service = MemorystoreService(project_id="test-project")
        result = service.create_instance(
            location="us-central1",
            instance_id="my-redis",
            tier="BASIC",
            memory_size_gb=1,
        )

        mock_instances.create.assert_called_once_with(
            parent="projects/test-project/locations/us-central1",
            instanceId="my-redis",
            body={
                "tier": "BASIC",
                "memorySizeGb": 1,
            },
        )
        assert result == SAMPLE_OPERATION_RESPONSE

    def test_create_instance_full(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_instances.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_OPERATION_RESPONSE

        service = MemorystoreService(project_id="test-project")
        result = service.create_instance(
            location="us-central1",
            instance_id="my-redis",
            tier="STANDARD_HA",
            memory_size_gb=4,
            redis_version="REDIS_7_0",
            display_name="My Redis",
            authorized_network="projects/test-project/global/networks/default",
            redis_configs={"maxmemory-policy": "allkeys-lru"},
            labels={"env": "prod"},
        )

        call_args = mock_instances.create.call_args
        body = call_args[1]["body"]
        assert body["tier"] == "STANDARD_HA"
        assert body["memorySizeGb"] == 4
        assert body["redisVersion"] == "REDIS_7_0"
        assert body["displayName"] == "My Redis"
        assert body["authorizedNetwork"] == "projects/test-project/global/networks/default"
        assert body["redisConfigs"] == {"maxmemory-policy": "allkeys-lru"}
        assert body["labels"] == {"env": "prod"}
        assert result == SAMPLE_OPERATION_RESPONSE

    def test_create_instance_no_optional_fields(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_instances.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_OPERATION_RESPONSE

        service = MemorystoreService(project_id="test-project")
        service.create_instance(
            location="us-central1",
            instance_id="my-redis",
            tier="BASIC",
            memory_size_gb=1,
        )

        call_args = mock_instances.create.call_args
        body = call_args[1]["body"]
        assert "redisVersion" not in body
        assert "displayName" not in body
        assert "authorizedNetwork" not in body
        assert "redisConfigs" not in body
        assert "labels" not in body


class TestMemorystoreServiceUpdateInstance:
    """Tests for updating a Redis instance."""

    def test_update_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_patch = mock.MagicMock()
        mock_instances.patch.return_value = mock_patch
        mock_patch.execute.return_value = SAMPLE_OPERATION_RESPONSE

        service = MemorystoreService(project_id="test-project")
        result = service.update_instance(
            location="us-central1",
            instance_id="my-redis",
            update_mask="memorySizeGb,displayName",
            update_fields={
                "memorySizeGb": 8,
                "displayName": "Updated Redis",
            },
        )

        mock_instances.patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/instances/my-redis",
            updateMask="memorySizeGb,displayName",
            body={
                "memorySizeGb": 8,
                "displayName": "Updated Redis",
            },
        )
        assert result == SAMPLE_OPERATION_RESPONSE

    def test_update_instance_single_field(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_patch = mock.MagicMock()
        mock_instances.patch.return_value = mock_patch
        mock_patch.execute.return_value = SAMPLE_OPERATION_RESPONSE

        service = MemorystoreService(project_id="test-project")
        service.update_instance(
            location="us-central1",
            instance_id="my-redis",
            update_mask="memorySizeGb",
            update_fields={"memorySizeGb": 16},
        )

        call_args = mock_instances.patch.call_args
        assert call_args[1]["updateMask"] == "memorySizeGb"
        assert call_args[1]["body"] == {"memorySizeGb": 16}


class TestMemorystoreServiceDeleteInstance:
    """Tests for deleting a Redis instance."""

    def test_delete_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_delete = mock.MagicMock()
        mock_instances.delete.return_value = mock_delete
        mock_delete.execute.return_value = SAMPLE_OPERATION_RESPONSE

        service = MemorystoreService(project_id="test-project")
        result = service.delete_instance("us-central1", "my-redis")

        mock_instances.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/instances/my-redis"
        )
        mock_delete.execute.assert_called_once()
        assert result == SAMPLE_OPERATION_RESPONSE


class TestMemorystoreServiceUpgradeInstance:
    """Tests for upgrading a Redis instance."""

    def test_upgrade_instance(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_upgrade = mock.MagicMock()
        mock_instances.upgrade.return_value = mock_upgrade
        mock_upgrade.execute.return_value = SAMPLE_OPERATION_RESPONSE

        service = MemorystoreService(project_id="test-project")
        result = service.upgrade_instance(
            "us-central1", "my-redis", "REDIS_7_2"
        )

        mock_instances.upgrade.assert_called_once_with(
            name="projects/test-project/locations/us-central1/instances/my-redis",
            body={"redisVersion": "REDIS_7_2"},
        )
        assert result == SAMPLE_OPERATION_RESPONSE


class TestMemorystoreServiceFailoverInstance:
    """Tests for initiating a failover of a Redis instance."""

    def test_failover_instance_default_mode(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_failover = mock.MagicMock()
        mock_instances.failover.return_value = mock_failover
        mock_failover.execute.return_value = SAMPLE_OPERATION_RESPONSE

        service = MemorystoreService(project_id="test-project")
        result = service.failover_instance("us-central1", "my-redis")

        mock_instances.failover.assert_called_once_with(
            name="projects/test-project/locations/us-central1/instances/my-redis",
            body={"dataProtectionMode": "LIMITED_DATA_LOSS"},
        )
        assert result == SAMPLE_OPERATION_RESPONSE

    def test_failover_instance_force_mode(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_failover = mock.MagicMock()
        mock_instances.failover.return_value = mock_failover
        mock_failover.execute.return_value = SAMPLE_OPERATION_RESPONSE

        service = MemorystoreService(project_id="test-project")
        result = service.failover_instance(
            "us-central1", "my-redis", data_protection_mode="FORCE_DATA_LOSS"
        )

        call_args = mock_instances.failover.call_args
        assert call_args[1]["body"]["dataProtectionMode"] == "FORCE_DATA_LOSS"
        assert result == SAMPLE_OPERATION_RESPONSE


class TestMemorystoreServiceGetAuthString:
    """Tests for getting the AUTH string of a Redis instance."""

    def test_get_instance_auth_string(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_get_auth = mock.MagicMock()
        mock_instances.getAuthString.return_value = mock_get_auth
        mock_get_auth.execute.return_value = {
            "authString": "super-secret-auth-string"
        }

        service = MemorystoreService(project_id="test-project")
        result = service.get_instance_auth_string("us-central1", "my-redis")

        mock_instances.getAuthString.assert_called_once_with(
            name="projects/test-project/locations/us-central1/instances/my-redis"
        )
        assert result == "super-secret-auth-string"

    def test_get_instance_auth_string_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_instances = _get_instances_mock(mock_service)
        mock_get_auth = mock.MagicMock()
        mock_instances.getAuthString.return_value = mock_get_auth
        mock_get_auth.execute.return_value = {}

        service = MemorystoreService(project_id="test-project")
        result = service.get_instance_auth_string("us-central1", "my-redis")

        assert result == ""


class TestMemorystoreServicePaths:
    """Tests for path formatting helper methods."""

    def test_instance_path(self, mock_discovery):
        _, _ = mock_discovery
        service = MemorystoreService(project_id="test-project")
        path = service._instance_path("us-central1", "my-redis")
        assert path == "projects/test-project/locations/us-central1/instances/my-redis"

    def test_location_path(self, mock_discovery):
        _, _ = mock_discovery
        service = MemorystoreService(project_id="test-project")
        path = service._location_path("us-central1")
        assert path == "projects/test-project/locations/us-central1"

    def test_location_path_all(self, mock_discovery):
        _, _ = mock_discovery
        service = MemorystoreService(project_id="test-project")
        path = service._location_path("-")
        assert path == "projects/test-project/locations/-"
