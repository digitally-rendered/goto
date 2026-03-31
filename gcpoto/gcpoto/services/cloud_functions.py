"""Service implementation for Google Cloud Functions."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.cloud_functions import CloudFunction
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class CloudFunctionsService(GCPService[CloudFunction]):
    """Service for interacting with Google Cloud Functions."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Functions service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="cloudfunctions",
            version="v1",
            credentials_file=credentials_file,
            resource_model=CloudFunction,
            **kwargs,
        )

    def _format_function_path(
        self, location: str, function_name: str
    ) -> str:
        """Format a fully qualified Cloud Function resource path.

        Args:
            location: The location (region) of the function
            function_name: The function name

        Returns:
            The fully qualified function path
        """
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/functions/{function_name}"
        )

    def _format_location_path(self, location: str = "-") -> str:
        """Format a fully qualified location path.

        Args:
            location: The location (region), or '-' for all locations

        Returns:
            The fully qualified location path
        """
        return f"projects/{self.project_id}/locations/{location}"

    def list_functions(
        self, location: str = "-", **kwargs
    ) -> List[CloudFunction]:
        """List Cloud Functions in the project.

        Args:
            location: The location to list functions in. Use '-' for all locations.
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of CloudFunction instances
        """
        parent = self._format_location_path(location)

        functions = []
        request = (
            self.service.projects()
            .locations()
            .functions()
            .list(parent=parent, **kwargs)
        )

        while request is not None:
            response = request.execute()
            for function_data in response.get("functions", []):
                functions.append(self._parse_response(function_data))

            request = (
                self.service.projects()
                .locations()
                .functions()
                .list_next(request, response)
            )

        return functions

    def get_function(
        self, location: str, function_name: str
    ) -> CloudFunction:
        """Get a specific Cloud Function.

        Args:
            location: The location (region) of the function
            function_name: The name of the function

        Returns:
            A CloudFunction instance
        """
        name = self._format_function_path(location, function_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .functions()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "CloudFunction", function_name
                )
            raise APIError(e.resp.status, str(e))

        return self._parse_response(response)

    def create_function(
        self,
        location: str,
        function_name: str,
        runtime: str,
        entry_point: str,
        source_archive_url: Optional[str] = None,
        trigger: Optional[Dict[str, Any]] = None,
        environment_variables: Optional[Dict[str, str]] = None,
        timeout: Optional[str] = None,
        memory_mb: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> CloudFunction:
        """Create a new Cloud Function.

        Args:
            location: The location (region) to create the function in
            function_name: The name of the function
            runtime: The runtime environment (e.g. 'python39', 'nodejs16')
            entry_point: The name of the function entry point
            source_archive_url: Optional GCS URL to the function source archive
            trigger: Optional trigger configuration dict
            environment_variables: Optional environment variables
            timeout: Optional execution timeout (e.g. '60s')
            memory_mb: Optional available memory in MB
            labels: Optional labels to apply to the function

        Returns:
            A CloudFunction instance for the newly created function
        """
        parent = self._format_location_path(location)
        name = self._format_function_path(location, function_name)

        body: Dict[str, Any] = {
            "name": name,
            "runtime": runtime,
            "entryPoint": entry_point,
        }

        if source_archive_url is not None:
            body["sourceArchiveUrl"] = source_archive_url

        if trigger is not None:
            # Merge trigger config into the body (httpsTrigger or eventTrigger)
            body.update(trigger)
        else:
            # Default to HTTPS trigger
            body["httpsTrigger"] = {}

        if environment_variables is not None:
            body["environmentVariables"] = environment_variables

        if timeout is not None:
            body["timeout"] = timeout

        if memory_mb is not None:
            body["availableMemoryMb"] = memory_mb

        if labels is not None:
            body["labels"] = labels

        body = self._process_tags(body, labels)

        try:
            request = (
                self.service.projects()
                .locations()
                .functions()
                .create(location=parent, body=body)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 409:
                raise APIError(
                    409,
                    f"Function '{function_name}' already exists in {location}",
                )
            raise APIError(e.resp.status, str(e))

        logger.info(
            "Created Cloud Function %s in %s", function_name, location
        )
        return self._parse_response(response)

    def update_function(
        self,
        location: str,
        function_name: str,
        update_fields: Dict[str, Any],
    ) -> CloudFunction:
        """Update an existing Cloud Function.

        Args:
            location: The location (region) of the function
            function_name: The name of the function
            update_fields: A dictionary of fields to update

        Returns:
            The updated CloudFunction instance
        """
        name = self._format_function_path(location, function_name)

        body: Dict[str, Any] = {"name": name}
        body.update(update_fields)

        # Build the update mask from the provided fields
        update_mask = ",".join(update_fields.keys())

        try:
            request = (
                self.service.projects()
                .locations()
                .functions()
                .patch(name=name, body=body, updateMask=update_mask)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "CloudFunction", function_name
                )
            raise APIError(e.resp.status, str(e))

        logger.info(
            "Updated Cloud Function %s in %s", function_name, location
        )
        return self._parse_response(response)

    def delete_function(
        self, location: str, function_name: str
    ) -> bool:
        """Delete a Cloud Function.

        Args:
            location: The location (region) of the function
            function_name: The name of the function

        Returns:
            True if the deletion was successful
        """
        name = self._format_function_path(location, function_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .functions()
                .delete(name=name)
            )
            request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "CloudFunction", function_name
                )
            raise APIError(e.resp.status, str(e))

        logger.info(
            "Deleted Cloud Function %s in %s", function_name, location
        )
        return True

    def call_function(
        self,
        location: str,
        function_name: str,
        data: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call (invoke) a Cloud Function.

        Args:
            location: The location (region) of the function
            function_name: The name of the function
            data: Optional JSON string data to pass to the function

        Returns:
            A dictionary containing the function execution result
        """
        name = self._format_function_path(location, function_name)

        body: Dict[str, Any] = {}
        if data is not None:
            body["data"] = data

        try:
            request = (
                self.service.projects()
                .locations()
                .functions()
                .call(name=name, body=body)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "CloudFunction", function_name
                )
            raise APIError(e.resp.status, str(e))

        logger.info(
            "Called Cloud Function %s in %s", function_name, location
        )
        return response

    def get_iam_policy(
        self, location: str, function_name: str
    ) -> Dict[str, Any]:
        """Get the IAM policy for a Cloud Function.

        Args:
            location: The location (region) of the function
            function_name: The name of the function

        Returns:
            The IAM policy dictionary
        """
        resource = self._format_function_path(location, function_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .functions()
                .getIamPolicy(resource=resource)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "CloudFunction", function_name
                )
            raise APIError(e.resp.status, str(e))

        return response

    def set_iam_policy(
        self,
        location: str,
        function_name: str,
        policy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Set the IAM policy for a Cloud Function.

        Args:
            location: The location (region) of the function
            function_name: The name of the function
            policy: The IAM policy dictionary to set

        Returns:
            The updated IAM policy dictionary
        """
        resource = self._format_function_path(location, function_name)

        body = {"policy": policy}

        try:
            request = (
                self.service.projects()
                .locations()
                .functions()
                .setIamPolicy(resource=resource, body=body)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "CloudFunction", function_name
                )
            raise APIError(e.resp.status, str(e))

        logger.info(
            "Set IAM policy for Cloud Function %s in %s",
            function_name,
            location,
        )
        return response
