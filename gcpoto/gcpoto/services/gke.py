"""Service implementation for Google Kubernetes Engine (GKE)."""

import logging
from typing import List, Optional, Dict, Any

from gcpoto.services.base import GCPService
from gcpoto.models.gke import GKECluster, NodePool

logger = logging.getLogger(__name__)

class GKEService(GCPService[GKECluster]):
    """Service for interacting with Google Kubernetes Engine."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the GKE service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="container",
            version="v1",
            credentials_file=credentials_file,
            resource_model=GKECluster,
        )

    # --- Cluster methods ---

    def list_clusters(self, location: str = "-") -> List[GKECluster]:
        """List GKE clusters in the project.

        Args:
            location: The location (zone or region) to list clusters in.
                Use "-" to list clusters across all locations.

        Returns:
            A list of GKECluster instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug("Listing GKE clusters in %s", parent)

        request = self.service.projects().locations().clusters().list(
            parent=parent
        )
        response = self._execute(request)
        clusters = [
            GKECluster.from_api_response(item)
            for item in response.get("clusters", [])
        ]
        logger.info("Found %s GKE cluster(s) in %s", len(clusters), parent)
        return clusters

    def get_cluster(self, location: str, cluster_name: str) -> GKECluster:
        """Get a specific GKE cluster by name.

        Args:
            location: The location (zone or region) of the cluster
            cluster_name: The name of the cluster to retrieve

        Returns:
            A GKECluster instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/clusters/{cluster_name}"
        )
        logger.debug("Getting GKE cluster %s", name)

        request = self.service.projects().locations().clusters().get(
            name=name
        )
        response = self._execute(request)
        return GKECluster.from_api_response(response)

    def create_cluster(
        self,
        location: str,
        cluster_name: str,
        node_count: int = 3,
        machine_type: str = "e2-medium",
        network: Optional[str] = None,
        subnetwork: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new GKE cluster.

        Args:
            location: The location (zone or region) for the cluster
            cluster_name: The name for the new cluster
            node_count: The initial number of nodes (default 3)
            machine_type: The machine type for nodes (default e2-medium)
            network: The VPC network name
            subnetwork: The subnetwork name
            labels: Resource labels to apply to the cluster

        Returns:
            The operation response dictionary
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.info(
            "Creating GKE cluster %s in %s with %s nodes",
            cluster_name,
            parent,
            node_count,
        )

        cluster_body: Dict[str, Any] = {
            "name": cluster_name,
            "initialNodeCount": node_count,
            "nodeConfig": {
                "machineType": machine_type,
            },
        }

        if network:
            cluster_body["network"] = network
        if subnetwork:
            cluster_body["subnetwork"] = subnetwork
        if labels:
            cluster_body["resourceLabels"] = labels

        body = {"cluster": cluster_body}

        request = self.service.projects().locations().clusters().create(
            parent=parent, body=body
        )
        response = self._execute(request)
        logger.info("Cluster creation initiated for %s", cluster_name)
        return response

    def delete_cluster(self, location: str, cluster_name: str) -> Dict[str, Any]:
        """Delete a GKE cluster.

        Args:
            location: The location (zone or region) of the cluster
            cluster_name: The name of the cluster to delete

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/clusters/{cluster_name}"
        )
        logger.info("Deleting GKE cluster %s", name)

        request = self.service.projects().locations().clusters().delete(
            name=name
        )
        response = self._execute(request)
        logger.info("Cluster deletion initiated for %s", cluster_name)
        return response

    def update_cluster(
        self,
        location: str,
        cluster_name: str,
        update_body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a GKE cluster.

        Args:
            location: The location (zone or region) of the cluster
            cluster_name: The name of the cluster to update
            update_body: The update request body

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/clusters/{cluster_name}"
        )
        logger.info("Updating GKE cluster %s", name)

        request = self.service.projects().locations().clusters().update(
            name=name, body=update_body
        )
        response = self._execute(request)
        logger.info("Cluster update initiated for %s", cluster_name)
        return response

    # --- Node Pool methods ---

    def list_node_pools(
        self, location: str, cluster_name: str
    ) -> List[NodePool]:
        """List node pools in a GKE cluster.

        Args:
            location: The location (zone or region) of the cluster
            cluster_name: The name of the cluster

        Returns:
            A list of NodePool instances
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/clusters/{cluster_name}"
        )
        logger.debug("Listing node pools in cluster %s", parent)

        request = self.service.projects().locations().clusters().nodePools().list(
            parent=parent
        )
        response = self._execute(request)
        pools = [
            NodePool.from_api_response(item)
            for item in response.get("nodePools", [])
        ]
        logger.info(
            "Found %s node pool(s) in cluster %s", len(pools), cluster_name
        )
        return pools

    def get_node_pool(
        self, location: str, cluster_name: str, pool_name: str
    ) -> NodePool:
        """Get a specific node pool by name.

        Args:
            location: The location (zone or region) of the cluster
            cluster_name: The name of the cluster
            pool_name: The name of the node pool to retrieve

        Returns:
            A NodePool instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/clusters/{cluster_name}/nodePools/{pool_name}"
        )
        logger.debug("Getting node pool %s", name)

        request = self.service.projects().locations().clusters().nodePools().get(
            name=name
        )
        response = self._execute(request)
        return NodePool.from_api_response(response)

    def create_node_pool(
        self,
        location: str,
        cluster_name: str,
        pool_name: str,
        node_count: int,
        machine_type: str,
        autoscaling: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new node pool in a GKE cluster.

        Args:
            location: The location (zone or region) of the cluster
            cluster_name: The name of the cluster
            pool_name: The name for the new node pool
            node_count: The initial number of nodes
            machine_type: The machine type for nodes
            autoscaling: Optional autoscaling configuration

        Returns:
            The operation response dictionary
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/clusters/{cluster_name}"
        )
        logger.info(
            "Creating node pool %s in cluster %s with %s nodes",
            pool_name,
            cluster_name,
            node_count,
        )

        node_pool_body: Dict[str, Any] = {
            "name": pool_name,
            "initialNodeCount": node_count,
            "config": {
                "machineType": machine_type,
            },
        }

        if autoscaling:
            node_pool_body["autoscaling"] = autoscaling

        body = {"nodePool": node_pool_body}

        request = (
            self.service.projects()
            .locations()
            .clusters()
            .nodePools()
            .create(parent=parent, body=body)
        )
        response = self._execute(request)
        logger.info("Node pool creation initiated for %s", pool_name)
        return response

    def delete_node_pool(
        self, location: str, cluster_name: str, pool_name: str
    ) -> Dict[str, Any]:
        """Delete a node pool from a GKE cluster.

        Args:
            location: The location (zone or region) of the cluster
            cluster_name: The name of the cluster
            pool_name: The name of the node pool to delete

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/clusters/{cluster_name}/nodePools/{pool_name}"
        )
        logger.info("Deleting node pool %s", name)

        request = (
            self.service.projects()
            .locations()
            .clusters()
            .nodePools()
            .delete(name=name)
        )
        response = self._execute(request)
        logger.info("Node pool deletion initiated for %s", pool_name)
        return response

    def set_node_pool_size(
        self,
        location: str,
        cluster_name: str,
        pool_name: str,
        node_count: int,
    ) -> Dict[str, Any]:
        """Set the size of a node pool.

        Args:
            location: The location (zone or region) of the cluster
            cluster_name: The name of the cluster
            pool_name: The name of the node pool
            node_count: The desired number of nodes

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/clusters/{cluster_name}/nodePools/{pool_name}"
        )
        logger.info(
            "Setting node pool %s size to %s nodes", pool_name, node_count
        )

        body = {"nodeCount": node_count}

        request = (
            self.service.projects()
            .locations()
            .clusters()
            .nodePools()
            .setSize(name=name, body=body)
        )
        response = self._execute(request)
        logger.info(
            "Node pool resize initiated for %s to %s nodes",
            pool_name,
            node_count,
        )
        return response
