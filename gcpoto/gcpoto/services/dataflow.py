"""Service implementation for Google Cloud Dataflow."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.dataflow import DataflowJob, DataflowTemplate

logger = logging.getLogger(__name__)

class DataflowService(GCPService[DataflowJob]):
    """Service for interacting with Google Cloud Dataflow."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Dataflow service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="dataflow",
            version="v1b3",
            credentials_file=credentials_file,
            resource_model=DataflowJob,
            **kwargs,
        )

    def list_jobs(self, location: str, **kwargs) -> List[DataflowJob]:
        """List Dataflow jobs in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of DataflowJob instances
        """
        request = (
            self.service.projects()
            .locations()
            .jobs()
            .list(
                projectId=self.project_id,
                location=location,
                **kwargs,
            )
        )

        jobs = []
        while request is not None:
            response = self._execute(request)
            for job_data in response.get("jobs", []):
                jobs.append(
                    DataflowJob.from_api_response(job_data, self.project_id)
                )

            request = (
                self.service.projects()
                .locations()
                .jobs()
                .list_next(request, response)
            )

        logger.debug("Listed %s jobs in %s", len(jobs), location)
        return jobs

    def get_job(self, location: str, job_id: str) -> DataflowJob:
        """Get a specific Dataflow job.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_id: The ID of the job to retrieve

        Returns:
            A DataflowJob instance
        """
        request = (
            self.service.projects()
            .locations()
            .jobs()
            .get(
                projectId=self.project_id,
                location=location,
                jobId=job_id,
            )
        )
        response = self._execute(request, "job", job_id)
        logger.debug("Retrieved job %s", job_id)
        return DataflowJob.from_api_response(response, self.project_id)

    def create_job(
        self, location: str, job_body: Dict[str, Any]
    ) -> DataflowJob:
        """Create a new Dataflow job.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_body: The job configuration body

        Returns:
            A DataflowJob instance for the newly created job
        """
        request = (
            self.service.projects()
            .locations()
            .jobs()
            .create(
                projectId=self.project_id,
                location=location,
                body=job_body,
            )
        )
        response = self._execute(request)
        logger.debug("Created job in %s", location)
        return DataflowJob.from_api_response(response, self.project_id)

    def update_job(
        self, location: str, job_id: str, requested_state: str
    ) -> DataflowJob:
        """Update a Dataflow job's requested state.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_id: The ID of the job to update
            requested_state: The new requested state for the job

        Returns:
            The updated DataflowJob instance
        """
        body = {"requestedState": requested_state}

        request = (
            self.service.projects()
            .locations()
            .jobs()
            .update(
                projectId=self.project_id,
                location=location,
                jobId=job_id,
                body=body,
            )
        )
        response = self._execute(request, "job", job_id)
        logger.debug("Updated job %s to state %s", job_id, requested_state)
        return DataflowJob.from_api_response(response, self.project_id)

    def cancel_job(self, location: str, job_id: str) -> DataflowJob:
        """Cancel a running Dataflow job.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_id: The ID of the job to cancel

        Returns:
            The updated DataflowJob instance
        """
        logger.debug("Cancelling job %s in %s", job_id, location)
        return self.update_job(location, job_id, "JOB_STATE_CANCELLED")

    def drain_job(self, location: str, job_id: str) -> DataflowJob:
        """Drain a running Dataflow streaming job.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_id: The ID of the job to drain

        Returns:
            The updated DataflowJob instance
        """
        logger.debug("Draining job %s in %s", job_id, location)
        return self.update_job(location, job_id, "JOB_STATE_DRAINED")

    def launch_template(
        self,
        location: str,
        template_gcs_path: str,
        job_name: str,
        parameters: Optional[Dict[str, str]] = None,
        environment: Optional[Dict[str, Any]] = None,
    ) -> DataflowTemplate:
        """Launch a Dataflow template.

        Args:
            location: The GCP location (e.g. 'us-central1')
            template_gcs_path: The GCS path to the template
            job_name: The name for the launched job
            parameters: Optional runtime parameters for the template
            environment: Optional environment configuration

        Returns:
            A DataflowTemplate instance for the launched template
        """
        launch_params: Dict[str, Any] = {"jobName": job_name}

        if parameters is not None:
            launch_params["parameters"] = parameters

        if environment is not None:
            launch_params["environment"] = environment

        request = (
            self.service.projects()
            .locations()
            .templates()
            .launch(
                projectId=self.project_id,
                location=location,
                gcsPath=template_gcs_path,
                body={"launchParameters": launch_params},
            )
        )
        response = self._execute(request, "template", template_gcs_path)
        logger.debug(
            "Launched template %s as job %s in %s",
            template_gcs_path,
            job_name,
            location,
        )
        return DataflowTemplate.from_api_response(response, self.project_id)

    def list_job_messages(
        self,
        location: str,
        job_id: str,
        minimum_importance: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """List messages for a Dataflow job.

        Args:
            location: The GCP location (e.g. 'us-central1')
            job_id: The ID of the job to list messages for
            minimum_importance: Optional minimum importance level filter
                (JOB_MESSAGE_DEBUG, JOB_MESSAGE_DETAILED,
                 JOB_MESSAGE_BASIC, JOB_MESSAGE_WARNING,
                 JOB_MESSAGE_ERROR)
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of job message dictionaries
        """
        list_kwargs: Dict[str, Any] = {
            "projectId": self.project_id,
            "location": location,
            "jobId": job_id,
        }

        if minimum_importance is not None:
            list_kwargs["minimumImportance"] = minimum_importance

        list_kwargs.update(kwargs)

        request = (
            self.service.projects()
            .locations()
            .jobs()
            .messages()
            .list(**list_kwargs)
        )

        messages = []
        while request is not None:
            response = self._execute(request)
            for message in response.get("jobMessages", []):
                messages.append(message)

            request = (
                self.service.projects()
                .locations()
                .jobs()
                .messages()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s messages for job %s", len(messages), job_id
        )
        return messages
