"""Service implementation for Google Cloud Deploy."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.cloud_deploy import DeliveryPipeline, Release, Rollout
from gcpoto.exceptions import ResourceAlreadyExistsError, ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class CloudDeployService(GCPService[DeliveryPipeline]):
    """Service for interacting with Google Cloud Deploy."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Deploy service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="clouddeploy",
            version="v1",
            credentials_file=credentials_file,
            resource_model=DeliveryPipeline,
            **kwargs,
        )

    def _format_location_path(self, location: str) -> str:
        """Format a fully qualified location path.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            The fully qualified location resource path
        """
        return f"projects/{self.project_id}/locations/{location}"

    def _format_pipeline_path(self, location: str, pipeline_name: str) -> str:
        """Format a fully qualified delivery pipeline path.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The pipeline name or full path

        Returns:
            The fully qualified pipeline resource path
        """
        if "/" in pipeline_name:
            return pipeline_name
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/deliveryPipelines/{pipeline_name}"
        )

    def _format_release_path(
        self, location: str, pipeline_name: str, release_name: str
    ) -> str:
        """Format a fully qualified release path.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The pipeline name
            release_name: The release name or full path

        Returns:
            The fully qualified release resource path
        """
        if "/" in release_name:
            return release_name
        pipeline_path = self._format_pipeline_path(location, pipeline_name)
        return f"{pipeline_path}/releases/{release_name}"

    def _format_rollout_path(
        self,
        location: str,
        pipeline_name: str,
        release_name: str,
        rollout_name: str,
    ) -> str:
        """Format a fully qualified rollout path.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The pipeline name
            release_name: The release name
            rollout_name: The rollout name or full path

        Returns:
            The fully qualified rollout resource path
        """
        if "/" in rollout_name:
            return rollout_name
        release_path = self._format_release_path(
            location, pipeline_name, release_name
        )
        return f"{release_path}/rollouts/{rollout_name}"

    # ── Delivery Pipeline methods ──────────────────────────────────────

    def list_pipelines(self, location: str, **kwargs) -> List[DeliveryPipeline]:
        """List Cloud Deploy delivery pipelines in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of DeliveryPipeline instances
        """
        parent = self._format_location_path(location)

        request = (
            self.service.projects()
            .locations()
            .deliveryPipelines()
            .list(parent=parent, **kwargs)
        )

        pipelines = []
        while request is not None:
            response = request.execute()
            for item in response.get("deliveryPipelines", []):
                pipelines.append(
                    DeliveryPipeline.from_api_response(item, self.project_id)
                )

            request = (
                self.service.projects()
                .locations()
                .deliveryPipelines()
                .list_next(request, response)
            )

        logger.debug("Listed %s pipelines in %s", len(pipelines), location)
        return pipelines

    def get_pipeline(
        self, location: str, pipeline_name: str
    ) -> DeliveryPipeline:
        """Get a specific Cloud Deploy delivery pipeline.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The name of the pipeline to retrieve

        Returns:
            A DeliveryPipeline instance
        """
        name = self._format_pipeline_path(location, pipeline_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .deliveryPipelines()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("deliveryPipeline", pipeline_name)
            raise

        logger.debug("Retrieved pipeline %s", pipeline_name)
        return DeliveryPipeline.from_api_response(response, self.project_id)

    def create_pipeline(
        self,
        location: str,
        pipeline_name: str,
        serial_pipeline: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> DeliveryPipeline:
        """Create a new Cloud Deploy delivery pipeline.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The name of the pipeline to create
            serial_pipeline: Optional serial pipeline configuration
            description: Optional description for the pipeline
            labels: Optional labels for the pipeline

        Returns:
            A DeliveryPipeline instance for the newly created pipeline
        """
        parent = self._format_location_path(location)

        body: Dict[str, Any] = {}

        if serial_pipeline is not None:
            body["serialPipeline"] = serial_pipeline

        if description is not None:
            body["description"] = description

        if labels is not None:
            body["labels"] = labels

        try:
            request = (
                self.service.projects()
                .locations()
                .deliveryPipelines()
                .create(
                    parent=parent,
                    body=body,
                    deliveryPipelineId=pipeline_name,
                )
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"Delivery pipeline '{pipeline_name}' already exists"
                )
            raise

        logger.debug("Created pipeline %s in %s", pipeline_name, location)
        return DeliveryPipeline.from_api_response(response, self.project_id)

    def delete_pipeline(self, location: str, pipeline_name: str) -> bool:
        """Delete a Cloud Deploy delivery pipeline.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The name of the pipeline to delete

        Returns:
            True if the deletion was successful
        """
        name = self._format_pipeline_path(location, pipeline_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .deliveryPipelines()
                .delete(name=name)
            )
            request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("deliveryPipeline", pipeline_name)
            raise

        logger.debug("Deleted pipeline %s in %s", pipeline_name, location)
        return True

    # ── Release methods ────────────────────────────────────────────────

    def list_releases(
        self, location: str, pipeline_name: str, **kwargs
    ) -> List[Release]:
        """List releases for a Cloud Deploy delivery pipeline.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The name of the delivery pipeline
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of Release instances
        """
        parent = self._format_pipeline_path(location, pipeline_name)

        request = (
            self.service.projects()
            .locations()
            .deliveryPipelines()
            .releases()
            .list(parent=parent, **kwargs)
        )

        releases = []
        while request is not None:
            response = request.execute()
            for item in response.get("releases", []):
                releases.append(
                    Release.from_api_response(item, self.project_id)
                )

            request = (
                self.service.projects()
                .locations()
                .deliveryPipelines()
                .releases()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s releases for pipeline %s",
            len(releases),
            pipeline_name,
        )
        return releases

    def get_release(
        self, location: str, pipeline_name: str, release_name: str
    ) -> Release:
        """Get a specific release from a Cloud Deploy delivery pipeline.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The name of the delivery pipeline
            release_name: The name of the release to retrieve

        Returns:
            A Release instance
        """
        name = self._format_release_path(
            location, pipeline_name, release_name
        )

        try:
            request = (
                self.service.projects()
                .locations()
                .deliveryPipelines()
                .releases()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("release", release_name)
            raise

        logger.debug(
            "Retrieved release %s from pipeline %s",
            release_name,
            pipeline_name,
        )
        return Release.from_api_response(response, self.project_id)

    def create_release(
        self,
        location: str,
        pipeline_name: str,
        release_name: str,
        skaffold_config_uri: str,
        skaffold_config_path: Optional[str] = None,
    ) -> Release:
        """Create a new release in a Cloud Deploy delivery pipeline.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The name of the delivery pipeline
            release_name: The name of the release to create
            skaffold_config_uri: Cloud Storage URI of the skaffold config
            skaffold_config_path: Optional filepath of the skaffold config

        Returns:
            A Release instance for the newly created release
        """
        parent = self._format_pipeline_path(location, pipeline_name)

        body: Dict[str, Any] = {
            "skaffoldConfigUri": skaffold_config_uri,
        }

        if skaffold_config_path is not None:
            body["skaffoldConfigPath"] = skaffold_config_path

        try:
            request = (
                self.service.projects()
                .locations()
                .deliveryPipelines()
                .releases()
                .create(
                    parent=parent,
                    body=body,
                    releaseId=release_name,
                )
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"Release '{release_name}' already exists"
                )
            raise

        logger.debug(
            "Created release %s in pipeline %s",
            release_name,
            pipeline_name,
        )
        return Release.from_api_response(response, self.project_id)

    # ── Rollout methods ────────────────────────────────────────────────

    def list_rollouts(
        self,
        location: str,
        pipeline_name: str,
        release_name: str,
        **kwargs,
    ) -> List[Rollout]:
        """List rollouts for a Cloud Deploy release.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The name of the delivery pipeline
            release_name: The name of the release
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of Rollout instances
        """
        parent = self._format_release_path(
            location, pipeline_name, release_name
        )

        request = (
            self.service.projects()
            .locations()
            .deliveryPipelines()
            .releases()
            .rollouts()
            .list(parent=parent, **kwargs)
        )

        rollouts = []
        while request is not None:
            response = request.execute()
            for item in response.get("rollouts", []):
                rollouts.append(
                    Rollout.from_api_response(item, self.project_id)
                )

            request = (
                self.service.projects()
                .locations()
                .deliveryPipelines()
                .releases()
                .rollouts()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s rollouts for release %s",
            len(rollouts),
            release_name,
        )
        return rollouts

    def get_rollout(
        self,
        location: str,
        pipeline_name: str,
        release_name: str,
        rollout_name: str,
    ) -> Rollout:
        """Get a specific rollout from a Cloud Deploy release.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The name of the delivery pipeline
            release_name: The name of the release
            rollout_name: The name of the rollout to retrieve

        Returns:
            A Rollout instance
        """
        name = self._format_rollout_path(
            location, pipeline_name, release_name, rollout_name
        )

        try:
            request = (
                self.service.projects()
                .locations()
                .deliveryPipelines()
                .releases()
                .rollouts()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("rollout", rollout_name)
            raise

        logger.debug(
            "Retrieved rollout %s from release %s",
            rollout_name,
            release_name,
        )
        return Rollout.from_api_response(response, self.project_id)

    def create_rollout(
        self,
        location: str,
        pipeline_name: str,
        release_name: str,
        rollout_name: str,
        target_id: str,
    ) -> Rollout:
        """Create a new rollout for a Cloud Deploy release.

        Args:
            location: The GCP location (e.g. 'us-central1')
            pipeline_name: The name of the delivery pipeline
            release_name: The name of the release
            rollout_name: The name of the rollout to create
            target_id: The target to which the rollout deploys

        Returns:
            A Rollout instance for the newly created rollout
        """
        parent = self._format_release_path(
            location, pipeline_name, release_name
        )

        body: Dict[str, Any] = {
            "targetId": target_id,
        }

        try:
            request = (
                self.service.projects()
                .locations()
                .deliveryPipelines()
                .releases()
                .rollouts()
                .create(
                    parent=parent,
                    body=body,
                    rolloutId=rollout_name,
                )
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"Rollout '{rollout_name}' already exists"
                )
            raise

        logger.debug(
            "Created rollout %s for release %s",
            rollout_name,
            release_name,
        )
        return Rollout.from_api_response(response, self.project_id)
