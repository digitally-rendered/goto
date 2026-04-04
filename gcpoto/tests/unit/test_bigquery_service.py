"""Tests for BigQuery service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.bigquery import BigQueryService
from gcpoto.models.bigquery import BigQueryDataset, BigQueryTable, BigQueryJob
from gcpoto.exceptions import ResourceNotFoundError, APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_datasets = mock.MagicMock()
        mock_service.datasets.return_value = mock_datasets

        mock_tables = mock.MagicMock()
        mock_service.tables.return_value = mock_tables

        mock_jobs = mock.MagicMock()
        mock_service.jobs.return_value = mock_jobs

        yield mock_service


@pytest.fixture
def sample_dataset_response():
    """Sample BigQuery dataset API response."""
    return {
        "id": "test-project:test_dataset",
        "datasetReference": {
            "datasetId": "test_dataset",
            "projectId": "test-project",
        },
        "friendlyName": "Test Dataset",
        "description": "A test dataset",
        "location": "US",
        "defaultTableExpirationMs": "3600000",
        "defaultPartitionExpirationMs": "7200000",
        "access": [
            {"role": "WRITER", "specialGroup": "projectWriters"},
            {"role": "OWNER", "userByEmail": "owner@example.com"},
            {"role": "READER", "specialGroup": "projectReaders"},
        ],
        "labels": {"env": "test", "team": "data"},
        "creationTime": "1609459200000",
        "lastModifiedTime": "1609459200000",
    }


@pytest.fixture
def sample_table_response():
    """Sample BigQuery table API response."""
    return {
        "id": "test-project:test_dataset.test_table",
        "tableReference": {
            "tableId": "test_table",
            "datasetId": "test_dataset",
            "projectId": "test-project",
        },
        "friendlyName": "Test Table",
        "description": "A test table",
        "schema": {
            "fields": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"},
                {"name": "name", "type": "STRING", "mode": "NULLABLE"},
                {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"},
            ]
        },
        "numRows": "1000",
        "numBytes": "50000",
        "type": "TABLE",
        "timePartitioning": {"type": "DAY", "field": "created_at"},
        "clustering": {"fields": ["name"]},
        "expirationTime": "1640995200000",
        "labels": {"env": "test"},
        "creationTime": "1609459200000",
        "lastModifiedTime": "1609459200000",
    }


@pytest.fixture
def sample_job_response():
    """Sample BigQuery job API response."""
    return {
        "id": "test-project:job_abc123",
        "jobReference": {
            "jobId": "job_abc123",
            "projectId": "test-project",
        },
        "status": {
            "state": "DONE",
        },
        "configuration": {
            "query": {
                "query": "SELECT * FROM `test_dataset.test_table`",
                "useLegacySql": False,
            }
        },
        "statistics": {
            "startTime": "1609459200000",
            "endTime": "1609459210000",
            "creationTime": "1609459199000",
            "totalBytesProcessed": "50000",
        },
        "user_email": "user@example.com",
        "labels": {"team": "analytics"},
    }


@pytest.fixture
def sample_job_response_with_error():
    """Sample BigQuery job API response with an error."""
    return {
        "id": "test-project:job_err456",
        "jobReference": {
            "jobId": "job_err456",
            "projectId": "test-project",
        },
        "status": {
            "state": "DONE",
            "errorResult": {
                "reason": "invalidQuery",
                "location": "query",
                "message": "Syntax error in SQL query",
            },
        },
        "configuration": {
            "query": {
                "query": "SELECT * FORM bad_table",
                "useLegacySql": False,
            }
        },
        "statistics": {
            "creationTime": "1609459199000",
        },
        "user_email": "user@example.com",
    }


class TestBigQueryServiceInit:
    """Tests for BigQuery service initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the BigQueryService."""
        from googleapiclient.discovery import build

        service = BigQueryService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "bigquery"
        assert service.version == "v2"
        build.assert_called_once_with("bigquery", "v2", credentials=None)


class TestBigQueryDatasets:
    """Tests for BigQuery dataset operations."""

    def test_list_datasets(self, mock_google_client, sample_dataset_response):
        """Test listing BigQuery datasets."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.datasets.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "datasets": [sample_dataset_response, sample_dataset_response]
        }

        mock_list_next = mock_google_client.datasets.return_value.list_next
        mock_list_next.return_value = None

        service = BigQueryService(project_id="test-project")
        datasets = service.list_datasets()

        mock_list.assert_called_once_with(projectId="test-project")
        assert len(datasets) == 2
        assert isinstance(datasets[0], BigQueryDataset)
        assert datasets[0].dataset_id == "test_dataset"
        assert datasets[0].project == "test-project"
        assert datasets[0].location == "US"

    def test_list_datasets_empty(self, mock_google_client):
        """Test listing datasets when none exist."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.datasets.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = mock_google_client.datasets.return_value.list_next
        mock_list_next.return_value = None

        service = BigQueryService(project_id="test-project")
        datasets = service.list_datasets()

        assert len(datasets) == 0

    def test_list_datasets_pagination(
        self, mock_google_client, sample_dataset_response
    ):
        """Test listing datasets with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = mock_google_client.datasets.return_value.list
        mock_list.return_value = mock_request_page1

        mock_request_page1.execute.return_value = {
            "datasets": [sample_dataset_response]
        }
        mock_request_page2.execute.return_value = {
            "datasets": [sample_dataset_response]
        }

        mock_list_next = mock_google_client.datasets.return_value.list_next
        mock_list_next.side_effect = [mock_request_page2, None]

        service = BigQueryService(project_id="test-project")
        datasets = service.list_datasets()

        assert len(datasets) == 2

    def test_get_dataset(self, mock_google_client, sample_dataset_response):
        """Test getting a specific dataset."""
        mock_request = mock.MagicMock()
        mock_get = mock_google_client.datasets.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_dataset_response

        service = BigQueryService(project_id="test-project")
        dataset = service.get_dataset("test_dataset")

        mock_get.assert_called_once_with(
            projectId="test-project", datasetId="test_dataset"
        )
        assert isinstance(dataset, BigQueryDataset)
        assert dataset.dataset_id == "test_dataset"
        assert dataset.friendly_name == "Test Dataset"
        assert dataset.description == "A test dataset"
        assert dataset.location == "US"
        assert len(dataset.access) == 3

    def test_get_dataset_not_found(self, mock_google_client):
        """Test getting a dataset that does not exist."""
        mock_get = mock_google_client.datasets.return_value.get
        mock_get.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigQueryService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_dataset("nonexistent_dataset")

    def test_create_dataset(self, mock_google_client, sample_dataset_response):
        """Test creating a new dataset."""
        mock_request = mock.MagicMock()
        mock_insert = mock_google_client.datasets.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.return_value = sample_dataset_response

        service = BigQueryService(project_id="test-project")
        dataset = service.create_dataset(
            dataset_id="test_dataset",
            location="US",
            description="A test dataset",
            labels={"env": "test"},
        )

        mock_insert.assert_called_once_with(
            projectId="test-project",
            body={
                "datasetReference": {
                    "datasetId": "test_dataset",
                    "projectId": "test-project",
                },
                "location": "US",
                "description": "A test dataset",
                "labels": {"env": "test"},
            },
        )
        assert isinstance(dataset, BigQueryDataset)
        assert dataset.dataset_id == "test_dataset"

    def test_create_dataset_minimal(
        self, mock_google_client, sample_dataset_response
    ):
        """Test creating a dataset with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_insert = mock_google_client.datasets.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.return_value = sample_dataset_response

        service = BigQueryService(project_id="test-project")
        service.create_dataset(dataset_id="test_dataset")

        mock_insert.assert_called_once_with(
            projectId="test-project",
            body={
                "datasetReference": {
                    "datasetId": "test_dataset",
                    "projectId": "test-project",
                },
                "location": "US",
            },
        )

    def test_create_dataset_conflict(self, mock_google_client):
        """Test creating a dataset that already exists."""
        mock_insert = mock_google_client.datasets.return_value.insert
        mock_insert.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        service = BigQueryService(project_id="test-project")

        with pytest.raises(APIError) as exc_info:
            service.create_dataset(dataset_id="existing_dataset")
        assert exc_info.value.status_code == 409

    def test_delete_dataset(self, mock_google_client):
        """Test deleting a dataset."""
        mock_request = mock.MagicMock()
        mock_delete = mock_google_client.datasets.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = BigQueryService(project_id="test-project")
        result = service.delete_dataset("test_dataset")

        mock_delete.assert_called_once_with(
            projectId="test-project",
            datasetId="test_dataset",
            deleteContents=False,
        )
        assert result is True

    def test_delete_dataset_with_contents(self, mock_google_client):
        """Test deleting a dataset with delete_contents=True."""
        mock_request = mock.MagicMock()
        mock_delete = mock_google_client.datasets.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = BigQueryService(project_id="test-project")
        result = service.delete_dataset("test_dataset", delete_contents=True)

        mock_delete.assert_called_once_with(
            projectId="test-project",
            datasetId="test_dataset",
            deleteContents=True,
        )
        assert result is True

    def test_delete_dataset_not_found(self, mock_google_client):
        """Test deleting a dataset that does not exist."""
        mock_delete = mock_google_client.datasets.return_value.delete
        mock_delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigQueryService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.delete_dataset("nonexistent_dataset")


class TestBigQueryTables:
    """Tests for BigQuery table operations."""

    def test_list_tables(self, mock_google_client, sample_table_response):
        """Test listing tables in a dataset."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.tables.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "tables": [sample_table_response, sample_table_response]
        }

        mock_list_next = mock_google_client.tables.return_value.list_next
        mock_list_next.return_value = None

        service = BigQueryService(project_id="test-project")
        tables = service.list_tables("test_dataset")

        mock_list.assert_called_once_with(
            projectId="test-project", datasetId="test_dataset"
        )
        assert len(tables) == 2
        assert isinstance(tables[0], BigQueryTable)
        assert tables[0].table_id == "test_table"
        assert tables[0].dataset_id == "test_dataset"

    def test_list_tables_empty(self, mock_google_client):
        """Test listing tables when none exist."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.tables.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = mock_google_client.tables.return_value.list_next
        mock_list_next.return_value = None

        service = BigQueryService(project_id="test-project")
        tables = service.list_tables("test_dataset")

        assert len(tables) == 0

    def test_list_tables_pagination(
        self, mock_google_client, sample_table_response
    ):
        """Test listing tables with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = mock_google_client.tables.return_value.list
        mock_list.return_value = mock_request_page1

        mock_request_page1.execute.return_value = {
            "tables": [sample_table_response]
        }
        mock_request_page2.execute.return_value = {
            "tables": [sample_table_response]
        }

        mock_list_next = mock_google_client.tables.return_value.list_next
        mock_list_next.side_effect = [mock_request_page2, None]

        service = BigQueryService(project_id="test-project")
        tables = service.list_tables("test_dataset")

        assert len(tables) == 2

    def test_get_table(self, mock_google_client, sample_table_response):
        """Test getting a specific table."""
        mock_request = mock.MagicMock()
        mock_get = mock_google_client.tables.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_table_response

        service = BigQueryService(project_id="test-project")
        table = service.get_table("test_dataset", "test_table")

        mock_get.assert_called_once_with(
            projectId="test-project",
            datasetId="test_dataset",
            tableId="test_table",
        )
        assert isinstance(table, BigQueryTable)
        assert table.table_id == "test_table"
        assert table.dataset_id == "test_dataset"
        assert table.friendly_name == "Test Table"
        assert table.num_rows == 1000
        assert table.num_bytes == 50000
        assert table.table_type == "TABLE"
        assert len(table.schema_fields) == 3
        assert table.time_partitioning == {"type": "DAY", "field": "created_at"}
        assert table.clustering_fields == ["name"]

    def test_get_table_not_found(self, mock_google_client):
        """Test getting a table that does not exist."""
        mock_get = mock_google_client.tables.return_value.get
        mock_get.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigQueryService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_table("test_dataset", "nonexistent_table")

    def test_create_table(self, mock_google_client, sample_table_response):
        """Test creating a new table."""
        mock_request = mock.MagicMock()
        mock_insert = mock_google_client.tables.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.return_value = sample_table_response

        schema_fields = [
            {"name": "id", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "name", "type": "STRING", "mode": "NULLABLE"},
        ]

        service = BigQueryService(project_id="test-project")
        table = service.create_table(
            dataset_id="test_dataset",
            table_id="test_table",
            schema_fields=schema_fields,
            description="A test table",
            time_partitioning={"type": "DAY", "field": "created_at"},
            clustering_fields=["name"],
        )

        mock_insert.assert_called_once_with(
            projectId="test-project",
            datasetId="test_dataset",
            body={
                "tableReference": {
                    "tableId": "test_table",
                    "datasetId": "test_dataset",
                    "projectId": "test-project",
                },
                "schema": {"fields": schema_fields},
                "description": "A test table",
                "timePartitioning": {"type": "DAY", "field": "created_at"},
                "clustering": {"fields": ["name"]},
            },
        )
        assert isinstance(table, BigQueryTable)
        assert table.table_id == "test_table"

    def test_create_table_minimal(
        self, mock_google_client, sample_table_response
    ):
        """Test creating a table with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_insert = mock_google_client.tables.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.return_value = sample_table_response

        service = BigQueryService(project_id="test-project")
        service.create_table(
            dataset_id="test_dataset",
            table_id="test_table",
        )

        mock_insert.assert_called_once_with(
            projectId="test-project",
            datasetId="test_dataset",
            body={
                "tableReference": {
                    "tableId": "test_table",
                    "datasetId": "test_dataset",
                    "projectId": "test-project",
                },
            },
        )

    def test_create_table_conflict(self, mock_google_client):
        """Test creating a table that already exists."""
        mock_insert = mock_google_client.tables.return_value.insert
        mock_insert.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        service = BigQueryService(project_id="test-project")

        with pytest.raises(APIError) as exc_info:
            service.create_table(
                dataset_id="test_dataset", table_id="existing_table"
            )
        assert exc_info.value.status_code == 409

    def test_delete_table(self, mock_google_client):
        """Test deleting a table."""
        mock_request = mock.MagicMock()
        mock_delete = mock_google_client.tables.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = BigQueryService(project_id="test-project")
        result = service.delete_table("test_dataset", "test_table")

        mock_delete.assert_called_once_with(
            projectId="test-project",
            datasetId="test_dataset",
            tableId="test_table",
        )
        assert result is True

    def test_delete_table_not_found(self, mock_google_client):
        """Test deleting a table that does not exist."""
        mock_delete = mock_google_client.tables.return_value.delete
        mock_delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigQueryService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.delete_table("test_dataset", "nonexistent_table")


class TestBigQueryQueries:
    """Tests for BigQuery query operations."""

    def test_query(self, mock_google_client):
        """Test executing a query."""
        mock_request = mock.MagicMock()
        mock_query = mock_google_client.jobs.return_value.query
        mock_query.return_value = mock_request

        query_response = {
            "kind": "bigquery#queryResponse",
            "schema": {
                "fields": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "name", "type": "STRING"},
                ]
            },
            "rows": [
                {"f": [{"v": "1"}, {"v": "Alice"}]},
                {"f": [{"v": "2"}, {"v": "Bob"}]},
            ],
            "totalRows": "2",
            "jobComplete": True,
        }
        mock_request.execute.return_value = query_response

        service = BigQueryService(project_id="test-project")
        result = service.query("SELECT id, name FROM `test_dataset.test_table`")

        mock_query.assert_called_once_with(
            projectId="test-project",
            body={
                "query": "SELECT id, name FROM `test_dataset.test_table`",
                "useLegacySql": False,
                "dryRun": False,
            },
        )
        assert result["jobComplete"] is True
        assert result["totalRows"] == "2"
        assert len(result["rows"]) == 2

    def test_query_legacy_sql(self, mock_google_client):
        """Test executing a query with legacy SQL."""
        mock_request = mock.MagicMock()
        mock_query = mock_google_client.jobs.return_value.query
        mock_query.return_value = mock_request
        mock_request.execute.return_value = {"jobComplete": True}

        service = BigQueryService(project_id="test-project")
        service.query(
            "SELECT * FROM [test_dataset.test_table]",
            use_legacy_sql=True,
        )

        mock_query.assert_called_once_with(
            projectId="test-project",
            body={
                "query": "SELECT * FROM [test_dataset.test_table]",
                "useLegacySql": True,
                "dryRun": False,
            },
        )

    def test_query_dry_run(self, mock_google_client):
        """Test executing a dry run query."""
        mock_request = mock.MagicMock()
        mock_query = mock_google_client.jobs.return_value.query
        mock_query.return_value = mock_request

        dry_run_response = {
            "kind": "bigquery#queryResponse",
            "jobComplete": True,
            "totalBytesProcessed": "50000",
        }
        mock_request.execute.return_value = dry_run_response

        service = BigQueryService(project_id="test-project")
        result = service.query(
            "SELECT * FROM `test_dataset.test_table`", dry_run=True
        )

        mock_query.assert_called_once_with(
            projectId="test-project",
            body={
                "query": "SELECT * FROM `test_dataset.test_table`",
                "useLegacySql": False,
                "dryRun": True,
            },
        )
        assert result["totalBytesProcessed"] == "50000"

    def test_query_with_kwargs(self, mock_google_client):
        """Test executing a query with additional parameters."""
        mock_request = mock.MagicMock()
        mock_query = mock_google_client.jobs.return_value.query
        mock_query.return_value = mock_request
        mock_request.execute.return_value = {"jobComplete": True}

        service = BigQueryService(project_id="test-project")
        service.query(
            "SELECT * FROM `test_dataset.test_table`",
            maxResults=100,
            timeoutMs=30000,
        )

        mock_query.assert_called_once_with(
            projectId="test-project",
            body={
                "query": "SELECT * FROM `test_dataset.test_table`",
                "useLegacySql": False,
                "dryRun": False,
                "maxResults": 100,
                "timeoutMs": 30000,
            },
        )

    def test_query_api_error(self, mock_google_client):
        """Test query that triggers an API error."""
        mock_query = mock_google_client.jobs.return_value.query
        mock_query.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        service = BigQueryService(project_id="test-project")

        with pytest.raises(APIError) as exc_info:
            service.query("INVALID SQL")
        assert exc_info.value.status_code == 400


class TestBigQueryJobs:
    """Tests for BigQuery job operations."""

    def test_get_job(self, mock_google_client, sample_job_response):
        """Test getting a specific job."""
        mock_request = mock.MagicMock()
        mock_get = mock_google_client.jobs.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_job_response

        service = BigQueryService(project_id="test-project")
        job = service.get_job("job_abc123")

        mock_get.assert_called_once_with(
            projectId="test-project", jobId="job_abc123"
        )
        assert isinstance(job, BigQueryJob)
        assert job.job_id == "job_abc123"
        assert job.job_type == "query"
        assert job.state == "DONE"
        assert job.user_email == "user@example.com"
        assert job.start_time == "1609459200000"
        assert job.end_time == "1609459210000"
        assert job.error_result is None

    def test_get_job_with_error(
        self, mock_google_client, sample_job_response_with_error
    ):
        """Test getting a job that has an error."""
        mock_request = mock.MagicMock()
        mock_get = mock_google_client.jobs.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_job_response_with_error

        service = BigQueryService(project_id="test-project")
        job = service.get_job("job_err456")

        assert isinstance(job, BigQueryJob)
        assert job.job_id == "job_err456"
        assert job.state == "DONE"
        assert job.error_result is not None
        assert job.error_result["reason"] == "invalidQuery"
        assert job.error_result["message"] == "Syntax error in SQL query"

    def test_get_job_not_found(self, mock_google_client):
        """Test getting a job that does not exist."""
        mock_get = mock_google_client.jobs.return_value.get
        mock_get.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigQueryService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_job("nonexistent_job")

    def test_list_jobs(self, mock_google_client, sample_job_response):
        """Test listing jobs."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.jobs.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "jobs": [sample_job_response, sample_job_response]
        }

        mock_list_next = mock_google_client.jobs.return_value.list_next
        mock_list_next.return_value = None

        service = BigQueryService(project_id="test-project")
        jobs = service.list_jobs()

        mock_list.assert_called_once_with(projectId="test-project")
        assert len(jobs) == 2
        assert isinstance(jobs[0], BigQueryJob)
        assert jobs[0].job_id == "job_abc123"

    def test_list_jobs_empty(self, mock_google_client):
        """Test listing jobs when none exist."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.jobs.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = mock_google_client.jobs.return_value.list_next
        mock_list_next.return_value = None

        service = BigQueryService(project_id="test-project")
        jobs = service.list_jobs()

        assert len(jobs) == 0

    def test_list_jobs_with_kwargs(self, mock_google_client, sample_job_response):
        """Test listing jobs with additional filters."""
        mock_request = mock.MagicMock()
        mock_list = mock_google_client.jobs.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "jobs": [sample_job_response]
        }

        mock_list_next = mock_google_client.jobs.return_value.list_next
        mock_list_next.return_value = None

        service = BigQueryService(project_id="test-project")
        service.list_jobs(stateFilter="done", maxResults=10)

        mock_list.assert_called_once_with(
            projectId="test-project",
            stateFilter="done",
            maxResults=10,
        )

    def test_list_jobs_pagination(
        self, mock_google_client, sample_job_response
    ):
        """Test listing jobs with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = mock_google_client.jobs.return_value.list
        mock_list.return_value = mock_request_page1

        mock_request_page1.execute.return_value = {
            "jobs": [sample_job_response]
        }
        mock_request_page2.execute.return_value = {
            "jobs": [sample_job_response]
        }

        mock_list_next = mock_google_client.jobs.return_value.list_next
        mock_list_next.side_effect = [mock_request_page2, None]

        service = BigQueryService(project_id="test-project")
        jobs = service.list_jobs()

        assert len(jobs) == 2

    def test_cancel_job(self, mock_google_client):
        """Test cancelling a job."""
        mock_request = mock.MagicMock()
        mock_cancel = mock_google_client.jobs.return_value.cancel
        mock_cancel.return_value = mock_request
        mock_request.execute.return_value = {
            "kind": "bigquery#jobCancelResponse",
            "job": {"status": {"state": "DONE"}},
        }

        service = BigQueryService(project_id="test-project")
        result = service.cancel_job("job_abc123")

        mock_cancel.assert_called_once_with(
            projectId="test-project", jobId="job_abc123"
        )
        assert result is True

    def test_cancel_job_not_found(self, mock_google_client):
        """Test cancelling a job that does not exist."""
        mock_cancel = mock_google_client.jobs.return_value.cancel
        mock_cancel.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = BigQueryService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.cancel_job("nonexistent_job")


class TestBigQueryModels:
    """Tests for BigQuery model parsing."""

    def test_dataset_from_api_response(self, sample_dataset_response):
        """Test creating a BigQueryDataset from an API response."""
        dataset = BigQueryDataset.from_api_response(sample_dataset_response)

        assert dataset.dataset_id == "test_dataset"
        assert dataset.project == "test-project"
        assert dataset.friendly_name == "Test Dataset"
        assert dataset.description == "A test dataset"
        assert dataset.location == "US"
        assert len(dataset.access) == 3
        assert dataset.labels == {"env": "test", "team": "data"}

    def test_dataset_get_tag(self, sample_dataset_response):
        """Test get_tag on a BigQueryDataset."""
        dataset = BigQueryDataset.from_api_response(sample_dataset_response)

        assert dataset.get_tag("env") == "test"
        assert dataset.get_tag("team") == "data"
        assert dataset.get_tag("nonexistent") == ""
        assert dataset.get_tag("nonexistent", "default") == "default"

    def test_table_from_api_response(self, sample_table_response):
        """Test creating a BigQueryTable from an API response."""
        table = BigQueryTable.from_api_response(sample_table_response)

        assert table.table_id == "test_table"
        assert table.dataset_id == "test_dataset"
        assert table.project == "test-project"
        assert table.friendly_name == "Test Table"
        assert table.num_rows == 1000
        assert table.num_bytes == 50000
        assert table.table_type == "TABLE"
        assert len(table.schema_fields) == 3
        assert table.schema_fields[0]["name"] == "id"
        assert table.time_partitioning == {"type": "DAY", "field": "created_at"}
        assert table.clustering_fields == ["name"]

    def test_table_get_tag(self, sample_table_response):
        """Test get_tag on a BigQueryTable."""
        table = BigQueryTable.from_api_response(sample_table_response)

        assert table.get_tag("env") == "test"
        assert table.get_tag("nonexistent") == ""

    def test_table_from_api_response_no_schema(self):
        """Test creating a BigQueryTable with no schema."""
        response = {
            "id": "test-project:ds.tbl",
            "tableReference": {
                "tableId": "tbl",
                "datasetId": "ds",
                "projectId": "test-project",
            },
            "type": "VIEW",
        }
        table = BigQueryTable.from_api_response(response)

        assert table.table_id == "tbl"
        assert table.table_type == "VIEW"
        assert table.schema_fields == []
        assert table.clustering_fields is None

    def test_job_from_api_response(self, sample_job_response):
        """Test creating a BigQueryJob from an API response."""
        job = BigQueryJob.from_api_response(sample_job_response)

        assert job.job_id == "job_abc123"
        assert job.project == "test-project"
        assert job.job_type == "query"
        assert job.state == "DONE"
        assert job.user_email == "user@example.com"
        assert job.error_result is None
        assert job.statistics["totalBytesProcessed"] == "50000"

    def test_job_from_api_response_with_error(
        self, sample_job_response_with_error
    ):
        """Test creating a BigQueryJob from an API response with error."""
        job = BigQueryJob.from_api_response(sample_job_response_with_error)

        assert job.job_id == "job_err456"
        assert job.state == "DONE"
        assert job.error_result is not None
        assert job.error_result["reason"] == "invalidQuery"

    def test_job_get_tag(self, sample_job_response):
        """Test get_tag on a BigQueryJob."""
        job = BigQueryJob.from_api_response(sample_job_response)

        assert job.get_tag("team") == "analytics"
        assert job.get_tag("nonexistent") == ""
        assert job.get_tag("nonexistent", "default") == "default"
