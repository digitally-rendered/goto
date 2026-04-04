"""Tests for Data Catalog service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.data_catalog import DataCatalogService
from gcpoto.models.data_catalog import EntryGroup, Entry, Tag
from gcpoto.exceptions import ResourceNotFoundError, APIError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
ENTRY_GROUP_ID = "my_entry_group"
ENTRY_ID = "my_entry"


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_entry_groups = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.entryGroups.return_value = (
            mock_entry_groups
        )

        mock_entries = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.entryGroups.return_value.entries.return_value = (
            mock_entries
        )

        mock_catalog = mock.MagicMock()
        mock_service.catalog.return_value = mock_catalog

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a DataCatalogService with mocked client."""
    return DataCatalogService(project_id=PROJECT_ID)


@pytest.fixture
def mock_entry_groups(mock_google_client):
    """Shortcut to mock entry groups resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .entryGroups.return_value
    )


@pytest.fixture
def mock_entries(mock_google_client):
    """Shortcut to mock entries resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .entryGroups.return_value.entries.return_value
    )


@pytest.fixture
def mock_catalog(mock_google_client):
    """Shortcut to mock catalog resource."""
    return mock_google_client.catalog.return_value


@pytest.fixture
def sample_entry_group_response():
    """Sample entry group API response."""
    return {
        "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/{ENTRY_GROUP_ID}",
        "displayName": "My Entry Group",
        "description": "A test entry group",
        "dataCatalogTimestamps": {
            "createTime": "2026-03-31T10:00:00Z",
            "updateTime": "2026-03-31T11:00:00Z",
        },
    }


@pytest.fixture
def sample_entry_response():
    """Sample entry API response."""
    return {
        "name": (
            f"projects/{PROJECT_ID}/locations/{LOCATION}"
            f"/entryGroups/{ENTRY_GROUP_ID}/entries/{ENTRY_ID}"
        ),
        "type": "TABLE",
        "linkedResource": "//bigquery.googleapis.com/projects/test/datasets/ds/tables/t",
        "displayName": "My Entry",
        "description": "A test entry",
        "schema": {
            "columns": [
                {"column": "id", "type": "INT64"},
                {"column": "name", "type": "STRING"},
            ]
        },
        "sourceSystemTimestamps": {
            "createTime": "2026-03-31T10:00:00Z",
            "updateTime": "2026-03-31T11:00:00Z",
        },
    }


class TestDataCatalogServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the DataCatalogService."""
        from googleapiclient.discovery import build

        svc = DataCatalogService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with("datacatalog", "v1", credentials=None)


class TestListEntryGroups:
    def test_list_entry_groups(
        self, service, mock_entry_groups, sample_entry_group_response
    ):
        """Test listing entry groups."""
        mock_request = mock.MagicMock()
        mock_entry_groups.list.return_value = mock_request
        mock_request.execute.return_value = {
            "entryGroups": [sample_entry_group_response]
        }
        mock_entry_groups.list_next.return_value = None

        results = service.list_entry_groups(LOCATION)

        mock_entry_groups.list.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}"
        )
        assert len(results) == 1
        assert isinstance(results[0], EntryGroup)
        assert results[0].display_name == "My Entry Group"

    def test_list_entry_groups_empty(self, service, mock_entry_groups):
        """Test listing entry groups when none exist."""
        mock_request = mock.MagicMock()
        mock_entry_groups.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_entry_groups.list_next.return_value = None

        results = service.list_entry_groups(LOCATION)
        assert len(results) == 0


class TestGetEntryGroup:
    def test_get_entry_group(
        self, service, mock_entry_groups, sample_entry_group_response
    ):
        """Test getting a specific entry group."""
        mock_request = mock.MagicMock()
        mock_entry_groups.get.return_value = mock_request
        mock_request.execute.return_value = sample_entry_group_response

        result = service.get_entry_group(LOCATION, ENTRY_GROUP_ID)

        assert isinstance(result, EntryGroup)
        assert result.display_name == "My Entry Group"
        assert result.description == "A test entry group"

    def test_get_entry_group_not_found(self, service, mock_entry_groups):
        """Test getting an entry group that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_entry_groups.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_entry_group(LOCATION, ENTRY_GROUP_ID)


class TestCreateEntryGroup:
    def test_create_entry_group(
        self, service, mock_entry_groups, sample_entry_group_response
    ):
        """Test creating a new entry group."""
        mock_request = mock.MagicMock()
        mock_entry_groups.create.return_value = mock_request
        mock_request.execute.return_value = sample_entry_group_response

        result = service.create_entry_group(
            LOCATION, ENTRY_GROUP_ID, display_name="My Entry Group"
        )

        mock_entry_groups.create.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}",
            entryGroupId=ENTRY_GROUP_ID,
            body={"displayName": "My Entry Group"},
        )
        assert isinstance(result, EntryGroup)
        assert result.display_name == "My Entry Group"

    def test_create_entry_group_api_error(self, service, mock_entry_groups):
        """Test creating an entry group when API returns an error."""
        mock_request = mock.MagicMock()
        mock_entry_groups.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_entry_group(LOCATION, ENTRY_GROUP_ID)


class TestDeleteEntryGroup:
    def test_delete_entry_group(self, service, mock_entry_groups):
        """Test deleting an entry group."""
        mock_entry_groups.delete.return_value.execute.return_value = {}

        result = service.delete_entry_group(LOCATION, ENTRY_GROUP_ID)
        assert result is True

    def test_delete_entry_group_not_found(self, service, mock_entry_groups):
        """Test deleting an entry group that doesn't exist."""
        mock_entry_groups.delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_entry_group(LOCATION, ENTRY_GROUP_ID)


class TestListEntries:
    def test_list_entries(
        self, service, mock_entries, sample_entry_response
    ):
        """Test listing entries in an entry group."""
        mock_request = mock.MagicMock()
        mock_entries.list.return_value = mock_request
        mock_request.execute.return_value = {
            "entries": [sample_entry_response]
        }
        mock_entries.list_next.return_value = None

        results = service.list_entries(LOCATION, ENTRY_GROUP_ID)

        assert len(results) == 1
        assert isinstance(results[0], Entry)
        assert results[0].display_name == "My Entry"

    def test_list_entries_empty(self, service, mock_entries):
        """Test listing entries when none exist."""
        mock_request = mock.MagicMock()
        mock_entries.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_entries.list_next.return_value = None

        results = service.list_entries(LOCATION, ENTRY_GROUP_ID)
        assert len(results) == 0


class TestGetEntry:
    def test_get_entry(
        self, service, mock_entries, sample_entry_response
    ):
        """Test getting a specific entry."""
        mock_request = mock.MagicMock()
        mock_entries.get.return_value = mock_request
        mock_request.execute.return_value = sample_entry_response

        result = service.get_entry(LOCATION, ENTRY_GROUP_ID, ENTRY_ID)

        assert isinstance(result, Entry)
        assert result.display_name == "My Entry"
        assert result.entry_type == "TABLE"

    def test_get_entry_not_found(self, service, mock_entries):
        """Test getting an entry that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_entries.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_entry(LOCATION, ENTRY_GROUP_ID, ENTRY_ID)


class TestCreateEntry:
    def test_create_entry(
        self, service, mock_entries, sample_entry_response
    ):
        """Test creating a new entry."""
        mock_request = mock.MagicMock()
        mock_entries.create.return_value = mock_request
        mock_request.execute.return_value = sample_entry_response

        result = service.create_entry(
            LOCATION, ENTRY_GROUP_ID, ENTRY_ID, "TABLE"
        )

        assert isinstance(result, Entry)
        assert result.entry_type == "TABLE"

    def test_create_entry_api_error(self, service, mock_entries):
        """Test creating an entry when API returns an error."""
        mock_request = mock.MagicMock()
        mock_entries.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_entry(
                LOCATION, ENTRY_GROUP_ID, ENTRY_ID, "TABLE"
            )


class TestDeleteEntry:
    def test_delete_entry(self, service, mock_entries):
        """Test deleting an entry."""
        mock_entries.delete.return_value.execute.return_value = {}

        result = service.delete_entry(LOCATION, ENTRY_GROUP_ID, ENTRY_ID)
        assert result is True

    def test_delete_entry_not_found(self, service, mock_entries):
        """Test deleting an entry that doesn't exist."""
        mock_entries.delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_entry(LOCATION, ENTRY_GROUP_ID, ENTRY_ID)


class TestSearchCatalog:
    def test_search_catalog(self, service, mock_catalog):
        """Test searching the catalog."""
        mock_request = mock.MagicMock()
        mock_catalog.search.return_value = mock_request
        mock_request.execute.return_value = {
            "results": [
                {"searchResultType": "ENTRY", "linkedResource": "//bigquery/t"}
            ]
        }

        results = service.search_catalog(
            scope={"includeProjectIds": [PROJECT_ID]},
            query="type=TABLE",
        )

        mock_catalog.search.assert_called_once_with(
            body={
                "scope": {"includeProjectIds": [PROJECT_ID]},
                "query": "type=TABLE",
            }
        )
        assert len(results) == 1

    def test_search_catalog_api_error(self, service, mock_catalog):
        """Test searching when API returns an error."""
        mock_request = mock.MagicMock()
        mock_catalog.search.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.search_catalog(
                scope={"includeProjectIds": [PROJECT_ID]},
                query="bad query",
            )


class TestEntryGroupModel:
    def test_from_api_response(self, sample_entry_group_response):
        """Test creating an EntryGroup from API response."""
        eg = EntryGroup.from_api_response(sample_entry_group_response)

        assert eg.id == ENTRY_GROUP_ID
        assert eg.location == LOCATION
        assert eg.project == PROJECT_ID
        assert eg.display_name == "My Entry Group"
        assert eg.description == "A test entry group"
        assert eg.type == "datacatalog.entryGroup"

    def test_from_api_response_minimal(self):
        """Test creating an EntryGroup from minimal API response."""
        response = {
            "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/entryGroups/minimal"
        }
        eg = EntryGroup.from_api_response(response)

        assert eg.id == "minimal"
        assert eg.display_name is None
        assert eg.description is None


class TestEntryModel:
    def test_from_api_response(self, sample_entry_response):
        """Test creating an Entry from API response."""
        entry = Entry.from_api_response(sample_entry_response)

        assert entry.id == ENTRY_ID
        assert entry.entry_group == ENTRY_GROUP_ID
        assert entry.location == LOCATION
        assert entry.entry_type == "TABLE"
        assert entry.display_name == "My Entry"
        assert entry.schema is not None
        assert entry.linked_resource is not None

    def test_from_api_response_minimal(self):
        """Test creating an Entry from minimal API response."""
        response = {
            "name": (
                f"projects/{PROJECT_ID}/locations/{LOCATION}"
                f"/entryGroups/{ENTRY_GROUP_ID}/entries/minimal"
            )
        }
        entry = Entry.from_api_response(response)

        assert entry.id == "minimal"
        assert entry.display_name is None
        assert entry.schema is None


class TestTagModel:
    def test_from_api_response(self):
        """Test creating a Tag from API response."""
        response = {
            "name": (
                f"projects/{PROJECT_ID}/locations/{LOCATION}"
                f"/entryGroups/{ENTRY_GROUP_ID}/entries/{ENTRY_ID}"
                "/tags/tag123"
            ),
            "template": f"projects/{PROJECT_ID}/locations/{LOCATION}/tagTemplates/tmpl",
            "fields": {
                "source": {"stringValue": "test"},
                "count": {"doubleValue": 42.0},
            },
        }
        tag = Tag.from_api_response(response)

        assert tag.id == "tag123"
        assert tag.template == response["template"]
        assert tag.fields == response["fields"]
        assert tag.type == "datacatalog.tag"
