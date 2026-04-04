"""Service implementation for Google Cloud Looker."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.looker import LookerInstance

logger = logging.getLogger(__name__)

class LookerService(GCPService[LookerInstance]):
    """Service for interacting with Google Cloud Looker."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Looker service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="looker",
            version="v1",
            credentials_file=credentials_file,
            resource_model=LookerInstance,
            **kwargs,
        )

    def list_instances(self, location: str) -> List[LookerInstance]:
        """List Looker instances in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            A list of LookerInstance instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        request = (
            self.service.projects()
            .locations()
            .instances()
            .list(parent=parent)
        )

        instances = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("instances", []):
                instances.append(
                    LookerInstance.from_api_response(
                        item, self.project_id
                    )
                )
            request = (
                self.service.projects()
                .locations()
                .instances()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s Looker instances in %s",
            len(instances),
            location,
        )
        return instances

    def get_instance(
        self, location: str, instance_name: str
    ) -> LookerInstance:
        """Get a specific Looker instance.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name of the instance

        Returns:
            A LookerInstance instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        request = (
            self.service.projects()
            .locations()
            .instances()
            .get(name=name)
        )
        response = self._execute(request, "instance", instance_name)
        logger.debug("Retrieved Looker instance %s", instance_name)
        return LookerInstance.from_api_response(
            response, self.project_id
        )

    def create_instance(
        self,
        location: str,
        instance_name: str,
        platform_edition: str,
        admin_settings: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> LookerInstance:
        """Create a new Looker instance.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name for the new instance
            platform_edition: The platform edition (STANDARD, ADVANCED, ELITE)
            admin_settings: Optional admin settings for the instance
            labels: Optional labels for the instance

        Returns:
            The created LookerInstance instance
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        body: Dict[str, Any] = {
            "platformEdition": platform_edition,
        }

        if admin_settings is not None:
            body["adminSettings"] = admin_settings

        if labels is not None:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .instances()
            .create(
                parent=parent,
                instanceId=instance_name,
                body=body,
            )
        )
        response = self._execute(request)
        logger.debug(
            "Created Looker instance %s in %s",
            instance_name,
            location,
        )
        return LookerInstance.from_api_response(
            response, self.project_id
        )

    def update_instance(
        self,
        location: str,
        instance_name: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> LookerInstance:
        """Update a Looker instance.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name of the instance to update
            update_mask: Comma-separated list of fields to update
            update_fields: The fields to update

        Returns:
            The updated LookerInstance instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        request = (
            self.service.projects()
            .locations()
            .instances()
            .patch(
                name=name,
                updateMask=update_mask,
                body=update_fields,
            )
        )
        response = self._execute(request, "instance", instance_name)
        logger.debug("Updated Looker instance %s", instance_name)
        return LookerInstance.from_api_response(
            response, self.project_id
        )

    def delete_instance(
        self, location: str, instance_name: str
    ) -> bool:
        """Delete a Looker instance.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name of the instance to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        request = self.service.projects().locations().instances().delete(
            name=name
        )
        self._execute(request)
        logger.debug("Deleted Looker instance %s", instance_name)
        return True

    def restart_instance(
        self, location: str, instance_name: str
    ) -> LookerInstance:
        """Restart a Looker instance.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name of the instance to restart

        Returns:
            The restarted LookerInstance instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        request = (
            self.service.projects()
            .locations()
            .instances()
            .restart(name=name)
        )
        response = self._execute(request, "instance", instance_name)
        logger.debug("Restarted Looker instance %s", instance_name)
        return LookerInstance.from_api_response(
            response, self.project_id
        )

    def export_instance(
        self, location: str, instance_name: str, gcs_uri: str
    ) -> Dict[str, Any]:
        """Export a Looker instance to a GCS URI.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name of the instance to export
            gcs_uri: The GCS URI to export to

        Returns:
            The operation response
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        body = {"gcsUri": gcs_uri}

        request = (
            self.service.projects()
            .locations()
            .instances()
            .export(name=name, body=body)
        )
        response = self._execute(request, "instance", instance_name)
        logger.debug(
            "Exported Looker instance %s to %s",
            instance_name,
            gcs_uri,
        )
        return response

    def import_instance(
        self, location: str, instance_name: str, gcs_uri: str
    ) -> Dict[str, Any]:
        """Import a Looker instance from a GCS URI.

        Args:
            location: The GCP location (e.g. 'us-central1')
            instance_name: The name of the instance to import into
            gcs_uri: The GCS URI to import from

        Returns:
            The operation response
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/instances/{instance_name}"
        )
        body = {"gcsUri": gcs_uri}

        request = (
            self.service.projects()
            .locations()
            .instances()
            .import_(name=name, body=body)
        )
        response = self._execute(request, "instance", instance_name)
        logger.debug(
            "Imported Looker instance %s from %s",
            instance_name,
            gcs_uri,
        )
        return response
