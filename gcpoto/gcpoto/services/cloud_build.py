"""Service implementation for Google Cloud Build."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.cloud_build import Build, BuildTrigger
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class CloudBuildService(GCPService[Build]):
    """Service for interacting with Google Cloud Build."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Build service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="cloudbuild",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Build,
            **kwargs,
        )

    def list_builds(
        self, filter_str: Optional[str] = None, **kwargs
    ) -> List[Build]:
        """List Cloud Build builds.

        Args:
            filter_str: Optional filter string for the list request
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of Build instances
        """
        list_kwargs: Dict[str, Any] = {
            "projectId": self.project_id,
        }

        if filter_str is not None:
            list_kwargs["filter"] = filter_str

        list_kwargs.update(kwargs)

        request = self.service.projects().builds().list(**list_kwargs)

        builds = []
        while request is not None:
            response = request.execute()
            for build_data in response.get("builds", []):
                builds.append(
                    Build.from_api_response(build_data, self.project_id)
                )

            request = (
                self.service.projects()
                .builds()
                .list_next(request, response)
            )

        logger.debug("Listed %s builds", len(builds))
        return builds

    def get_build(self, build_id: str) -> Build:
        """Get a specific Cloud Build build.

        Args:
            build_id: The ID of the build to retrieve

        Returns:
            A Build instance
        """
        try:
            request = (
                self.service.projects()
                .builds()
                .get(projectId=self.project_id, id=build_id)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("build", build_id)
            raise

        logger.debug("Retrieved build %s", build_id)
        return Build.from_api_response(response, self.project_id)

    def create_build(self, build_body: Dict[str, Any]) -> Build:
        """Create a new Cloud Build build.

        Args:
            build_body: The build configuration body

        Returns:
            A Build instance for the newly created build
        """
        try:
            request = (
                self.service.projects()
                .builds()
                .create(projectId=self.project_id, body=build_body)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

        logger.debug("Created build in project %s", self.project_id)
        return Build.from_api_response(response, self.project_id)

    def cancel_build(self, build_id: str) -> Build:
        """Cancel a running Cloud Build build.

        Args:
            build_id: The ID of the build to cancel

        Returns:
            The cancelled Build instance
        """
        try:
            request = (
                self.service.projects()
                .builds()
                .cancel(
                    projectId=self.project_id,
                    id=build_id,
                    body={},
                )
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("build", build_id)
            raise

        logger.debug("Cancelled build %s", build_id)
        return Build.from_api_response(response, self.project_id)

    def retry_build(self, build_id: str) -> Build:
        """Retry a Cloud Build build.

        Args:
            build_id: The ID of the build to retry

        Returns:
            A Build instance for the retried build
        """
        try:
            request = (
                self.service.projects()
                .builds()
                .retry(
                    projectId=self.project_id,
                    id=build_id,
                    body={},
                )
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("build", build_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

        logger.debug("Retried build %s", build_id)
        return Build.from_api_response(response, self.project_id)

    def list_triggers(self, **kwargs) -> List[BuildTrigger]:
        """List Cloud Build triggers.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of BuildTrigger instances
        """
        request = (
            self.service.projects()
            .triggers()
            .list(projectId=self.project_id, **kwargs)
        )

        triggers = []
        while request is not None:
            response = request.execute()
            for trigger_data in response.get("triggers", []):
                triggers.append(
                    BuildTrigger.from_api_response(
                        trigger_data, self.project_id
                    )
                )

            request = (
                self.service.projects()
                .triggers()
                .list_next(request, response)
            )

        logger.debug("Listed %s triggers", len(triggers))
        return triggers

    def get_trigger(self, trigger_id: str) -> BuildTrigger:
        """Get a specific Cloud Build trigger.

        Args:
            trigger_id: The ID of the trigger to retrieve

        Returns:
            A BuildTrigger instance
        """
        try:
            request = (
                self.service.projects()
                .triggers()
                .get(projectId=self.project_id, triggerId=trigger_id)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("trigger", trigger_id)
            raise

        logger.debug("Retrieved trigger %s", trigger_id)
        return BuildTrigger.from_api_response(response, self.project_id)

    def create_trigger(
        self, trigger_body: Dict[str, Any]
    ) -> BuildTrigger:
        """Create a new Cloud Build trigger.

        Args:
            trigger_body: The trigger configuration body

        Returns:
            A BuildTrigger instance for the newly created trigger
        """
        try:
            request = (
                self.service.projects()
                .triggers()
                .create(projectId=self.project_id, body=trigger_body)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

        logger.debug("Created trigger in project %s", self.project_id)
        return BuildTrigger.from_api_response(response, self.project_id)

    def update_trigger(
        self, trigger_id: str, trigger_body: Dict[str, Any]
    ) -> BuildTrigger:
        """Update an existing Cloud Build trigger.

        Args:
            trigger_id: The ID of the trigger to update
            trigger_body: The updated trigger configuration body

        Returns:
            The updated BuildTrigger instance
        """
        try:
            request = (
                self.service.projects()
                .triggers()
                .patch(
                    projectId=self.project_id,
                    triggerId=trigger_id,
                    body=trigger_body,
                )
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("trigger", trigger_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

        logger.debug("Updated trigger %s", trigger_id)
        return BuildTrigger.from_api_response(response, self.project_id)

    def delete_trigger(self, trigger_id: str) -> bool:
        """Delete a Cloud Build trigger.

        Args:
            trigger_id: The ID of the trigger to delete

        Returns:
            True if the deletion was successful
        """
        try:
            self.service.projects().triggers().delete(
                projectId=self.project_id, triggerId=trigger_id
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("trigger", trigger_id)
            raise

        logger.debug("Deleted trigger %s", trigger_id)
        return True

    def run_trigger(
        self,
        trigger_id: str,
        source: Optional[Dict[str, Any]] = None,
    ) -> Build:
        """Run a Cloud Build trigger.

        Args:
            trigger_id: The ID of the trigger to run
            source: Optional source configuration to use for the trigger run

        Returns:
            A Build instance for the triggered build
        """
        body: Dict[str, Any] = {}
        if source is not None:
            body["source"] = source

        try:
            request = (
                self.service.projects()
                .triggers()
                .run(
                    projectId=self.project_id,
                    triggerId=trigger_id,
                    body=body,
                )
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("trigger", trigger_id)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

        logger.debug("Ran trigger %s", trigger_id)
        return Build.from_api_response(response, self.project_id)
