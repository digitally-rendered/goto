"""Service implementation for Google Cloud Run."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.cloud_run import CloudRunService, CloudRunRevision
from gcpoto.exceptions import ResourceAlreadyExistsError, ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class CloudRunServiceManager(GCPService[CloudRunService]):
    """Service for interacting with Google Cloud Run.

    Named CloudRunServiceManager to avoid name clash with the
    CloudRunService model class.
    """

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Run service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="run",
            version="v2",
            credentials_file=credentials_file,
            resource_model=CloudRunService,
            **kwargs,
        )

    def _format_parent(self, location: str) -> str:
        """Format the parent path for Cloud Run resources.

        Args:
            location: The GCP location/region (use "-" for all locations)

        Returns:
            The formatted parent path
        """
        return f"projects/{self.project_id}/locations/{location}"

    def _format_service_name(self, location: str, service_name: str) -> str:
        """Format the full service resource name.

        Args:
            location: The GCP location/region
            service_name: The short service name or full resource path

        Returns:
            The fully qualified service resource name
        """
        if "/" in service_name:
            return service_name
        return f"projects/{self.project_id}/locations/{location}/services/{service_name}"

    def _format_revision_name(self, location: str, revision_name: str) -> str:
        """Format the full revision resource name.

        Args:
            location: The GCP location/region
            revision_name: The short revision name or full resource path

        Returns:
            The fully qualified revision resource name
        """
        if "/" in revision_name:
            return revision_name
        return f"projects/{self.project_id}/locations/{location}/revisions/{revision_name}"

    def list_services(
        self, location: str = "-", **kwargs
    ) -> List[CloudRunService]:
        """List Cloud Run services.

        Args:
            location: The GCP location/region (default "-" for all locations)
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of CloudRunService instances
        """
        parent = self._format_parent(location)
        logger.debug("Listing Cloud Run services in %s", parent)

        request = (
            self.service.projects()
            .locations()
            .services()
            .list(parent=parent, **kwargs)
        )

        services = []
        while request is not None:
            response = request.execute()
            for svc_data in response.get("services", []):
                services.append(
                    CloudRunService.from_api_response(svc_data, self.project_id)
                )

            request = (
                self.service.projects()
                .locations()
                .services()
                .list_next(request, response)
            )

        return services

    def get_service(
        self, location: str, service_name: str
    ) -> CloudRunService:
        """Get a specific Cloud Run service.

        Args:
            location: The GCP location/region
            service_name: The name of the service to retrieve

        Returns:
            A CloudRunService instance
        """
        full_name = self._format_service_name(location, service_name)
        logger.debug("Getting Cloud Run service %s", full_name)

        request = (
            self.service.projects()
            .locations()
            .services()
            .get(name=full_name)
        )
        response = request.execute()

        return CloudRunService.from_api_response(response, self.project_id)

    def create_service(
        self,
        location: str,
        service_name: str,
        image: str,
        port: int = 8080,
        env_vars: Optional[Dict[str, str]] = None,
        memory: str = "512Mi",
        cpu: str = "1",
        max_instances: Optional[int] = None,
        min_instances: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> CloudRunService:
        """Create a new Cloud Run service.

        Args:
            location: The GCP location/region
            service_name: The name of the service to create
            image: The container image URI to deploy
            port: The container port (default: 8080)
            env_vars: Optional environment variables as key-value pairs
            memory: Memory limit for the container (default: "512Mi")
            cpu: CPU limit for the container (default: "1")
            max_instances: Optional maximum number of instances
            min_instances: Optional minimum number of instances
            labels: Optional labels to apply to the service

        Returns:
            A CloudRunService instance for the newly created service
        """
        parent = self._format_parent(location)
        logger.debug(
            "Creating Cloud Run service %s in %s", service_name, parent
        )

        # Build container spec
        container = {
            "image": image,
            "ports": [{"containerPort": port}],
            "resources": {
                "limits": {
                    "memory": memory,
                    "cpu": cpu,
                },
            },
        }

        # Add environment variables
        if env_vars:
            container["env"] = [
                {"name": k, "value": v} for k, v in env_vars.items()
            ]

        # Build template
        template = {
            "containers": [container],
        }

        # Add scaling settings
        scaling = {}
        if max_instances is not None:
            scaling["maxInstanceCount"] = max_instances
        if min_instances is not None:
            scaling["minInstanceCount"] = min_instances
        if scaling:
            template["scaling"] = scaling

        # Build service body
        body = {
            "template": template,
        }

        if labels:
            body["labels"] = labels

        # Process tags via base class
        body = self._process_tags(body, None)

        try:
            request = (
                self.service.projects()
                .locations()
                .services()
                .create(parent=parent, serviceId=service_name, body=body)
            )
            response = request.execute()

            return CloudRunService.from_api_response(
                response, self.project_id
            )
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"Cloud Run service '{service_name}' already exists in {location}"
                )
            raise

    def update_service(
        self,
        location: str,
        service_name: str,
        update_fields: Dict[str, Any],
    ) -> CloudRunService:
        """Update a Cloud Run service.

        Args:
            location: The GCP location/region
            service_name: The name of the service to update
            update_fields: Dictionary of fields to update

        Returns:
            The updated CloudRunService instance
        """
        full_name = self._format_service_name(location, service_name)
        logger.debug("Updating Cloud Run service %s", full_name)

        request = (
            self.service.projects()
            .locations()
            .services()
            .patch(name=full_name, body=update_fields)
        )
        response = request.execute()

        return CloudRunService.from_api_response(response, self.project_id)

    def delete_service(self, location: str, service_name: str) -> bool:
        """Delete a Cloud Run service.

        Args:
            location: The GCP location/region
            service_name: The name of the service to delete

        Returns:
            True if the deletion was successful
        """
        full_name = self._format_service_name(location, service_name)
        logger.debug("Deleting Cloud Run service %s", full_name)

        request = (
            self.service.projects()
            .locations()
            .services()
            .delete(name=full_name)
        )
        request.execute()

        return True

    def list_revisions(
        self, location: str, service_name: str, **kwargs
    ) -> List[CloudRunRevision]:
        """List revisions for a Cloud Run service.

        Args:
            location: The GCP location/region
            service_name: The name of the service
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of CloudRunRevision instances
        """
        parent = self._format_service_name(location, service_name)
        logger.debug("Listing revisions for Cloud Run service %s", parent)

        request = (
            self.service.projects()
            .locations()
            .services()
            .revisions()
            .list(parent=parent, **kwargs)
        )

        revisions = []
        while request is not None:
            response = request.execute()
            for rev_data in response.get("revisions", []):
                revisions.append(
                    CloudRunRevision.from_api_response(
                        rev_data, self.project_id
                    )
                )

            request = (
                self.service.projects()
                .locations()
                .services()
                .revisions()
                .list_next(request, response)
            )

        return revisions

    def get_revision(
        self, location: str, revision_name: str
    ) -> CloudRunRevision:
        """Get a specific Cloud Run revision.

        Args:
            location: The GCP location/region
            revision_name: The name of the revision to retrieve

        Returns:
            A CloudRunRevision instance
        """
        full_name = self._format_revision_name(location, revision_name)
        logger.debug("Getting Cloud Run revision %s", full_name)

        request = (
            self.service.projects()
            .locations()
            .services()
            .revisions()
            .get(name=full_name)
        )
        response = request.execute()

        return CloudRunRevision.from_api_response(response, self.project_id)

    def delete_revision(self, location: str, revision_name: str) -> bool:
        """Delete a Cloud Run revision.

        Args:
            location: The GCP location/region
            revision_name: The name of the revision to delete

        Returns:
            True if the deletion was successful
        """
        full_name = self._format_revision_name(location, revision_name)
        logger.debug("Deleting Cloud Run revision %s", full_name)

        request = (
            self.service.projects()
            .locations()
            .services()
            .revisions()
            .delete(name=full_name)
        )
        request.execute()

        return True

    def get_iam_policy(
        self, location: str, service_name: str
    ) -> Dict[str, Any]:
        """Get the IAM policy for a Cloud Run service.

        Args:
            location: The GCP location/region
            service_name: The name of the service

        Returns:
            The IAM policy dictionary
        """
        full_name = self._format_service_name(location, service_name)
        logger.debug("Getting IAM policy for Cloud Run service %s", full_name)

        request = (
            self.service.projects()
            .locations()
            .services()
            .getIamPolicy(resource=full_name)
        )
        return request.execute()

    def set_iam_policy(
        self, location: str, service_name: str, policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set the IAM policy for a Cloud Run service.

        Args:
            location: The GCP location/region
            service_name: The name of the service
            policy: The IAM policy to set

        Returns:
            The updated IAM policy dictionary
        """
        full_name = self._format_service_name(location, service_name)
        logger.debug("Setting IAM policy for Cloud Run service %s", full_name)

        request = (
            self.service.projects()
            .locations()
            .services()
            .setIamPolicy(
                resource=full_name, body={"policy": policy}
            )
        )
        return request.execute()
