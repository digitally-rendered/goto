"""Service implementation for Google Cloud BigQuery."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.bigquery import BigQueryDataset, BigQueryTable, BigQueryJob
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class BigQueryService(GCPService[BigQueryDataset]):
    """Service for interacting with Google Cloud BigQuery."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the BigQuery service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="bigquery",
            version="v2",
            credentials_file=credentials_file,
            resource_model=BigQueryDataset,
            **kwargs,
        )

    def list_datasets(self, **kwargs) -> List[BigQueryDataset]:
        """List BigQuery datasets in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of BigQueryDataset instances
        """
        logger.debug("Listing datasets for project %s", self.project_id)

        datasets = []
        request = self.service.datasets().list(
            projectId=self.project_id, **kwargs
        )

        while request is not None:
            response = request.execute()
            for dataset_data in response.get("datasets", []):
                datasets.append(
                    BigQueryDataset.from_api_response(
                        dataset_data, self.project_id
                    )
                )
            request = self.service.datasets().list_next(request, response)

        logger.debug("Found %s datasets", len(datasets))
        return datasets

    def get_dataset(self, dataset_id: str) -> BigQueryDataset:
        """Get a specific BigQuery dataset.

        Args:
            dataset_id: The ID of the dataset to retrieve

        Returns:
            A BigQueryDataset instance
        """
        logger.debug(
            "Getting dataset %s in project %s", dataset_id, self.project_id
        )

        try:
            request = self.service.datasets().get(
                projectId=self.project_id, datasetId=dataset_id
            )
            response = request.execute()
            return BigQueryDataset.from_api_response(response, self.project_id)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("dataset", dataset_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_dataset(
        self,
        dataset_id: str,
        location: str = "US",
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> BigQueryDataset:
        """Create a new BigQuery dataset.

        Args:
            dataset_id: The ID of the dataset to create
            location: The geographic location for the dataset
            description: Optional description for the dataset
            labels: Optional labels to apply to the dataset

        Returns:
            A BigQueryDataset instance for the newly created dataset
        """
        logger.info(
            "Creating dataset %s in project %s", dataset_id, self.project_id
        )

        body: Dict[str, Any] = {
            "datasetReference": {
                "datasetId": dataset_id,
                "projectId": self.project_id,
            },
            "location": location,
        }

        if description is not None:
            body["description"] = description

        if labels is not None:
            body["labels"] = labels

        try:
            request = self.service.datasets().insert(
                projectId=self.project_id, body=body
            )
            response = request.execute()
            return BigQueryDataset.from_api_response(response, self.project_id)
        except HttpError as e:
            if e.resp.status == 409:
                raise APIError(409, f"Dataset '{dataset_id}' already exists")
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def delete_dataset(
        self, dataset_id: str, delete_contents: bool = False
    ) -> bool:
        """Delete a BigQuery dataset.

        Args:
            dataset_id: The ID of the dataset to delete
            delete_contents: If True, delete all tables in the dataset

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting dataset %s in project %s", dataset_id, self.project_id
        )

        try:
            self.service.datasets().delete(
                projectId=self.project_id,
                datasetId=dataset_id,
                deleteContents=delete_contents,
            ).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("dataset", dataset_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def list_tables(self, dataset_id: str, **kwargs) -> List[BigQueryTable]:
        """List tables in a BigQuery dataset.

        Args:
            dataset_id: The ID of the dataset to list tables from
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of BigQueryTable instances
        """
        logger.debug(
            "Listing tables in dataset %s for project %s",
            dataset_id,
            self.project_id,
        )

        tables = []
        request = self.service.tables().list(
            projectId=self.project_id, datasetId=dataset_id, **kwargs
        )

        while request is not None:
            response = request.execute()
            for table_data in response.get("tables", []):
                tables.append(
                    BigQueryTable.from_api_response(
                        table_data, self.project_id
                    )
                )
            request = self.service.tables().list_next(request, response)

        logger.debug("Found %s tables in dataset %s", len(tables), dataset_id)
        return tables

    def get_table(self, dataset_id: str, table_id: str) -> BigQueryTable:
        """Get a specific BigQuery table.

        Args:
            dataset_id: The ID of the dataset containing the table
            table_id: The ID of the table to retrieve

        Returns:
            A BigQueryTable instance
        """
        logger.debug(
            "Getting table %s.%s in project %s",
            dataset_id,
            table_id,
            self.project_id,
        )

        try:
            request = self.service.tables().get(
                projectId=self.project_id,
                datasetId=dataset_id,
                tableId=table_id,
            )
            response = request.execute()
            return BigQueryTable.from_api_response(response, self.project_id)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "table", f"{dataset_id}.{table_id}"
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_table(
        self,
        dataset_id: str,
        table_id: str,
        schema_fields: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        time_partitioning: Optional[Dict[str, Any]] = None,
        clustering_fields: Optional[List[str]] = None,
    ) -> BigQueryTable:
        """Create a new BigQuery table.

        Args:
            dataset_id: The ID of the dataset to create the table in
            table_id: The ID of the table to create
            schema_fields: Optional list of schema field definitions
            description: Optional description for the table
            time_partitioning: Optional time partitioning configuration
            clustering_fields: Optional list of clustering fields

        Returns:
            A BigQueryTable instance for the newly created table
        """
        logger.info(
            "Creating table %s.%s in project %s",
            dataset_id,
            table_id,
            self.project_id,
        )

        body: Dict[str, Any] = {
            "tableReference": {
                "tableId": table_id,
                "datasetId": dataset_id,
                "projectId": self.project_id,
            },
        }

        if schema_fields is not None:
            body["schema"] = {"fields": schema_fields}

        if description is not None:
            body["description"] = description

        if time_partitioning is not None:
            body["timePartitioning"] = time_partitioning

        if clustering_fields is not None:
            body["clustering"] = {"fields": clustering_fields}

        try:
            request = self.service.tables().insert(
                projectId=self.project_id,
                datasetId=dataset_id,
                body=body,
            )
            response = request.execute()
            return BigQueryTable.from_api_response(response, self.project_id)
        except HttpError as e:
            if e.resp.status == 409:
                raise APIError(
                    409,
                    f"Table '{dataset_id}.{table_id}' already exists",
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def delete_table(self, dataset_id: str, table_id: str) -> bool:
        """Delete a BigQuery table.

        Args:
            dataset_id: The ID of the dataset containing the table
            table_id: The ID of the table to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting table %s.%s in project %s",
            dataset_id,
            table_id,
            self.project_id,
        )

        try:
            self.service.tables().delete(
                projectId=self.project_id,
                datasetId=dataset_id,
                tableId=table_id,
            ).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "table", f"{dataset_id}.{table_id}"
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def query(
        self,
        sql: str,
        use_legacy_sql: bool = False,
        dry_run: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute a BigQuery SQL query.

        Args:
            sql: The SQL query string to execute
            use_legacy_sql: Whether to use legacy SQL syntax
            dry_run: If True, only validate the query without executing
            **kwargs: Additional parameters to pass to the query request

        Returns:
            A dictionary containing the query results
        """
        logger.info("Executing query in project %s", self.project_id)
        logger.debug("Query SQL: %s", sql)

        body: Dict[str, Any] = {
            "query": sql,
            "useLegacySql": use_legacy_sql,
            "dryRun": dry_run,
        }

        for key, value in kwargs.items():
            body[key] = value

        try:
            request = self.service.jobs().query(
                projectId=self.project_id, body=body
            )
            response = request.execute()
            return response
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def get_job(self, job_id: str) -> BigQueryJob:
        """Get a specific BigQuery job.

        Args:
            job_id: The ID of the job to retrieve

        Returns:
            A BigQueryJob instance
        """
        logger.debug(
            "Getting job %s in project %s", job_id, self.project_id
        )

        try:
            request = self.service.jobs().get(
                projectId=self.project_id, jobId=job_id
            )
            response = request.execute()
            return BigQueryJob.from_api_response(response, self.project_id)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("job", job_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def list_jobs(self, **kwargs) -> List[BigQueryJob]:
        """List BigQuery jobs in the project.

        Args:
            **kwargs: Additional parameters (e.g., stateFilter, maxResults)

        Returns:
            A list of BigQueryJob instances
        """
        logger.debug("Listing jobs for project %s", self.project_id)

        jobs = []
        request = self.service.jobs().list(
            projectId=self.project_id, **kwargs
        )

        while request is not None:
            response = request.execute()
            for job_data in response.get("jobs", []):
                jobs.append(
                    BigQueryJob.from_api_response(job_data, self.project_id)
                )
            request = self.service.jobs().list_next(request, response)

        logger.debug("Found %s jobs", len(jobs))
        return jobs

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running BigQuery job.

        Args:
            job_id: The ID of the job to cancel

        Returns:
            True if the cancellation was successful
        """
        logger.info(
            "Cancelling job %s in project %s", job_id, self.project_id
        )

        try:
            self.service.jobs().cancel(
                projectId=self.project_id, jobId=job_id
            ).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("job", job_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))
