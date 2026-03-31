"""Service implementation for Google Cloud Batch."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.batch import BatchJob, BatchTask
from gcpoto.exceptions import (
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class BatchService(GCPService[BatchJob]):
    """Service for interacting with Google Cloud Batch."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Batch service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="batch",
            version="v1",
            credentials_file=credentials_file,
            resource_model=BatchJob,
            **kwargs,
        )

    def _format_location_path(self, location: str) -> str:
        """Format a fully qualified location path.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            The fully qualified location resource path
        """
        return f"projects/{self.project_id}/locations/{location}"

    def _format_job_path(self, location: str, job_name: str) -> str:
        """Format a fully qualified job path.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_name: The job name or full path

        Returns:
            The fully qualified job resource path
        """
        if "/" in job_name:
            return job_name
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/jobs/{job_name}"
        )

    def _format_task_group_path(
        self, location: str, job_name: str, task_group: str
    ) -> str:
        """Format a fully qualified task group path.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_name: The job name
            task_group: The task group name

        Returns:
            The fully qualified task group resource path
        """
        job_path = self._format_job_path(location, job_name)
        return f"{job_path}/taskGroups/{task_group}"

    def list_jobs(self, location: str, **kwargs) -> List[BatchJob]:
        """List Batch jobs in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of BatchJob instances
        """
        parent = self._format_location_path(location)

        request = (
            self.service.projects()
            .locations()
            .jobs()
            .list(parent=parent, **kwargs)
        )

        jobs = []
        while request is not None:
            response = request.execute()
            for item in response.get("jobs", []):
                jobs.append(
                    BatchJob.from_api_response(item, self.project_id)
                )

            request = (
                self.service.projects()
                .locations()
                .jobs()
                .list_next(request, response)
            )

        logger.debug("Listed %s jobs in %s", len(jobs), location)
        return jobs

    def get_job(self, location: str, job_name: str) -> BatchJob:
        """Get a specific Batch job.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_name: The name of the job to retrieve

        Returns:
            A BatchJob instance
        """
        name = self._format_job_path(location, job_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .jobs()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("job", job_name)
            raise

        logger.debug("Retrieved job %s", job_name)
        return BatchJob.from_api_response(response, self.project_id)

    def create_job(
        self,
        location: str,
        job_id: str,
        task_groups: List[Dict[str, Any]],
        allocation_policy: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> BatchJob:
        """Create a new Batch job.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_id: The ID for the new job
            task_groups: Task group configurations for the job
            allocation_policy: Optional compute resource allocation policy
            labels: Optional labels for the job

        Returns:
            A BatchJob instance for the newly created job
        """
        parent = self._format_location_path(location)

        body: Dict[str, Any] = {
            "taskGroups": task_groups,
        }

        if allocation_policy is not None:
            body["allocationPolicy"] = allocation_policy

        if labels is not None:
            body["labels"] = labels

        try:
            request = (
                self.service.projects()
                .locations()
                .jobs()
                .create(parent=parent, body=body, jobId=job_id)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"Job '{job_id}' already exists"
                )
            raise

        logger.debug("Created job %s in %s", job_id, location)
        return BatchJob.from_api_response(response, self.project_id)

    def delete_job(self, location: str, job_name: str) -> bool:
        """Delete a Batch job.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_name: The name of the job to delete

        Returns:
            True if the deletion was successful
        """
        name = self._format_job_path(location, job_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .jobs()
                .delete(name=name)
            )
            request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("job", job_name)
            raise

        logger.debug("Deleted job %s in %s", job_name, location)
        return True

    def list_tasks(
        self,
        location: str,
        job_name: str,
        task_group: str = "group0",
        **kwargs,
    ) -> List[BatchTask]:
        """List tasks in a Batch job task group.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_name: The name of the job
            task_group: The task group name (default: 'group0')
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of BatchTask instances
        """
        parent = self._format_task_group_path(location, job_name, task_group)

        request = (
            self.service.projects()
            .locations()
            .jobs()
            .taskGroups()
            .tasks()
            .list(parent=parent, **kwargs)
        )

        tasks = []
        while request is not None:
            response = request.execute()
            for item in response.get("tasks", []):
                tasks.append(
                    BatchTask.from_api_response(item, self.project_id)
                )

            request = (
                self.service.projects()
                .locations()
                .jobs()
                .taskGroups()
                .tasks()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s tasks in job %s group %s",
            len(tasks),
            job_name,
            task_group,
        )
        return tasks
