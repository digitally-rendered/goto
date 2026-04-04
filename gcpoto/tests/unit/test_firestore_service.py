"""Tests for Firestore service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.firestore import FirestoreService
from gcpoto.models.firestore import (
    FirestoreDocument,
    FirestoreCollection,
    FirestoreIndex,
)
from gcpoto.exceptions import ResourceNotFoundError, APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().databases().documents() chain
        mock_documents = mock.MagicMock()
        mock_service.projects.return_value.databases.return_value.documents.return_value = (
            mock_documents
        )

        # Set up projects().databases().collectionGroups().indexes() chain
        mock_indexes = mock.MagicMock()
        mock_service.projects.return_value.databases.return_value.collectionGroups.return_value.indexes.return_value = (
            mock_indexes
        )

        yield mock_service


@pytest.fixture
def sample_document_response():
    """Sample Firestore document API response."""
    return {
        "name": "projects/test-project/databases/(default)/documents/users/user1",
        "fields": {
            "displayName": {"stringValue": "Alice"},
            "age": {"integerValue": "30"},
            "active": {"booleanValue": True},
        },
        "createTime": "2025-06-15T10:30:00Z",
        "updateTime": "2025-06-15T12:00:00Z",
    }


@pytest.fixture
def sample_index_response():
    """Sample Firestore index API response."""
    return {
        "name": "projects/test-project/databases/(default)/collectionGroups/users/indexes/idx1",
        "queryScope": "COLLECTION",
        "fields": [
            {"fieldPath": "age", "order": "ASCENDING"},
            {"fieldPath": "displayName", "order": "ASCENDING"},
        ],
        "state": "READY",
    }


# --- Model tests ---


class TestFirestoreDocumentModel:
    def test_from_api_response(self, sample_document_response):
        doc = FirestoreDocument.from_api_response(
            sample_document_response, "test-project"
        )
        assert doc.collection == "users"
        assert doc.document_id == "user1"
        assert doc.project == "test-project"
        assert doc.type == "firestore.document"
        assert doc.fields["displayName"] == {"stringValue": "Alice"}
        assert doc.create_time is not None
        assert doc.update_time is not None

    def test_from_api_response_extracts_project(
        self, sample_document_response
    ):
        doc = FirestoreDocument.from_api_response(sample_document_response)
        assert doc.project == "test-project"

    def test_from_api_response_minimal(self):
        doc = FirestoreDocument.from_api_response(
            {"name": "projects/p/databases/(default)/documents/c/d"},
            "p",
        )
        assert doc.collection == "c"
        assert doc.document_id == "d"
        assert doc.fields == {}
        assert doc.create_time is None
        assert doc.update_time is None

    def test_get_tag_default(self, sample_document_response):
        doc = FirestoreDocument.from_api_response(
            sample_document_response, "test-project"
        )
        assert doc.get_tag("missing") == ""
        assert doc.get_tag("missing", "fallback") == "fallback"


class TestFirestoreCollectionModel:
    def test_from_api_response_string(self):
        collection = FirestoreCollection.from_api_response(
            "users", "test-project"
        )
        assert collection.collection_id == "users"
        assert collection.name == "users"
        assert collection.project == "test-project"
        assert collection.type == "firestore.collection"
        assert collection.document_count is None

    def test_from_api_response_dict(self):
        collection = FirestoreCollection.from_api_response(
            {"collectionId": "orders", "documentCount": 42},
            "test-project",
        )
        assert collection.collection_id == "orders"
        assert collection.document_count == 42


class TestFirestoreIndexModel:
    def test_from_api_response(self, sample_index_response):
        index = FirestoreIndex.from_api_response(
            sample_index_response, "test-project"
        )
        assert index.collection_group == "users"
        assert index.query_scope == "COLLECTION"
        assert index.state == "READY"
        assert len(index.fields_config) == 2
        assert index.fields_config[0]["fieldPath"] == "age"
        assert index.project == "test-project"
        assert index.type == "firestore.index"

    def test_from_api_response_extracts_project(self, sample_index_response):
        index = FirestoreIndex.from_api_response(sample_index_response)
        assert index.project == "test-project"

    def test_from_api_response_collection_group_scope(self):
        response = {
            "name": "projects/p/databases/(default)/collectionGroups/events/indexes/idx2",
            "queryScope": "COLLECTION_GROUP",
            "fields": [{"fieldPath": "timestamp", "order": "DESCENDING"}],
            "state": "CREATING",
        }
        index = FirestoreIndex.from_api_response(response, "p")
        assert index.query_scope == "COLLECTION_GROUP"
        assert index.state == "CREATING"
        assert index.collection_group == "events"


# --- Service init tests ---


class TestFirestoreServiceInit:
    def test_init(self, mock_google_client):
        from googleapiclient.discovery import build

        service = FirestoreService(project_id="test-project")
        assert service.project_id == "test-project"
        build.assert_called_once_with("firestore", "v1", credentials=None)

    def test_database_path(self, mock_google_client):
        service = FirestoreService(project_id="test-project")
        assert (
            service._database_path()
            == "projects/test-project/databases/(default)"
        )

    def test_documents_path(self, mock_google_client):
        service = FirestoreService(project_id="test-project")
        assert (
            service._documents_path()
            == "projects/test-project/databases/(default)/documents"
        )

    def test_document_path(self, mock_google_client):
        service = FirestoreService(project_id="test-project")
        assert (
            service._document_path("users", "user1")
            == "projects/test-project/databases/(default)/documents/users/user1"
        )


# --- Get document tests ---


class TestGetDocument:
    def test_get_document(self, mock_google_client, sample_document_response):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_document_response

        service = FirestoreService(project_id="test-project")
        doc = service.get_document("users", "user1")

        mock_get.assert_called_once_with(
            name="projects/test-project/databases/(default)/documents/users/user1"
        )
        assert isinstance(doc, FirestoreDocument)
        assert doc.collection == "users"
        assert doc.document_id == "user1"

    def test_get_document_not_found(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = FirestoreService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.get_document("users", "nonexistent")

    def test_get_document_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = FirestoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.get_document("users", "user1")


# --- Create document tests ---


class TestCreateDocument:
    def test_create_document(
        self, mock_google_client, sample_document_response
    ):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.createDocument
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_document_response

        service = FirestoreService(project_id="test-project")
        fields = {"displayName": {"stringValue": "Alice"}}
        doc = service.create_document("users", "user1", fields)

        mock_create.assert_called_once_with(
            parent="projects/test-project/databases/(default)/documents",
            collectionId="users",
            documentId="user1",
            body={"fields": fields},
        )
        assert isinstance(doc, FirestoreDocument)
        assert doc.document_id == "user1"

    def test_create_document_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.createDocument
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        service = FirestoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.create_document("users", "user1", {})


# --- Update document tests ---


class TestUpdateDocument:
    def test_update_document(
        self, mock_google_client, sample_document_response
    ):
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_document_response

        service = FirestoreService(project_id="test-project")
        fields = {"displayName": {"stringValue": "Bob"}}
        doc = service.update_document("users", "user1", fields)

        mock_patch.assert_called_once_with(
            name="projects/test-project/databases/(default)/documents/users/user1",
            body={"fields": fields},
        )
        assert isinstance(doc, FirestoreDocument)

    def test_update_document_with_mask(
        self, mock_google_client, sample_document_response
    ):
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_document_response

        service = FirestoreService(project_id="test-project")
        fields = {"displayName": {"stringValue": "Bob"}}
        doc = service.update_document(
            "users", "user1", fields, update_mask=["displayName"]
        )

        mock_patch.assert_called_once_with(
            name="projects/test-project/databases/(default)/documents/users/user1",
            body={"fields": fields},
            updateMask_fieldPaths=["displayName"],
        )
        assert isinstance(doc, FirestoreDocument)

    def test_update_document_not_found(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = FirestoreService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.update_document("users", "nonexistent", {})


# --- Delete document tests ---


class TestDeleteDocument:
    def test_delete_document(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = FirestoreService(project_id="test-project")
        result = service.delete_document("users", "user1")

        mock_delete.assert_called_once_with(
            name="projects/test-project/databases/(default)/documents/users/user1"
        )
        assert result is True

    def test_delete_document_not_found(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = FirestoreService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.delete_document("users", "nonexistent")


# --- List documents tests ---


class TestListDocuments:
    def test_list_documents(
        self, mock_google_client, sample_document_response
    ):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "documents": [sample_document_response, sample_document_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.list_next
        )
        mock_list_next.return_value = None

        service = FirestoreService(project_id="test-project")
        docs = service.list_documents("users")

        mock_list.assert_called_once_with(
            parent="projects/test-project/databases/(default)/documents",
            collectionId="users",
            pageSize=100,
        )
        assert len(docs) == 2
        assert isinstance(docs[0], FirestoreDocument)
        assert docs[0].collection == "users"

    def test_list_documents_with_order_by(
        self, mock_google_client, sample_document_response
    ):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "documents": [sample_document_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.list_next
        )
        mock_list_next.return_value = None

        service = FirestoreService(project_id="test-project")
        docs = service.list_documents(
            "users", page_size=50, order_by="displayName"
        )

        mock_list.assert_called_once_with(
            parent="projects/test-project/databases/(default)/documents",
            collectionId="users",
            pageSize=50,
            orderBy="displayName",
        )
        assert len(docs) == 1

    def test_list_documents_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.list_next
        )
        mock_list_next.return_value = None

        service = FirestoreService(project_id="test-project")
        docs = service.list_documents("users")
        assert docs == []

    def test_list_documents_pagination(
        self, mock_google_client, sample_document_response
    ):
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.list
        )
        mock_list.return_value = mock_request_page1

        mock_request_page1.execute.return_value = {
            "documents": [sample_document_response]
        }
        mock_request_page2.execute.return_value = {
            "documents": [sample_document_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.list_next
        )
        mock_list_next.side_effect = [mock_request_page2, None]

        service = FirestoreService(project_id="test-project")
        docs = service.list_documents("users")
        assert len(docs) == 2


# --- Query documents tests ---


class TestQueryDocuments:
    def test_query_documents_single_filter(
        self, mock_google_client, sample_document_response
    ):
        mock_request = mock.MagicMock()
        mock_run_query = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.runQuery
        )
        mock_run_query.return_value = mock_request
        mock_request.execute.return_value = [
            {"document": sample_document_response}
        ]

        service = FirestoreService(project_id="test-project")
        filters = [
            {
                "field": "age",
                "op": "GREATER_THAN",
                "value": {"integerValue": "25"},
            }
        ]
        docs = service.query_documents("users", field_filters=filters)

        call_args = mock_run_query.call_args
        body = call_args[1]["body"]
        assert body["structuredQuery"]["from"] == [
            {"collectionId": "users"}
        ]
        assert "fieldFilter" in body["structuredQuery"]["where"]
        assert len(docs) == 1
        assert isinstance(docs[0], FirestoreDocument)

    def test_query_documents_multiple_filters(
        self, mock_google_client, sample_document_response
    ):
        mock_request = mock.MagicMock()
        mock_run_query = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.runQuery
        )
        mock_run_query.return_value = mock_request
        mock_request.execute.return_value = [
            {"document": sample_document_response}
        ]

        service = FirestoreService(project_id="test-project")
        filters = [
            {
                "field": "age",
                "op": "GREATER_THAN",
                "value": {"integerValue": "25"},
            },
            {
                "field": "active",
                "op": "EQUAL",
                "value": {"booleanValue": True},
            },
        ]
        docs = service.query_documents("users", field_filters=filters)

        call_args = mock_run_query.call_args
        body = call_args[1]["body"]
        composite = body["structuredQuery"]["where"]["compositeFilter"]
        assert composite["op"] == "AND"
        assert len(composite["filters"]) == 2
        assert len(docs) == 1

    def test_query_documents_with_order_and_limit(
        self, mock_google_client, sample_document_response
    ):
        mock_request = mock.MagicMock()
        mock_run_query = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.runQuery
        )
        mock_run_query.return_value = mock_request
        mock_request.execute.return_value = [
            {"document": sample_document_response}
        ]

        service = FirestoreService(project_id="test-project")
        docs = service.query_documents(
            "users",
            order_by=[{"field": "age", "direction": "DESCENDING"}],
            limit=10,
        )

        call_args = mock_run_query.call_args
        body = call_args[1]["body"]
        assert body["structuredQuery"]["orderBy"][0]["direction"] == "DESCENDING"
        assert body["structuredQuery"]["limit"] == 10
        assert len(docs) == 1

    def test_query_documents_no_results(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_run_query = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.runQuery
        )
        mock_run_query.return_value = mock_request
        mock_request.execute.return_value = [{"readTime": "2025-01-01T00:00:00Z"}]

        service = FirestoreService(project_id="test-project")
        docs = service.query_documents("users")
        assert docs == []

    def test_query_documents_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_run_query = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.runQuery
        )
        mock_run_query.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        service = FirestoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.query_documents("users")


# --- List collection IDs tests ---


class TestListCollectionIds:
    def test_list_collection_ids(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list_ids = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.listCollectionIds
        )
        mock_list_ids.return_value = mock_request
        mock_request.execute.return_value = {
            "collectionIds": ["users", "orders", "products"]
        }

        service = FirestoreService(project_id="test-project")
        collections = service.list_collection_ids()

        mock_list_ids.assert_called_once_with(
            parent="projects/test-project/databases/(default)/documents",
            body={},
        )
        assert len(collections) == 3
        assert isinstance(collections[0], FirestoreCollection)
        assert collections[0].collection_id == "users"
        assert collections[1].collection_id == "orders"
        assert collections[2].collection_id == "products"

    def test_list_collection_ids_with_parent(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list_ids = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.listCollectionIds
        )
        mock_list_ids.return_value = mock_request
        mock_request.execute.return_value = {
            "collectionIds": ["subcollection1"]
        }

        service = FirestoreService(project_id="test-project")
        parent = "projects/test-project/databases/(default)/documents/users/user1"
        collections = service.list_collection_ids(parent=parent)

        mock_list_ids.assert_called_once_with(
            parent=parent,
            body={},
        )
        assert len(collections) == 1
        assert collections[0].collection_id == "subcollection1"

    def test_list_collection_ids_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list_ids = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.listCollectionIds
        )
        mock_list_ids.return_value = mock_request
        mock_request.execute.return_value = {}

        service = FirestoreService(project_id="test-project")
        collections = service.list_collection_ids()
        assert collections == []


# --- List indexes tests ---


class TestListIndexes:
    def test_list_indexes(self, mock_google_client, sample_index_response):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.databases.return_value.collectionGroups.return_value.indexes.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "indexes": [sample_index_response]
        }

        service = FirestoreService(project_id="test-project")
        indexes = service.list_indexes(collection_group="users")

        mock_list.assert_called_once_with(
            parent="projects/test-project/databases/(default)/collectionGroups/users"
        )
        assert len(indexes) == 1
        assert isinstance(indexes[0], FirestoreIndex)
        assert indexes[0].collection_group == "users"
        assert indexes[0].state == "READY"

    def test_list_indexes_all(self, mock_google_client, sample_index_response):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.databases.return_value.collectionGroups.return_value.indexes.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "indexes": [sample_index_response]
        }

        service = FirestoreService(project_id="test-project")
        indexes = service.list_indexes()

        mock_list.assert_called_once_with(
            parent="projects/test-project/databases/(default)/collectionGroups/-"
        )
        assert len(indexes) == 1

    def test_list_indexes_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.databases.return_value.collectionGroups.return_value.indexes.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        service = FirestoreService(project_id="test-project")
        indexes = service.list_indexes()
        assert indexes == []


# --- Create index tests ---


class TestCreateIndex:
    def test_create_index(self, mock_google_client, sample_index_response):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.databases.return_value.collectionGroups.return_value.indexes.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_index_response

        service = FirestoreService(project_id="test-project")
        fields_config = [
            {"fieldPath": "age", "order": "ASCENDING"},
            {"fieldPath": "displayName", "order": "ASCENDING"},
        ]
        index = service.create_index("users", fields_config)

        mock_create.assert_called_once_with(
            parent="projects/test-project/databases/(default)/collectionGroups/users",
            body={
                "queryScope": "COLLECTION",
                "fields": fields_config,
            },
        )
        assert isinstance(index, FirestoreIndex)
        assert index.collection_group == "users"

    def test_create_index_collection_group_scope(
        self, mock_google_client, sample_index_response
    ):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.databases.return_value.collectionGroups.return_value.indexes.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_index_response

        service = FirestoreService(project_id="test-project")
        fields_config = [{"fieldPath": "timestamp", "order": "DESCENDING"}]
        service.create_index(
            "events", fields_config, query_scope="COLLECTION_GROUP"
        )

        call_args = mock_create.call_args
        assert call_args[1]["body"]["queryScope"] == "COLLECTION_GROUP"

    def test_create_index_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.databases.return_value.collectionGroups.return_value.indexes.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        service = FirestoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.create_index("users", [])


# --- Delete index tests ---


class TestDeleteIndex:
    def test_delete_index(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.databases.return_value.collectionGroups.return_value.indexes.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = FirestoreService(project_id="test-project")
        index_name = "projects/test-project/databases/(default)/collectionGroups/users/indexes/idx1"
        result = service.delete_index(index_name)

        mock_delete.assert_called_once_with(name=index_name)
        assert result is True

    def test_delete_index_not_found(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.databases.return_value.collectionGroups.return_value.indexes.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = FirestoreService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.delete_index("projects/p/databases/(default)/collectionGroups/g/indexes/bad")


# --- Batch get documents tests ---


class TestBatchGetDocuments:
    def test_batch_get_documents(
        self, mock_google_client, sample_document_response
    ):
        mock_request = mock.MagicMock()
        mock_batch_get = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.batchGet
        )
        mock_batch_get.return_value = mock_request
        mock_request.execute.return_value = [
            {"found": {"document": sample_document_response}},
            {"found": {"document": sample_document_response}},
        ]

        service = FirestoreService(project_id="test-project")
        docs = service.batch_get_documents("users", ["user1", "user2"])

        mock_batch_get.assert_called_once_with(
            database="projects/test-project/databases/(default)",
            body={
                "documents": [
                    "projects/test-project/databases/(default)/documents/users/user1",
                    "projects/test-project/databases/(default)/documents/users/user2",
                ]
            },
        )
        assert len(docs) == 2
        assert isinstance(docs[0], FirestoreDocument)

    def test_batch_get_documents_partial_missing(
        self, mock_google_client, sample_document_response
    ):
        mock_request = mock.MagicMock()
        mock_batch_get = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.batchGet
        )
        mock_batch_get.return_value = mock_request
        mock_request.execute.return_value = [
            {"found": {"document": sample_document_response}},
            {
                "missing": "projects/test-project/databases/(default)/documents/users/user2"
            },
        ]

        service = FirestoreService(project_id="test-project")
        docs = service.batch_get_documents("users", ["user1", "user2"])

        assert len(docs) == 1
        assert docs[0].document_id == "user1"

    def test_batch_get_documents_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_batch_get = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.batchGet
        )
        mock_batch_get.return_value = mock_request
        mock_request.execute.return_value = []

        service = FirestoreService(project_id="test-project")
        docs = service.batch_get_documents("users", ["user1"])
        assert docs == []

    def test_batch_get_documents_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_batch_get = (
            mock_google_client.projects.return_value.databases.return_value.documents.return_value.batchGet
        )
        mock_batch_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = FirestoreService(project_id="test-project")
        with pytest.raises(APIError):
            service.batch_get_documents("users", ["user1"])
