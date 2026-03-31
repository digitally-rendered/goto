"""Service implementation for Google Cloud Scheduler."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.scheduler import SchedulerJob
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


def format_job_path(project_id: str, location: str, job_name: str) -> str:
    """Return full projects/{project}/locations/{location}/jobs/{job} path.

    Args:
        project_id: The GCP project ID.
        location: The GCP location (region).
        job_name: Either a short job name or a full resource path.

    Returns:
        The fully-qualified job resource path.
    """
    if "/" not in job_name:
        return f"projects/{project_id}/locations/{location}/jobs/{job_name}"
    return job_name


def format_location_path(project_id: str, location: str) -> str:
    """Return full projects/{project}/locations/{location} path.

    Args:
        project_id: The GCP project ID.
        location: The GCP location (region).

    Returns:
        The fully-qualified location resource path.
    """
    return f"projects/{project_id}/locations/{location}"


class SchedulerService(GCPService[SchedulerJob]):
    """Service for interacting with Google Cloud Scheduler."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Scheduler service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="cloudscheduler",
            version="v1",
            credentials_file=credentials_file,
            resource_model=SchedulerJob,
            **kwargs,
        )

    def list_jobs(self, location: str, **kwargs) -> List[SchedulerJob]:
        """List Cloud Scheduler jobs in a location.

        Args:
            location: The GCP location (region) to list jobs in
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of SchedulerJob instances
        """
        parent = format_location_path(self.project_id, location)

        jobs = []
        request = (
            self.service.projects()
            .locations()
            .jobs()
            .list(parent=parent, **kwargs)
        )

        while request is not None:
            response = request.execute()
            for job_data in response.get("jobs", []):
                jobs.append(
                    SchedulerJob.from_api_response(job_data, self.project_id)
                )

            request = (
                self.service.projects()
                .locations()
                .jobs()
                .list_next(request, response)
            )

        logger.info("Listed %s jobs in location %s", len(jobs), location)
        return jobs

    def get_job(self, location: str, job_name: str) -> SchedulerJob:
        """Get a specific Cloud Scheduler job.

        Args:
            location: The GCP location (region) of the job
            job_name: The name of the job to retrieve

        Returns:
            A SchedulerJob instance
        """
        full_name = format_job_path(self.project_id, location, job_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .jobs()
                .get(name=full_name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SchedulerJob", job_name)
            raise APIError(e.resp.status, str(e))

        logger.info("Retrieved job %s", job_name)
        return SchedulerJob.from_api_response(response, self.project_id)

    def create_job(
        self,
        location: str,
        job_name: str,
        schedule: str,
        time_zone: str,
        http_target: Optional[Dict[str, Any]] = None,
        pubsub_target: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        retry_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SchedulerJob:
        """Create a new Cloud Scheduler job.

        Args:
            location: The GCP location (region) for the job
            job_name: The name of the job to create
            schedule: Cron expression for the job schedule
            time_zone: The time zone for the cron schedule
            http_target: Optional HTTP target configuration
            pubsub_target: Optional Pub/Sub target configuration
            description: Optional human-readable description
            retry_config: Optional retry configuration
            **kwargs: Additional parameters to pass to the create request

        Returns:
            A SchedulerJob instance for the newly created job
        """
        parent = format_location_path(self.project_id, location)
        full_name = format_job_path(self.project_id, location, job_name)

        body = {
            "name": full_name,
            "schedule": schedule,
            "timeZone": time_zone,
        }

        if description is not None:
            body["description"] = description

        if http_target is not None:
            body["httpTarget"] = http_target

        if pubsub_target is not None:
            body["pubsubTarget"] = pubsub_target

        if retry_config is not None:
            body["retryConfig"] = retry_config

        # Process tags if provided
        tags = kwargs.pop("tags", None)
        body = self._process_tags(body, tags)

        # Add any remaining kwargs to the body
        for key, value in kwargs.items():
            body[key] = value

        try:
            request = (
                self.service.projects()
                .locations()
                .jobs()
                .create(parent=parent, body=body)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 409:
                raise ValueError(f"Job '{job_name}' already exists")
            raise APIError(e.resp.status, str(e))

        logger.info("Created job %s in location %s", job_name, location)
        return SchedulerJob.from_api_response(response, self.project_id)

    def update_job(
        self, location: str, job_name: str, update_fields: Dict[str, Any]
    ) -> SchedulerJob:
        """Update an existing Cloud Scheduler job.

        Args:
            location: The GCP location (region) of the job
            job_name: The name of the job to update
            update_fields: Dictionary of fields to update

        Returns:
            The updated SchedulerJob instance
        """
        full_name = format_job_path(self.project_id, location, job_name)

        body = dict(update_fields)
        body["name"] = full_name

        update_mask = ",".join(update_fields.keys())

        try:
            request = (
                self.service.projects()
                .locations()
                .jobs()
                .patch(name=full_name, body=body, updateMask=update_mask)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SchedulerJob", job_name)
            raise APIError(e.resp.status, str(e))

        logger.info("Updated job %s", job_name)
        return SchedulerJob.from_api_response(response, self.project_id)

    def delete_job(self, location: str, job_name: str) -> bool:
        """Delete a Cloud Scheduler job.

        Args:
            location: The GCP location (region) of the job
            job_name: The name of the job to delete

        Returns:
            True if the deletion was successful
        """
        full_name = format_job_path(self.project_id, location, job_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .jobs()
                .delete(name=full_name)
            )
            request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SchedulerJob", job_name)
            raise APIError(e.resp.status, str(e))

        logger.info("Deleted job %s", job_name)
        return True

    def pause_job(self, location: str, job_name: str) -> SchedulerJob:
        """Pause a Cloud Scheduler job.

        Args:
            location: The GCP location (region) of the job
            job_name: The name of the job to pause

        Returns:
            The paused SchedulerJob instance
        """
        full_name = format_job_path(self.project_id, location, job_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .jobs()
                .pause(name=full_name, body={})
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SchedulerJob", job_name)
            raise APIError(e.resp.status, str(e))

        logger.info("Paused job %s", job_name)
        return SchedulerJob.from_api_response(response, self.project_id)

    def resume_job(self, location: str, job_name: str) -> SchedulerJob:
        """Resume a paused Cloud Scheduler job.

        Args:
            location: The GCP location (region) of the job
            job_name: The name of the job to resume

        Returns:
            The resumed SchedulerJob instance
        """
        full_name = format_job_path(self.project_id, location, job_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .jobs()
                .resume(name=full_name, body={})
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SchedulerJob", job_name)
            raise APIError(e.resp.status, str(e))

        logger.info("Resumed job %s", job_name)
        return SchedulerJob.from_api_response(response, self.project_id)

    def run_job(self, location: str, job_name: str) -> SchedulerJob:
        """Force run a Cloud Scheduler job immediately.

        Args:
            location: The GCP location (region) of the job
            job_name: The name of the job to run

        Returns:
            The SchedulerJob instance after triggering the run
        """
        full_name = format_job_path(self.project_id, location, job_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .jobs()
                .run(name=full_name, body={})
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SchedulerJob", job_name)
            raise APIError(e.resp.status, str(e))

        logger.info("Triggered run for job %s", job_name)
        return SchedulerJob.from_api_response(response, self.project_id)
