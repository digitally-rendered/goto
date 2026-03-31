"""Service implementation for Google Cloud Dataproc."""

import logging
from typing import List, Optional, Dict, Any

from gcpoto.services.base import GCPService
from gcpoto.models.dataproc import DataprocCluster, DataprocJob

logger = logging.getLogger(__name__)

class DataprocService(GCPService[DataprocCluster]):
    """Service for interacting with Google Cloud Dataproc."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the Dataproc service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="dataproc",
            version="v1",
            credentials_file=credentials_file,
            resource_model=DataprocCluster,
        )

    # --- Cluster methods ---

    def list_clusters(self, region: str) -> List[DataprocCluster]:
        """List Dataproc clusters in a region.

        Args:
            region: The GCP region to list clusters in

        Returns:
            A list of DataprocCluster instances
        """
        logger.debug(
            "Listing Dataproc clusters in project %s, region %s",
            self.project_id,
            region,
        )
        clusters = []
        request = self.service.projects().regions().clusters().list(
            projectId=self.project_id, region=region
        )
        while request is not None:
            response = self._execute(request)
            for item in response.get("clusters", []):
                clusters.append(DataprocCluster.from_api_response(item))
            request = self.service.projects().regions().clusters().list_next(
                previous_request=request, previous_response=response
            )
        logger.debug("Found %s clusters", len(clusters))
        return clusters

    def get_cluster(
        self, region: str, cluster_name: str
    ) -> DataprocCluster:
        """Get a specific Dataproc cluster by name.

        Args:
            region: The GCP region of the cluster
            cluster_name: The name of the cluster to retrieve

        Returns:
            A DataprocCluster instance
        """
        logger.debug(
            "Getting Dataproc cluster %s in region %s", cluster_name, region
        )
        request = self.service.projects().regions().clusters().get(
            projectId=self.project_id,
            region=region,
            clusterName=cluster_name,
        )
        response = self._execute(request)
        return DataprocCluster.from_api_response(response)

    def create_cluster(
        self,
        region: str,
        cluster_name: str,
        config: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> DataprocCluster:
        """Create a new Dataproc cluster.

        Args:
            region: The GCP region for the cluster
            cluster_name: The name for the new cluster
            config: The cluster configuration dictionary
            labels: Labels to apply to the cluster

        Returns:
            The created DataprocCluster
        """
        logger.info(
            "Creating Dataproc cluster %s in region %s",
            cluster_name,
            region,
        )
        body = {
            "clusterName": cluster_name,
            "projectId": self.project_id,
            "config": config or {},
        }
        if labels:
            body["labels"] = labels

        request = self.service.projects().regions().clusters().create(
            projectId=self.project_id, region=region, body=body
        )
        response = self._execute(request)
        return DataprocCluster.from_api_response(response)

    def update_cluster(
        self,
        region: str,
        cluster_name: str,
        update_mask: str,
        cluster_config: Dict[str, Any],
    ) -> DataprocCluster:
        """Update an existing Dataproc cluster.

        Args:
            region: The GCP region of the cluster
            cluster_name: The name of the cluster to update
            update_mask: Comma-separated list of fields to update
            cluster_config: The updated cluster configuration

        Returns:
            The updated DataprocCluster
        """
        logger.info(
            "Updating Dataproc cluster %s in region %s with mask %s",
            cluster_name,
            region,
            update_mask,
        )
        body = cluster_config

        request = self.service.projects().regions().clusters().patch(
            projectId=self.project_id,
            region=region,
            clusterName=cluster_name,
            updateMask=update_mask,
            body=body,
        )
        response = self._execute(request)
        return DataprocCluster.from_api_response(response)

    def delete_cluster(self, region: str, cluster_name: str) -> bool:
        """Delete a Dataproc cluster.

        Args:
            region: The GCP region of the cluster
            cluster_name: The name of the cluster to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting Dataproc cluster %s in region %s",
            cluster_name,
            region,
        )
        request = self.service.projects().regions().clusters().delete(
            projectId=self.project_id,
            region=region,
            clusterName=cluster_name,
        )
        self._execute(request)
        return True

    def start_cluster(self, region: str, cluster_name: str) -> Dict:
        """Start a stopped Dataproc cluster.

        Args:
            region: The GCP region of the cluster
            cluster_name: The name of the cluster to start

        Returns:
            The operation response dictionary
        """
        logger.info(
            "Starting Dataproc cluster %s in region %s",
            cluster_name,
            region,
        )
        request = self.service.projects().regions().clusters().start(
            projectId=self.project_id,
            region=region,
            clusterName=cluster_name,
            body={},
        )
        return request.execute()

    def stop_cluster(self, region: str, cluster_name: str) -> Dict:
        """Stop a running Dataproc cluster.

        Args:
            region: The GCP region of the cluster
            cluster_name: The name of the cluster to stop

        Returns:
            The operation response dictionary
        """
        logger.info(
            "Stopping Dataproc cluster %s in region %s",
            cluster_name,
            region,
        )
        request = self.service.projects().regions().clusters().stop(
            projectId=self.project_id,
            region=region,
            clusterName=cluster_name,
            body={},
        )
        return request.execute()

    # --- Job methods ---

    def submit_job(self, region: str, job: Dict[str, Any]) -> DataprocJob:
        """Submit a job to a Dataproc cluster.

        Args:
            region: The GCP region of the cluster
            job: The job configuration dictionary

        Returns:
            The submitted DataprocJob
        """
        logger.info("Submitting Dataproc job in region %s", region)
        body = {"job": job}

        request = self.service.projects().regions().jobs().submit(
            projectId=self.project_id, region=region, body=body
        )
        response = self._execute(request)
        return DataprocJob.from_api_response(response)

    def get_job(self, region: str, job_id: str) -> DataprocJob:
        """Get a specific Dataproc job by ID.

        Args:
            region: The GCP region of the job
            job_id: The ID of the job to retrieve

        Returns:
            A DataprocJob instance
        """
        logger.debug("Getting Dataproc job %s in region %s", job_id, region)
        request = self.service.projects().regions().jobs().get(
            projectId=self.project_id, region=region, jobId=job_id
        )
        response = self._execute(request)
        return DataprocJob.from_api_response(response)

    def list_jobs(self, region: str) -> List[DataprocJob]:
        """List Dataproc jobs in a region.

        Args:
            region: The GCP region to list jobs in

        Returns:
            A list of DataprocJob instances
        """
        logger.debug(
            "Listing Dataproc jobs in project %s, region %s",
            self.project_id,
            region,
        )
        jobs = []
        request = self.service.projects().regions().jobs().list(
            projectId=self.project_id, region=region
        )
        while request is not None:
            response = self._execute(request)
            for item in response.get("jobs", []):
                jobs.append(DataprocJob.from_api_response(item))
            request = self.service.projects().regions().jobs().list_next(
                previous_request=request, previous_response=response
            )
        logger.debug("Found %s jobs", len(jobs))
        return jobs

    def cancel_job(self, region: str, job_id: str) -> DataprocJob:
        """Cancel a running Dataproc job.

        Args:
            region: The GCP region of the job
            job_id: The ID of the job to cancel

        Returns:
            The cancelled DataprocJob
        """
        logger.info(
            "Cancelling Dataproc job %s in region %s", job_id, region
        )
        request = self.service.projects().regions().jobs().cancel(
            projectId=self.project_id,
            region=region,
            jobId=job_id,
            body={},
        )
        response = self._execute(request)
        return DataprocJob.from_api_response(response)
