"""Service implementation for Google Cloud VMware Engine."""

import logging
from typing import List, Optional, Dict, Any

from gcpoto.services.base import GCPService
from gcpoto.models.vmware_engine import PrivateCloud, Cluster

logger = logging.getLogger(__name__)

class VMwareEngineService(GCPService[PrivateCloud]):
    """Service for interacting with Google Cloud VMware Engine."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the VMware Engine service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="vmwareengine",
            version="v1",
            credentials_file=credentials_file,
            resource_model=PrivateCloud,
        )

    # --- Private Cloud methods ---

    def list_private_clouds(self, location: str) -> List[PrivateCloud]:
        """List private clouds in the project.

        Args:
            location: The location to list private clouds in

        Returns:
            A list of PrivateCloud instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug("Listing VMware Engine private clouds in %s", parent)

        request = (
            self.service.projects()
            .locations()
            .privateClouds()
            .list(parent=parent)
        )
        response = self._execute(request)
        clouds = [
            PrivateCloud.from_api_response(item)
            for item in response.get("privateClouds", [])
        ]
        logger.info(
            "Found %s private cloud(s) in %s", len(clouds), parent
        )
        return clouds

    def get_private_cloud(
        self, location: str, cloud_name: str
    ) -> PrivateCloud:
        """Get a specific private cloud by name.

        Args:
            location: The location of the private cloud
            cloud_name: The name of the private cloud

        Returns:
            A PrivateCloud instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/privateClouds/{cloud_name}"
        )
        logger.debug("Getting VMware Engine private cloud %s", name)

        request = (
            self.service.projects()
            .locations()
            .privateClouds()
            .get(name=name)
        )
        response = self._execute(request)
        return PrivateCloud.from_api_response(response)

    def create_private_cloud(
        self,
        location: str,
        cloud_name: str,
        network_config: Dict[str, Any],
        management_cluster: Dict[str, Any],
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new private cloud.

        Args:
            location: The location for the private cloud
            cloud_name: The name for the new private cloud
            network_config: Network configuration for the private cloud
            management_cluster: Management cluster configuration
            labels: Resource labels to apply

        Returns:
            The operation response dictionary
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.info(
            "Creating VMware Engine private cloud %s in %s",
            cloud_name,
            parent,
        )

        body: Dict[str, Any] = {
            "networkConfig": network_config,
            "managementCluster": management_cluster,
        }

        if labels:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .privateClouds()
            .create(parent=parent, privateCloudId=cloud_name, body=body)
        )
        response = self._execute(request)
        logger.info(
            "Private cloud creation initiated for %s", cloud_name
        )
        return response

    def delete_private_cloud(
        self, location: str, cloud_name: str
    ) -> Dict[str, Any]:
        """Delete a private cloud.

        Args:
            location: The location of the private cloud
            cloud_name: The name of the private cloud to delete

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/privateClouds/{cloud_name}"
        )
        logger.info("Deleting VMware Engine private cloud %s", name)

        request = (
            self.service.projects()
            .locations()
            .privateClouds()
            .delete(name=name)
        )
        response = self._execute(request)
        logger.info(
            "Private cloud deletion initiated for %s", cloud_name
        )
        return response

    # --- Cluster methods ---

    def list_clusters(
        self, location: str, cloud_name: str
    ) -> List[Cluster]:
        """List clusters in a private cloud.

        Args:
            location: The location of the private cloud
            cloud_name: The name of the private cloud

        Returns:
            A list of Cluster instances
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/privateClouds/{cloud_name}"
        )
        logger.debug(
            "Listing clusters in private cloud %s", parent
        )

        request = (
            self.service.projects()
            .locations()
            .privateClouds()
            .clusters()
            .list(parent=parent)
        )
        response = self._execute(request)
        clusters = [
            Cluster.from_api_response(item)
            for item in response.get("clusters", [])
        ]
        logger.info(
            "Found %s cluster(s) in private cloud %s",
            len(clusters),
            cloud_name,
        )
        return clusters

    def get_cluster(
        self, location: str, cloud_name: str, cluster_name: str
    ) -> Cluster:
        """Get a specific cluster by name.

        Args:
            location: The location of the private cloud
            cloud_name: The name of the private cloud
            cluster_name: The name of the cluster

        Returns:
            A Cluster instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/privateClouds/{cloud_name}/clusters/{cluster_name}"
        )
        logger.debug("Getting VMware Engine cluster %s", name)

        request = (
            self.service.projects()
            .locations()
            .privateClouds()
            .clusters()
            .get(name=name)
        )
        response = self._execute(request)
        return Cluster.from_api_response(response)

    def create_cluster(
        self,
        location: str,
        cloud_name: str,
        cluster_name: str,
        node_type_configs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new cluster in a private cloud.

        Args:
            location: The location of the private cloud
            cloud_name: The name of the private cloud
            cluster_name: The name for the new cluster
            node_type_configs: Node type configurations

        Returns:
            The operation response dictionary
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/privateClouds/{cloud_name}"
        )
        logger.info(
            "Creating cluster %s in private cloud %s",
            cluster_name,
            cloud_name,
        )

        body: Dict[str, Any] = {
            "nodeTypeConfigs": node_type_configs,
        }

        request = (
            self.service.projects()
            .locations()
            .privateClouds()
            .clusters()
            .create(parent=parent, clusterId=cluster_name, body=body)
        )
        response = self._execute(request)
        logger.info("Cluster creation initiated for %s", cluster_name)
        return response

    def delete_cluster(
        self, location: str, cloud_name: str, cluster_name: str
    ) -> Dict[str, Any]:
        """Delete a cluster from a private cloud.

        Args:
            location: The location of the private cloud
            cloud_name: The name of the private cloud
            cluster_name: The name of the cluster to delete

        Returns:
            The operation response dictionary
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/privateClouds/{cloud_name}/clusters/{cluster_name}"
        )
        logger.info("Deleting VMware Engine cluster %s", name)

        request = (
            self.service.projects()
            .locations()
            .privateClouds()
            .clusters()
            .delete(name=name)
        )
        response = self._execute(request)
        logger.info("Cluster deletion initiated for %s", cluster_name)
        return response
