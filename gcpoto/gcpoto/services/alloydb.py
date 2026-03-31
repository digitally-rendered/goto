"""Service implementation for Google Cloud AlloyDB."""

import logging
from typing import List, Optional, Dict, Any

from gcpoto.services.base import GCPService
from gcpoto.models.alloydb import AlloyDBCluster, AlloyDBInstance
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class AlloyDBService(GCPService[AlloyDBCluster]):
    """Service for interacting with Google Cloud AlloyDB."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the AlloyDB service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="alloydb",
            version="v1",
            credentials_file=credentials_file,
            resource_model=AlloyDBCluster,
        )

    def _cluster_path(self, location: str, cluster_id: str) -> str:
        """Format a full cluster resource path.

        Args:
            location: The GCP location
            cluster_id: The cluster ID

        Returns:
            The fully-qualified cluster path
        """
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/clusters/{cluster_id}"
        )

    def _instance_path(
        self, location: str, cluster_id: str, instance_id: str
    ) -> str:
        """Format a full instance resource path.

        Args:
            location: The GCP location
            cluster_id: The cluster ID
            instance_id: The instance ID

        Returns:
            The fully-qualified instance path
        """
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/clusters/{cluster_id}/instances/{instance_id}"
        )

    # --- Cluster methods ---

    def list_clusters(self, location: str) -> List[AlloyDBCluster]:
        """List AlloyDB clusters in a location.

        Args:
            location: The GCP location (e.g. us-central1)

        Returns:
            A list of AlloyDBCluster instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug("Listing AlloyDB clusters in %s", parent)
        all_clusters = []
        request = (
            self.service.projects()
            .locations()
            .clusters()
            .list(parent=parent)
        )
        while request is not None:
            response = request.execute()
            clusters = response.get("clusters", [])
            all_clusters.extend(
                AlloyDBCluster.from_api_response(item) for item in clusters
            )
            request = (
                self.service.projects()
                .locations()
                .clusters()
                .list_next(request, response)
            )
        return all_clusters

    def get_cluster(
        self, location: str, cluster_id: str
    ) -> AlloyDBCluster:
        """Get a specific AlloyDB cluster by ID.

        Args:
            location: The GCP location
            cluster_id: The cluster ID

        Returns:
            An AlloyDBCluster instance
        """
        name = self._cluster_path(location, cluster_id)
        logger.debug("Getting AlloyDB cluster %s", name)
        request = (
            self.service.projects()
            .locations()
            .clusters()
            .get(name=name)
        )
        response = request.execute()
        return AlloyDBCluster.from_api_response(response)

    def create_cluster(
        self,
        location: str,
        cluster_id: str,
        network: str,
        database_version: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        automated_backup_policy: Optional[Dict] = None,
    ) -> AlloyDBCluster:
        """Create a new AlloyDB cluster.

        Args:
            location: The GCP location
            cluster_id: The ID for the new cluster
            network: The VPC network for the cluster
            database_version: The database engine version (e.g. POSTGRES_14)
            labels: Labels to apply to the cluster
            automated_backup_policy: Automated backup policy configuration

        Returns:
            The created AlloyDBCluster
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.info(
            "Creating AlloyDB cluster %s in %s", cluster_id, parent
        )

        body = {
            "network": network,
        }

        if database_version is not None:
            body["databaseVersion"] = database_version

        if labels:
            body["labels"] = labels

        if automated_backup_policy is not None:
            body["automatedBackupPolicy"] = automated_backup_policy

        request = (
            self.service.projects()
            .locations()
            .clusters()
            .create(parent=parent, clusterId=cluster_id, body=body)
        )
        response = request.execute()
        return AlloyDBCluster.from_api_response(response)

    def update_cluster(
        self,
        location: str,
        cluster_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> AlloyDBCluster:
        """Update an existing AlloyDB cluster.

        Args:
            location: The GCP location
            cluster_id: The cluster ID
            update_mask: Comma-separated list of fields to update
            update_fields: Dictionary of fields to update

        Returns:
            The updated AlloyDBCluster
        """
        name = self._cluster_path(location, cluster_id)
        logger.info("Updating AlloyDB cluster %s", name)

        request = (
            self.service.projects()
            .locations()
            .clusters()
            .patch(name=name, updateMask=update_mask, body=update_fields)
        )
        response = request.execute()
        return AlloyDBCluster.from_api_response(response)

    def delete_cluster(self, location: str, cluster_id: str) -> bool:
        """Delete an AlloyDB cluster.

        Args:
            location: The GCP location
            cluster_id: The cluster ID

        Returns:
            True if the deletion was successful
        """
        name = self._cluster_path(location, cluster_id)
        logger.info("Deleting AlloyDB cluster %s", name)
        request = (
            self.service.projects()
            .locations()
            .clusters()
            .delete(name=name)
        )
        request.execute()
        return True

    # --- Instance methods ---

    def list_instances(
        self, location: str, cluster_id: str
    ) -> List[AlloyDBInstance]:
        """List instances in an AlloyDB cluster.

        Args:
            location: The GCP location
            cluster_id: The cluster ID

        Returns:
            A list of AlloyDBInstance instances
        """
        parent = self._cluster_path(location, cluster_id)
        logger.debug("Listing instances in AlloyDB cluster %s", parent)
        all_instances = []
        request = (
            self.service.projects()
            .locations()
            .clusters()
            .instances()
            .list(parent=parent)
        )
        while request is not None:
            response = request.execute()
            instances = response.get("instances", [])
            all_instances.extend(
                AlloyDBInstance.from_api_response(item) for item in instances
            )
            request = (
                self.service.projects()
                .locations()
                .clusters()
                .instances()
                .list_next(request, response)
            )
        return all_instances

    def get_instance(
        self, location: str, cluster_id: str, instance_id: str
    ) -> AlloyDBInstance:
        """Get a specific AlloyDB instance by ID.

        Args:
            location: The GCP location
            cluster_id: The cluster ID
            instance_id: The instance ID

        Returns:
            An AlloyDBInstance instance
        """
        name = self._instance_path(location, cluster_id, instance_id)
        logger.debug("Getting AlloyDB instance %s", name)
        request = (
            self.service.projects()
            .locations()
            .clusters()
            .instances()
            .get(name=name)
        )
        response = request.execute()
        return AlloyDBInstance.from_api_response(response)

    def create_instance(
        self,
        location: str,
        cluster_id: str,
        instance_id: str,
        instance_type: str,
        machine_config: Optional[Dict] = None,
        availability_type: Optional[str] = None,
    ) -> AlloyDBInstance:
        """Create a new instance in an AlloyDB cluster.

        Args:
            location: The GCP location
            cluster_id: The cluster ID
            instance_id: The ID for the new instance
            instance_type: The instance type (PRIMARY or READ_POOL)
            machine_config: Machine configuration for the instance
            availability_type: Availability type (e.g. REGIONAL, ZONAL)

        Returns:
            The created AlloyDBInstance
        """
        parent = self._cluster_path(location, cluster_id)
        logger.info(
            "Creating AlloyDB instance %s in cluster %s",
            instance_id,
            parent,
        )

        body = {
            "instanceType": instance_type,
        }

        if machine_config is not None:
            body["machineConfig"] = machine_config

        if availability_type is not None:
            body["availabilityType"] = availability_type

        request = (
            self.service.projects()
            .locations()
            .clusters()
            .instances()
            .create(parent=parent, instanceId=instance_id, body=body)
        )
        response = request.execute()
        return AlloyDBInstance.from_api_response(response)

    def update_instance(
        self,
        location: str,
        cluster_id: str,
        instance_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> AlloyDBInstance:
        """Update an existing AlloyDB instance.

        Args:
            location: The GCP location
            cluster_id: The cluster ID
            instance_id: The instance ID
            update_mask: Comma-separated list of fields to update
            update_fields: Dictionary of fields to update

        Returns:
            The updated AlloyDBInstance
        """
        name = self._instance_path(location, cluster_id, instance_id)
        logger.info("Updating AlloyDB instance %s", name)

        request = (
            self.service.projects()
            .locations()
            .clusters()
            .instances()
            .patch(name=name, updateMask=update_mask, body=update_fields)
        )
        response = request.execute()
        return AlloyDBInstance.from_api_response(response)

    def delete_instance(
        self, location: str, cluster_id: str, instance_id: str
    ) -> bool:
        """Delete an AlloyDB instance.

        Args:
            location: The GCP location
            cluster_id: The cluster ID
            instance_id: The instance ID

        Returns:
            True if the deletion was successful
        """
        name = self._instance_path(location, cluster_id, instance_id)
        logger.info("Deleting AlloyDB instance %s", name)
        request = (
            self.service.projects()
            .locations()
            .clusters()
            .instances()
            .delete(name=name)
        )
        request.execute()
        return True
