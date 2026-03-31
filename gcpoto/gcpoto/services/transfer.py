"""Service implementation for Google Cloud Storage Transfer Service."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.transfer import TransferJob, TransferOperation

logger = logging.getLogger(__name__)

class TransferService(GCPService[TransferJob]):
    """Service for interacting with Google Cloud Storage Transfer Service."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Storage Transfer service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="storagetransfer",
            version="v1",
            credentials_file=credentials_file,
            resource_model=TransferJob,
            **kwargs,
        )

    def list_transfer_jobs(
        self, filter_str: Optional[str] = None
    ) -> List[TransferJob]:
        """List transfer jobs in the project.

        Args:
            filter_str: Optional JSON filter string
                (e.g. '{"projectId":"my-project"}')

        Returns:
            A list of TransferJob instances
        """
        if filter_str is None:
            filter_str = f'{{"projectId":"{self.project_id}"}}'

        logger.debug(
            "Listing transfer jobs for project %s", self.project_id
        )

        jobs = []
        request = self.service.transferJobs().list(
            filter=filter_str
        )

        while request is not None:
            response = self._execute(request)
            for job_data in response.get("transferJobs", []):
                jobs.append(
                    TransferJob.from_api_response(job_data, self.project_id)
                )
            request = self.service.transferJobs().list_next(
                request, response
            )

        return jobs

    def get_transfer_job(self, job_name: str) -> TransferJob:
        """Get a specific transfer job.

        Args:
            job_name: The transfer job name
                (e.g. 'transferJobs/12345')

        Returns:
            A TransferJob instance
        """
        logger.debug("Getting transfer job %s", job_name)

        request = self.service.transferJobs().get(
            jobName=job_name, projectId=self.project_id
        )
        response = self._execute(request)

        return TransferJob.from_api_response(response, self.project_id)

    def create_transfer_job(
        self,
        description: str,
        transfer_spec: Dict[str, Any],
        schedule: Optional[Dict[str, Any]] = None,
        notification_config: Optional[Dict[str, Any]] = None,
    ) -> TransferJob:
        """Create a new transfer job.

        Args:
            description: A description for the transfer job
            transfer_spec: The transfer specification
            schedule: Optional schedule configuration
            notification_config: Optional notification configuration

        Returns:
            The created TransferJob instance
        """
        logger.debug(
            "Creating transfer job for project %s", self.project_id
        )

        body: Dict[str, Any] = {
            "projectId": self.project_id,
            "description": description,
            "transferSpec": transfer_spec,
            "status": "ENABLED",
        }

        if schedule is not None:
            body["schedule"] = schedule

        if notification_config is not None:
            body["notificationConfig"] = notification_config

        request = self.service.transferJobs().create(body=body)
        response = self._execute(request)

        return TransferJob.from_api_response(response, self.project_id)

    def update_transfer_job(
        self,
        job_name: str,
        update_fields: Dict[str, Any],
        update_mask: str,
    ) -> TransferJob:
        """Update an existing transfer job.

        Args:
            job_name: The transfer job name (e.g. 'transferJobs/12345')
            update_fields: Dictionary of fields to update
            update_mask: Comma-separated list of fields to update

        Returns:
            The updated TransferJob instance
        """
        logger.debug("Updating transfer job %s", job_name)

        body: Dict[str, Any] = {
            "projectId": self.project_id,
            "transferJob": update_fields,
            "updateTransferJobFieldMask": update_mask,
        }

        request = self.service.transferJobs().patch(
            jobName=job_name, body=body
        )
        response = self._execute(request)

        return TransferJob.from_api_response(response, self.project_id)

    def pause_transfer_job(self, job_name: str) -> None:
        """Pause a transfer job.

        Args:
            job_name: The transfer job name (e.g. 'transferJobs/12345')
        """
        logger.debug("Pausing transfer job %s", job_name)

        body: Dict[str, Any] = {
            "projectId": self.project_id,
            "transferJob": {"status": "DISABLED"},
            "updateTransferJobFieldMask": "status",
        }

        request = self.service.transferJobs().patch(
            jobName=job_name, body=body
        )
        self._execute(request)

    def resume_transfer_job(self, job_name: str) -> None:
        """Resume a paused transfer job.

        Args:
            job_name: The transfer job name (e.g. 'transferJobs/12345')
        """
        logger.debug("Resuming transfer job %s", job_name)

        body: Dict[str, Any] = {
            "projectId": self.project_id,
            "transferJob": {"status": "ENABLED"},
            "updateTransferJobFieldMask": "status",
        }

        request = self.service.transferJobs().patch(
            jobName=job_name, body=body
        )
        self._execute(request)

    def delete_transfer_job(self, job_name: str) -> None:
        """Delete a transfer job (soft delete - sets status to DELETED).

        Args:
            job_name: The transfer job name (e.g. 'transferJobs/12345')
        """
        logger.debug("Deleting transfer job %s", job_name)

        body: Dict[str, Any] = {
            "projectId": self.project_id,
            "transferJob": {"status": "DELETED"},
            "updateTransferJobFieldMask": "status",
        }

        request = self.service.transferJobs().patch(
            jobName=job_name, body=body
        )
        self._execute(request)

    def run_transfer_job(self, job_name: str) -> Dict[str, Any]:
        """Run a transfer job immediately.

        Args:
            job_name: The transfer job name (e.g. 'transferJobs/12345')

        Returns:
            The operation response
        """
        logger.debug("Running transfer job %s", job_name)

        body: Dict[str, Any] = {
            "projectId": self.project_id,
        }

        request = self.service.transferJobs().run(
            jobName=job_name, body=body
        )
        response = self._execute(request)

        return response

    def list_transfer_operations(
        self, job_name: str
    ) -> List[TransferOperation]:
        """List transfer operations for a job.

        Args:
            job_name: The transfer job name (e.g. 'transferJobs/12345')

        Returns:
            A list of TransferOperation instances
        """
        logger.debug(
            "Listing transfer operations for job %s", job_name
        )

        filter_str = (
            f'{{"projectId":"{self.project_id}",'
            f'"jobNames":["{job_name}"]}}'
        )

        operations = []
        request = self.service.transferOperations().list(
            name="transferOperations", filter=filter_str
        )

        while request is not None:
            response = self._execute(request)
            for op_data in response.get("operations", []):
                operations.append(
                    TransferOperation.from_api_response(
                        op_data, self.project_id
                    )
                )
            request = self.service.transferOperations().list_next(
                request, response
            )

        return operations

    def get_transfer_operation(
        self, operation_name: str
    ) -> TransferOperation:
        """Get a specific transfer operation.

        Args:
            operation_name: The operation name
                (e.g. 'transferOperations/12345')

        Returns:
            A TransferOperation instance
        """
        logger.debug("Getting transfer operation %s", operation_name)

        request = self.service.transferOperations().get(
            name=operation_name
        )
        response = self._execute(request)

        return TransferOperation.from_api_response(
            response, self.project_id
        )
