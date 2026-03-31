"""Service implementation for Google Cloud Bigtable."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.bigtable import BigtableInstance, BigtableCluster, BigtableTable
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class BigtableService(GCPService[BigtableInstance]):
    """Service for interacting with Google Cloud Bigtable."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the Bigtable service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="bigtableadmin",
            version="v2",
            credentials_file=credentials_file,
            resource_model=BigtableInstance,
        )

    def _parent_path(self) -> str:
        """Return the parent path for project-level resources.

        Returns:
            The parent path string
        """
        return f"projects/{self.project_id}"

    def _instance_path(self, instance_id: str) -> str:
        """Return the full instance resource path.

        Args:
            instance_id: The instance ID

        Returns:
            The full instance path
        """
        return f"projects/{self.project_id}/instances/{instance_id}"

    def _cluster_path(self, instance_id: str, cluster_id: str) -> str:
        """Return the full cluster resource path.

        Args:
            instance_id: The instance ID
            cluster_id: The cluster ID

        Returns:
            The full cluster path
        """
        return (
            f"projects/{self.project_id}/instances/{instance_id}"
            f"/clusters/{cluster_id}"
        )

    def _table_path(self, instance_id: str, table_id: str) -> str:
        """Return the full table resource path.

        Args:
            instance_id: The instance ID
            table_id: The table ID

        Returns:
            The full table path
        """
        return (
            f"projects/{self.project_id}/instances/{instance_id}"
            f"/tables/{table_id}"
        )

    # --- Instance methods ---

    def list_instances(self) -> List[BigtableInstance]:
        """List Bigtable instances in the project.

        Returns:
            A list of BigtableInstance instances
        """
        logger.debug("Listing Bigtable instances for project %s", self.project_id)
        request = (
            self.service.projects()
            .instances()
            .list(parent=self._parent_path())
        )
        response = request.execute()
        instances = [
            BigtableInstance.from_api_response(item)
            for item in response.get("instances", [])
        ]
        logger.info("Found %s Bigtable instances", len(instances))
        return instances

    def get_instance(self, instance_id: str) -> BigtableInstance:
        """Get a specific Bigtable instance by ID.

        Args:
            instance_id: The ID of the instance to retrieve

        Returns:
            A BigtableInstance instance

        Raises:
            ResourceNotFoundError: If the instance does not exist
        """
        logger.debug("Getting Bigtable instance %s", instance_id)
        try:
            request = (
                self.service.projects()
                .instances()
                .get(name=self._instance_path(instance_id))
            )
            response = request.execute()
            return BigtableInstance.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("BigtableInstance", instance_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_instance(
        self,
        instance_id: str,
        display_name: str,
        instance_type: str = "PRODUCTION",
        clusters: Optional[Dict[str, Dict[str, Any]]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> BigtableInstance:
        """Create a new Bigtable instance.

        Args:
            instance_id: The ID for the new instance
            display_name: The descriptive name for the instance
            instance_type: The type of instance (PRODUCTION or DEVELOPMENT)
            clusters: A dict mapping cluster IDs to cluster configs, each with
                keys like 'location', 'serveNodes', 'defaultStorageType'
            labels: Optional labels to apply to the instance

        Returns:
            The created BigtableInstance
        """
        logger.debug("Creating Bigtable instance %s", instance_id)

        instance_body = {
            "displayName": display_name,
            "type": instance_type,
        }
        if labels:
            instance_body["labels"] = labels

        # Build clusters body
        clusters_body = {}
        if clusters:
            for cluster_id, cluster_config in clusters.items():
                cluster_entry = {
                    "location": (
                        f"projects/{self.project_id}/locations/"
                        f"{cluster_config['location']}"
                    ),
                    "serveNodes": cluster_config.get("serveNodes", 0),
                    "defaultStorageType": cluster_config.get(
                        "defaultStorageType", "SSD"
                    ),
                }
                clusters_body[cluster_id] = cluster_entry

        body = {
            "instanceId": instance_id,
            "instance": instance_body,
            "clusters": clusters_body,
        }

        request = (
            self.service.projects()
            .instances()
            .create(parent=self._parent_path(), body=body)
        )
        response = request.execute()
        logger.info("Created Bigtable instance %s", instance_id)
        return BigtableInstance.from_api_response(response)

    def update_instance(
        self,
        instance_id: str,
        display_name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> BigtableInstance:
        """Update a Bigtable instance.

        Args:
            instance_id: The ID of the instance to update
            display_name: New display name for the instance
            labels: New labels for the instance

        Returns:
            The updated BigtableInstance
        """
        logger.debug("Updating Bigtable instance %s", instance_id)

        body = {"name": self._instance_path(instance_id)}
        if display_name is not None:
            body["displayName"] = display_name
        if labels is not None:
            body["labels"] = labels

        request = (
            self.service.projects()
            .instances()
            .partialUpdateInstance(
                name=self._instance_path(instance_id),
                body=body,
                updateMask="displayName,labels",
            )
        )
        response = request.execute()
        logger.info("Updated Bigtable instance %s", instance_id)
        return BigtableInstance.from_api_response(response)

    def delete_instance(self, instance_id: str) -> bool:
        """Delete a Bigtable instance.

        Args:
            instance_id: The ID of the instance to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the instance does not exist
        """
        logger.debug("Deleting Bigtable instance %s", instance_id)
        try:
            request = (
                self.service.projects()
                .instances()
                .delete(name=self._instance_path(instance_id))
            )
            request.execute()
            logger.info("Deleted Bigtable instance %s", instance_id)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("BigtableInstance", instance_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    # --- Cluster methods ---

    def list_clusters(self, instance_id: str) -> List[BigtableCluster]:
        """List clusters in a Bigtable instance.

        Args:
            instance_id: The ID of the instance

        Returns:
            A list of BigtableCluster instances
        """
        logger.debug(
            "Listing clusters for Bigtable instance %s", instance_id
        )
        request = (
            self.service.projects()
            .instances()
            .clusters()
            .list(parent=self._instance_path(instance_id))
        )
        response = request.execute()
        clusters = [
            BigtableCluster.from_api_response(item)
            for item in response.get("clusters", [])
        ]
        logger.info(
            "Found %s clusters for instance %s", len(clusters), instance_id
        )
        return clusters

    def get_cluster(
        self, instance_id: str, cluster_id: str
    ) -> BigtableCluster:
        """Get a specific cluster by ID.

        Args:
            instance_id: The ID of the instance
            cluster_id: The ID of the cluster

        Returns:
            A BigtableCluster instance

        Raises:
            ResourceNotFoundError: If the cluster does not exist
        """
        logger.debug(
            "Getting cluster %s for instance %s", cluster_id, instance_id
        )
        try:
            request = (
                self.service.projects()
                .instances()
                .clusters()
                .get(name=self._cluster_path(instance_id, cluster_id))
            )
            response = request.execute()
            return BigtableCluster.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("BigtableCluster", cluster_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_cluster(
        self,
        instance_id: str,
        cluster_id: str,
        location: str,
        serve_nodes: int,
        storage_type: str = "SSD",
    ) -> BigtableCluster:
        """Create a new cluster in a Bigtable instance.

        Args:
            instance_id: The ID of the instance
            cluster_id: The ID for the new cluster
            location: The location for the cluster (e.g. us-central1-b)
            serve_nodes: The number of nodes to allocate
            storage_type: The storage type (SSD or HDD)

        Returns:
            The created BigtableCluster
        """
        logger.debug(
            "Creating cluster %s for instance %s", cluster_id, instance_id
        )

        body = {
            "location": f"projects/{self.project_id}/locations/{location}",
            "serveNodes": serve_nodes,
            "defaultStorageType": storage_type,
        }

        request = (
            self.service.projects()
            .instances()
            .clusters()
            .create(
                parent=self._instance_path(instance_id),
                clusterId=cluster_id,
                body=body,
            )
        )
        response = request.execute()
        logger.info(
            "Created cluster %s for instance %s", cluster_id, instance_id
        )
        return BigtableCluster.from_api_response(response)

    def update_cluster(
        self,
        instance_id: str,
        cluster_id: str,
        serve_nodes: int,
    ) -> BigtableCluster:
        """Update a cluster's serve_nodes count.

        Args:
            instance_id: The ID of the instance
            cluster_id: The ID of the cluster
            serve_nodes: The new number of nodes

        Returns:
            The updated BigtableCluster
        """
        logger.debug(
            "Updating cluster %s for instance %s", cluster_id, instance_id
        )

        body = {
            "serveNodes": serve_nodes,
        }

        request = (
            self.service.projects()
            .instances()
            .clusters()
            .update(
                name=self._cluster_path(instance_id, cluster_id),
                body=body,
            )
        )
        response = request.execute()
        logger.info(
            "Updated cluster %s for instance %s", cluster_id, instance_id
        )
        return BigtableCluster.from_api_response(response)

    def delete_cluster(self, instance_id: str, cluster_id: str) -> bool:
        """Delete a cluster from a Bigtable instance.

        Args:
            instance_id: The ID of the instance
            cluster_id: The ID of the cluster to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the cluster does not exist
        """
        logger.debug(
            "Deleting cluster %s from instance %s", cluster_id, instance_id
        )
        try:
            request = (
                self.service.projects()
                .instances()
                .clusters()
                .delete(name=self._cluster_path(instance_id, cluster_id))
            )
            request.execute()
            logger.info(
                "Deleted cluster %s from instance %s",
                cluster_id,
                instance_id,
            )
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("BigtableCluster", cluster_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    # --- Table methods ---

    def list_tables(self, instance_id: str) -> List[BigtableTable]:
        """List tables in a Bigtable instance.

        Args:
            instance_id: The ID of the instance

        Returns:
            A list of BigtableTable instances
        """
        logger.debug(
            "Listing tables for Bigtable instance %s", instance_id
        )
        request = (
            self.service.projects()
            .instances()
            .tables()
            .list(parent=self._instance_path(instance_id))
        )

        tables = []
        while request is not None:
            response = request.execute()
            for item in response.get("tables", []):
                tables.append(BigtableTable.from_api_response(item))
            request = (
                self.service.projects()
                .instances()
                .tables()
                .list_next(request, response)
            )

        logger.info(
            "Found %s tables for instance %s", len(tables), instance_id
        )
        return tables

    def get_table(self, instance_id: str, table_id: str) -> BigtableTable:
        """Get a specific table by ID.

        Args:
            instance_id: The ID of the instance
            table_id: The ID of the table

        Returns:
            A BigtableTable instance

        Raises:
            ResourceNotFoundError: If the table does not exist
        """
        logger.debug(
            "Getting table %s for instance %s", table_id, instance_id
        )
        try:
            request = (
                self.service.projects()
                .instances()
                .tables()
                .get(name=self._table_path(instance_id, table_id))
            )
            response = request.execute()
            return BigtableTable.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("BigtableTable", table_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_table(
        self,
        instance_id: str,
        table_id: str,
        column_families: Optional[Dict[str, Dict]] = None,
    ) -> BigtableTable:
        """Create a new table in a Bigtable instance.

        Args:
            instance_id: The ID of the instance
            table_id: The ID for the new table
            column_families: A dict mapping column family names to their
                gc rule configs

        Returns:
            The created BigtableTable
        """
        logger.debug(
            "Creating table %s for instance %s", table_id, instance_id
        )

        table_body = {}
        if column_families:
            table_body["columnFamilies"] = column_families

        body = {
            "tableId": table_id,
            "table": table_body,
        }

        request = (
            self.service.projects()
            .instances()
            .tables()
            .create(
                parent=self._instance_path(instance_id),
                body=body,
            )
        )
        response = request.execute()
        logger.info(
            "Created table %s for instance %s", table_id, instance_id
        )
        return BigtableTable.from_api_response(response)

    def delete_table(self, instance_id: str, table_id: str) -> bool:
        """Delete a table from a Bigtable instance.

        Args:
            instance_id: The ID of the instance
            table_id: The ID of the table to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the table does not exist
        """
        logger.debug(
            "Deleting table %s from instance %s", table_id, instance_id
        )
        try:
            request = (
                self.service.projects()
                .instances()
                .tables()
                .delete(name=self._table_path(instance_id, table_id))
            )
            request.execute()
            logger.info(
                "Deleted table %s from instance %s", table_id, instance_id
            )
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("BigtableTable", table_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))
