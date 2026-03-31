"""Tests for Datastore service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.datastore import DatastoreService
from gcpoto.models.datastore import Entity, EntityResult
from gcpoto.exceptions import APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects

        yield mock_service


@pytest.fixture
def sample_entity_response():
    """Sample Datastore entity API response."""
    return {
        "key": {
            "partitionId": {"projectId": "test-project"},
            "path": [{"kind": "Task", "id": "123"}],
        },
        "properties": {
            "title": {"stringValue": "Buy milk"},
            "done": {"booleanValue": False},
        },
    }


@pytest.fixture
def sample_entity_result_response(sample_entity_response):
    """Sample Datastore entity result API response."""
    return {
        "entity": sample_entity_response,
        "cursor": "abc123cursor",
    }


# --- Model tests ---


class TestEntityModel:
    def test_from_api_response(self, sample_entity_response):
        entity = Entity.from_api_response(sample_entity_response, "test-project")
        assert entity.kind == "Task"
        assert entity.id == "123"
        assert entity.project == "test-project"
        assert entity.type == "datastore.entity"
        assert entity.properties["title"] == {"stringValue": "Buy milk"}
        assert entity.key == sample_entity_response["key"]

    def test_from_api_response_extracts_project(self, sample_entity_response):
        entity = Entity.from_api_response(sample_entity_response)
        assert entity.project == "test-project"

    def test_from_api_response_with_name_key(self):
        response = {
            "key": {
                "partitionId": {"projectId": "p"},
                "path": [{"kind": "Config", "name": "main"}],
            },
            "properties": {},
        }
        entity = Entity.from_api_response(response, "p")
        assert entity.kind == "Config"
        assert entity.id == "main"

    def test_from_api_response_minimal(self):
        entity = Entity.from_api_response({"key": {}, "properties": {}}, "p")
        assert entity.kind == ""
        assert entity.id == ""
        assert entity.properties == {}

    def test_get_tag_default(self, sample_entity_response):
        entity = Entity.from_api_response(sample_entity_response, "test-project")
        assert entity.get_tag("missing") == ""
        assert entity.get_tag("missing", "fallback") == "fallback"


class TestEntityResultModel:
    def test_from_api_response(self, sample_entity_result_response):
        result = EntityResult.from_api_response(
            sample_entity_result_response, "test-project"
        )
        assert result.cursor == "abc123cursor"
        assert result.entity["key"]["path"][0]["kind"] == "Task"
        assert result.project == "test-project"
        assert result.type == "datastore.entityResult"

    def test_from_api_response_no_cursor(self, sample_entity_response):
        response = {"entity": sample_entity_response}
        result = EntityResult.from_api_response(response, "test-project")
        assert result.cursor is None

    def test_from_api_response_extracts_project(
        self, sample_entity_result_response
    ):
        result = EntityResult.from_api_response(sample_entity_result_response)
        assert result.project == "test-project"


# --- Service init tests ---


class TestDatastoreServiceInit:
    def test_init(self, mock_google_client):
        from googleapiclient.discovery import build

        service = DatastoreService(project_id="test-project")
        assert service.project_id == "test-project"
        build.assert_called_once_with("datastore", "v1", credentials=None)


# --- Lookup tests ---


class TestLookup:
    def test_lookup(
        self, mock_google_client, sample_entity_result_response
    ):
        mock_request = mock.MagicMock()
        mock_lookup = mock_google_client.projects.return_value.lookup
        mock_lookup.return_value = mock_request
        mock_request.execute.return_value = {
            "found": [sample_entity_result_response]
        }

        service = DatastoreService(project_id="test-project")
        keys = [
            {
                "partitionId": {"projectId": "test-project"},
                "path": [{"kind": "Task", "id": "123"}],
            }
        ]
        results = service.lookup(keys)

        mock_lookup.assert_called_once_with(
            projectId="test-project", body={"keys": keys}
        )
        assert len(results) == 1
        assert isinstance(results[0], EntityResult)
        assert results[0].cursor == "abc123cursor"

    def test_lookup_not_found(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_lookup = mock_google_client.projects.return_value.lookup
        mock_lookup.return_value = mock_request
        mock_request.execute.return_value = {}

        service = DatastoreService(project_id="test-project")
        results = service.lookup([{"path": [{"kind": "Task", "id": "999"}]}])
        assert results == []

    def test_lookup_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_lookup = mock_google_client.projects.return_value.lookup
        mock_lookup.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = DatastoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.lookup([{"path": [{"kind": "Task", "id": "123"}]}])


# --- Run query tests ---


class TestRunQuery:
    def test_run_query_simple(
        self, mock_google_client, sample_entity_result_response
    ):
        mock_request = mock.MagicMock()
        mock_run_query = mock_google_client.projects.return_value.runQuery
        mock_run_query.return_value = mock_request
        mock_request.execute.return_value = {
            "batch": {
                "entityResults": [sample_entity_result_response],
            }
        }

        service = DatastoreService(project_id="test-project")
        results = service.run_query("Task")

        call_args = mock_run_query.call_args
        body = call_args[1]["body"]
        assert body["query"]["kind"] == [{"name": "Task"}]
        assert len(results) == 1
        assert isinstance(results[0], EntityResult)

    def test_run_query_with_filters(
        self, mock_google_client, sample_entity_result_response
    ):
        mock_request = mock.MagicMock()
        mock_run_query = mock_google_client.projects.return_value.runQuery
        mock_run_query.return_value = mock_request
        mock_request.execute.return_value = {
            "batch": {"entityResults": [sample_entity_result_response]}
        }

        service = DatastoreService(project_id="test-project")
        filters = [
            {
                "property": {"name": "done"},
                "op": "EQUAL",
                "value": {"booleanValue": False},
            }
        ]
        results = service.run_query("Task", filters=filters)

        call_args = mock_run_query.call_args
        body = call_args[1]["body"]
        assert "propertyFilter" in body["query"]["filter"]
        assert len(results) == 1

    def test_run_query_with_multiple_filters(
        self, mock_google_client, sample_entity_result_response
    ):
        mock_request = mock.MagicMock()
        mock_run_query = mock_google_client.projects.return_value.runQuery
        mock_run_query.return_value = mock_request
        mock_request.execute.return_value = {
            "batch": {"entityResults": [sample_entity_result_response]}
        }

        service = DatastoreService(project_id="test-project")
        filters = [
            {
                "property": {"name": "done"},
                "op": "EQUAL",
                "value": {"booleanValue": False},
            },
            {
                "property": {"name": "priority"},
                "op": "GREATER_THAN",
                "value": {"integerValue": "3"},
            },
        ]
        results = service.run_query("Task", filters=filters)

        call_args = mock_run_query.call_args
        body = call_args[1]["body"]
        composite = body["query"]["filter"]["compositeFilter"]
        assert composite["op"] == "AND"
        assert len(composite["filters"]) == 2
        assert len(results) == 1

    def test_run_query_with_order_and_limit(
        self, mock_google_client, sample_entity_result_response
    ):
        mock_request = mock.MagicMock()
        mock_run_query = mock_google_client.projects.return_value.runQuery
        mock_run_query.return_value = mock_request
        mock_request.execute.return_value = {
            "batch": {"entityResults": [sample_entity_result_response]}
        }

        service = DatastoreService(project_id="test-project")
        results = service.run_query(
            "Task",
            order=[{"property": "priority", "direction": "DESCENDING"}],
            limit=10,
        )

        call_args = mock_run_query.call_args
        body = call_args[1]["body"]
        assert body["query"]["order"][0]["direction"] == "DESCENDING"
        assert body["query"]["limit"] == 10
        assert len(results) == 1

    def test_run_query_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_run_query = mock_google_client.projects.return_value.runQuery
        mock_run_query.return_value = mock_request
        mock_request.execute.return_value = {"batch": {}}

        service = DatastoreService(project_id="test-project")
        results = service.run_query("Task")
        assert results == []

    def test_run_query_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_run_query = mock_google_client.projects.return_value.runQuery
        mock_run_query.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        service = DatastoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.run_query("Task")


# --- Upsert tests ---


class TestUpsert:
    def test_upsert(self, mock_google_client, sample_entity_response):
        mock_request = mock.MagicMock()
        mock_commit = mock_google_client.projects.return_value.commit
        mock_commit.return_value = mock_request
        mock_request.execute.return_value = {
            "mutationResults": [
                {"key": sample_entity_response["key"]}
            ]
        }

        service = DatastoreService(project_id="test-project")
        results = service.upsert([sample_entity_response])

        call_args = mock_commit.call_args
        body = call_args[1]["body"]
        assert len(body["mutations"]) == 1
        assert "upsert" in body["mutations"][0]
        assert len(results) == 1
        assert isinstance(results[0], Entity)

    def test_upsert_api_error(self, mock_google_client, sample_entity_response):
        mock_request = mock.MagicMock()
        mock_commit = mock_google_client.projects.return_value.commit
        mock_commit.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = DatastoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.upsert([sample_entity_response])


# --- Delete tests ---


class TestDelete:
    def test_delete(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_commit = mock_google_client.projects.return_value.commit
        mock_commit.return_value = mock_request
        mock_request.execute.return_value = {"mutationResults": [{}]}

        service = DatastoreService(project_id="test-project")
        keys = [
            {
                "partitionId": {"projectId": "test-project"},
                "path": [{"kind": "Task", "id": "123"}],
            }
        ]
        result = service.delete(keys)

        call_args = mock_commit.call_args
        body = call_args[1]["body"]
        assert len(body["mutations"]) == 1
        assert "delete" in body["mutations"][0]
        assert result is True

    def test_delete_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_commit = mock_google_client.projects.return_value.commit
        mock_commit.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = DatastoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.delete([{"path": [{"kind": "Task", "id": "123"}]}])


# --- Allocate IDs tests ---


class TestAllocateIds:
    def test_allocate_ids(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_allocate = mock_google_client.projects.return_value.allocateIds
        mock_allocate.return_value = mock_request
        mock_request.execute.return_value = {
            "keys": [
                {
                    "partitionId": {"projectId": "test-project"},
                    "path": [{"kind": "Task", "id": "100"}],
                },
                {
                    "partitionId": {"projectId": "test-project"},
                    "path": [{"kind": "Task", "id": "101"}],
                },
            ]
        }

        service = DatastoreService(project_id="test-project")
        keys = service.allocate_ids("Task", 2)

        call_args = mock_allocate.call_args
        body = call_args[1]["body"]
        assert len(body["keys"]) == 2
        assert body["keys"][0]["path"][0]["kind"] == "Task"
        assert len(keys) == 2

    def test_allocate_ids_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_allocate = mock_google_client.projects.return_value.allocateIds
        mock_allocate.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = DatastoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.allocate_ids("Task", 1)


# --- Begin transaction tests ---


class TestBeginTransaction:
    def test_begin_transaction(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_begin = mock_google_client.projects.return_value.beginTransaction
        mock_begin.return_value = mock_request
        mock_request.execute.return_value = {"transaction": "txn-abc-123"}

        service = DatastoreService(project_id="test-project")
        txn = service.begin_transaction()

        mock_begin.assert_called_once_with(
            projectId="test-project", body={}
        )
        assert txn == "txn-abc-123"

    def test_begin_transaction_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_begin = mock_google_client.projects.return_value.beginTransaction
        mock_begin.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = DatastoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.begin_transaction()


# --- Commit tests ---


class TestCommit:
    def test_commit_non_transactional(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_commit = mock_google_client.projects.return_value.commit
        mock_commit.return_value = mock_request
        mock_request.execute.return_value = {"mutationResults": [{}]}

        service = DatastoreService(project_id="test-project")
        mutations = [{"upsert": {"key": {}, "properties": {}}}]
        result = service.commit(mutations)

        call_args = mock_commit.call_args
        body = call_args[1]["body"]
        assert body["mode"] == "NON_TRANSACTIONAL"
        assert "transaction" not in body
        assert result == {"mutationResults": [{}]}

    def test_commit_with_transaction(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_commit = mock_google_client.projects.return_value.commit
        mock_commit.return_value = mock_request
        mock_request.execute.return_value = {"mutationResults": [{}]}

        service = DatastoreService(project_id="test-project")
        mutations = [{"upsert": {"key": {}, "properties": {}}}]
        result = service.commit(mutations, transaction="txn-abc-123")

        call_args = mock_commit.call_args
        body = call_args[1]["body"]
        assert body["transaction"] == "txn-abc-123"
        assert "mode" not in body
        assert result == {"mutationResults": [{}]}

    def test_commit_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_commit = mock_google_client.projects.return_value.commit
        mock_commit.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = DatastoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.commit([{"upsert": {"key": {}, "properties": {}}}])


# --- Rollback tests ---


class TestRollback:
    def test_rollback(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_rollback = mock_google_client.projects.return_value.rollback
        mock_rollback.return_value = mock_request
        mock_request.execute.return_value = {}

        service = DatastoreService(project_id="test-project")
        result = service.rollback("txn-abc-123")

        mock_rollback.assert_called_once_with(
            projectId="test-project", body={"transaction": "txn-abc-123"}
        )
        assert result is True

    def test_rollback_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_rollback = mock_google_client.projects.return_value.rollback
        mock_rollback.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = DatastoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.rollback("txn-abc-123")
