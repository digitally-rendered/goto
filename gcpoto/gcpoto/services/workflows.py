"""Service implementation for Google Cloud Workflows."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.workflows import Workflow, WorkflowExecution
from gcpoto.exceptions import (
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class WorkflowsService(GCPService[Workflow]):
    """Service for interacting with Google Cloud Workflows."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Workflows service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="workflows",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Workflow,
            **kwargs,
        )
        self._executions_service = self._create_executions_service()

    def _create_executions_service(self):
        """Create the workflow executions service client.

        Returns:
            An authenticated Google API client for workflow executions
        """
        credentials = None
        if self.credentials_file:
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        return build("workflowexecutions", "v1", credentials=credentials)

    def _format_workflow_path(
        self, location: str, workflow_name: str
    ) -> str:
        """Format a fully qualified workflow path.

        Args:
            location: The GCP location (e.g. 'us-central1')
            workflow_name: The workflow name or full path

        Returns:
            The fully qualified workflow resource path
        """
        if "/" in workflow_name:
            return workflow_name
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/workflows/{workflow_name}"
        )

    def _format_execution_path(
        self, location: str, workflow_name: str, execution_id: str
    ) -> str:
        """Format a fully qualified execution path.

        Args:
            location: The GCP location (e.g. 'us-central1')
            workflow_name: The workflow name
            execution_id: The execution ID or full path

        Returns:
            The fully qualified execution resource path
        """
        if "/" in execution_id:
            return execution_id
        workflow_path = self._format_workflow_path(location, workflow_name)
        return f"{workflow_path}/executions/{execution_id}"

    def _format_location_path(self, location: str) -> str:
        """Format a fully qualified location path.

        Args:
            location: The GCP location (e.g. 'us-central1' or '-' for all)

        Returns:
            The fully qualified location resource path
        """
        return f"projects/{self.project_id}/locations/{location}"

    def list_workflows(
        self, location: str = "-", **kwargs
    ) -> List[Workflow]:
        """List workflows in a location.

        Args:
            location: The GCP location (e.g. 'us-central1', '-' for all)
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of Workflow instances
        """
        parent = self._format_location_path(location)

        request = (
            self.service.projects()
            .locations()
            .workflows()
            .list(parent=parent, **kwargs)
        )

        workflows = []
        while request is not None:
            response = request.execute()
            for workflow_data in response.get("workflows", []):
                workflows.append(
                    Workflow.from_api_response(
                        workflow_data, self.project_id
                    )
                )

            request = (
                self.service.projects()
                .locations()
                .workflows()
                .list_next(request, response)
            )

        logger.debug("Listed %s workflows in %s", len(workflows), location)
        return workflows

    def get_workflow(
        self, location: str, workflow_name: str
    ) -> Workflow:
        """Get a specific workflow.

        Args:
            location: The GCP location (e.g. 'us-central1')
            workflow_name: The name of the workflow to retrieve

        Returns:
            A Workflow instance
        """
        name = self._format_workflow_path(location, workflow_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .workflows()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("workflow", workflow_name)
            raise

        logger.debug("Retrieved workflow %s", workflow_name)
        return Workflow.from_api_response(response, self.project_id)

    def create_workflow(
        self,
        location: str,
        workflow_name: str,
        source_contents: str,
        description: Optional[str] = None,
        service_account: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Workflow:
        """Create a new workflow.

        Args:
            location: The GCP location (e.g. 'us-central1')
            workflow_name: The name of the workflow to create
            source_contents: The workflow source code (YAML or JSON)
            description: Optional description of the workflow
            service_account: Optional IAM service account email
            labels: Optional labels to apply to the workflow

        Returns:
            A Workflow instance for the newly created workflow
        """
        parent = self._format_location_path(location)

        body: Dict[str, Any] = {
            "sourceContents": source_contents,
        }

        if description is not None:
            body["description"] = description

        if service_account is not None:
            body["serviceAccount"] = service_account

        if labels is not None:
            body["labels"] = labels

        try:
            request = (
                self.service.projects()
                .locations()
                .workflows()
                .create(
                    parent=parent,
                    body=body,
                    workflowId=workflow_name,
                )
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"Workflow '{workflow_name}' already exists"
                )
            raise

        logger.debug("Created workflow %s in %s", workflow_name, location)
        return Workflow.from_api_response(response, self.project_id)

    def update_workflow(
        self,
        location: str,
        workflow_name: str,
        source_contents: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Workflow:
        """Update an existing workflow.

        Args:
            location: The GCP location (e.g. 'us-central1')
            workflow_name: The name of the workflow to update
            source_contents: Optional updated workflow source code
            description: Optional updated description

        Returns:
            The updated Workflow instance
        """
        name = self._format_workflow_path(location, workflow_name)

        body: Dict[str, Any] = {"name": name}
        update_mask_fields = []

        if source_contents is not None:
            body["sourceContents"] = source_contents
            update_mask_fields.append("sourceContents")

        if description is not None:
            body["description"] = description
            update_mask_fields.append("description")

        update_mask = ",".join(update_mask_fields)

        try:
            request = (
                self.service.projects()
                .locations()
                .workflows()
                .patch(name=name, body=body, updateMask=update_mask)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("workflow", workflow_name)
            raise

        logger.debug("Updated workflow %s in %s", workflow_name, location)
        return Workflow.from_api_response(response, self.project_id)

    def delete_workflow(self, location: str, workflow_name: str) -> bool:
        """Delete a workflow.

        Args:
            location: The GCP location (e.g. 'us-central1')
            workflow_name: The name of the workflow to delete

        Returns:
            True if the deletion was successful
        """
        name = self._format_workflow_path(location, workflow_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .workflows()
                .delete(name=name)
            )
            request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("workflow", workflow_name)
            raise

        logger.debug("Deleted workflow %s in %s", workflow_name, location)
        return True

    def execute_workflow(
        self,
        location: str,
        workflow_name: str,
        argument: Optional[str] = None,
    ) -> WorkflowExecution:
        """Execute a workflow.

        Args:
            location: The GCP location (e.g. 'us-central1')
            workflow_name: The name of the workflow to execute
            argument: Optional JSON argument to pass to the workflow

        Returns:
            A WorkflowExecution instance for the new execution
        """
        parent = self._format_workflow_path(location, workflow_name)

        body: Dict[str, Any] = {}
        if argument is not None:
            body["argument"] = argument

        try:
            request = (
                self._executions_service.projects()
                .locations()
                .workflows()
                .executions()
                .create(parent=parent, body=body)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("workflow", workflow_name)
            raise

        logger.debug("Executed workflow %s", workflow_name)
        return WorkflowExecution.from_api_response(
            response, self.project_id
        )

    def get_execution(
        self,
        location: str,
        workflow_name: str,
        execution_id: str,
    ) -> WorkflowExecution:
        """Get a specific workflow execution.

        Args:
            location: The GCP location (e.g. 'us-central1')
            workflow_name: The name of the workflow
            execution_id: The ID of the execution to retrieve

        Returns:
            A WorkflowExecution instance
        """
        name = self._format_execution_path(
            location, workflow_name, execution_id
        )

        try:
            request = (
                self._executions_service.projects()
                .locations()
                .workflows()
                .executions()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("execution", execution_id)
            raise

        logger.debug(
            "Retrieved execution %s for workflow %s",
            execution_id,
            workflow_name,
        )
        return WorkflowExecution.from_api_response(
            response, self.project_id
        )

    def list_executions(
        self,
        location: str,
        workflow_name: str,
        **kwargs,
    ) -> List[WorkflowExecution]:
        """List executions for a workflow.

        Args:
            location: The GCP location (e.g. 'us-central1')
            workflow_name: The name of the workflow
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of WorkflowExecution instances
        """
        parent = self._format_workflow_path(location, workflow_name)

        request = (
            self._executions_service.projects()
            .locations()
            .workflows()
            .executions()
            .list(parent=parent, **kwargs)
        )

        executions = []
        while request is not None:
            response = request.execute()
            for exec_data in response.get("executions", []):
                executions.append(
                    WorkflowExecution.from_api_response(
                        exec_data, self.project_id
                    )
                )

            request = (
                self._executions_service.projects()
                .locations()
                .workflows()
                .executions()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s executions for workflow %s",
            len(executions),
            workflow_name,
        )
        return executions

    def cancel_execution(
        self,
        location: str,
        workflow_name: str,
        execution_id: str,
    ) -> WorkflowExecution:
        """Cancel a workflow execution.

        Args:
            location: The GCP location (e.g. 'us-central1')
            workflow_name: The name of the workflow
            execution_id: The ID of the execution to cancel

        Returns:
            The cancelled WorkflowExecution instance
        """
        name = self._format_execution_path(
            location, workflow_name, execution_id
        )

        try:
            request = (
                self._executions_service.projects()
                .locations()
                .workflows()
                .executions()
                .cancel(name=name, body={})
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("execution", execution_id)
            raise

        logger.debug(
            "Cancelled execution %s for workflow %s",
            execution_id,
            workflow_name,
        )
        return WorkflowExecution.from_api_response(
            response, self.project_id
        )
