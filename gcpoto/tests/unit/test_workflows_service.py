"""Tests for Workflows service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.workflows import WorkflowsService
from gcpoto.models.workflows import Workflow, WorkflowExecution
from gcpoto.exceptions import ResourceNotFoundError, ResourceAlreadyExistsError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
WORKFLOW_NAME = "test-workflow"
EXECUTION_ID = "exec-abc-123"

WORKFLOW_PATH = (
    f"projects/{PROJECT_ID}/locations/{LOCATION}/workflows/{WORKFLOW_NAME}"
)
EXECUTION_PATH = f"{WORKFLOW_PATH}/executions/{EXECUTION_ID}"
LOCATION_PATH = f"projects/{PROJECT_ID}/locations/{LOCATION}"

SAMPLE_SOURCE = """
- init:
    assign:
      - message: "Hello, World!"
- return_message:
    return: ${message}
"""


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    mock_workflows_service = mock.MagicMock()
    mock_executions_service = mock.MagicMock()

    def build_side_effect(service_name, version, credentials=None):
        if service_name == "workflowexecutions":
            return mock_executions_service
        return mock_workflows_service

    with mock.patch(
        "googleapiclient.discovery.build", side_effect=build_side_effect
    ) as mock_build_discovery, mock.patch(
        "gcpoto.services.workflows.build", side_effect=build_side_effect
    ) as mock_build_local:
        # Set up projects().locations().workflows() chain for workflows service
        mock_workflows = mock.MagicMock()
        mock_workflows_service.projects.return_value.locations.return_value.workflows.return_value = (
            mock_workflows
        )

        # Set up projects().locations().workflows().executions() chain for executions service
        mock_executions = mock.MagicMock()
        mock_executions_service.projects.return_value.locations.return_value.workflows.return_value.executions.return_value = (
            mock_executions
        )

        yield {
            "build": mock_build_local,
            "workflows_service": mock_workflows_service,
            "executions_service": mock_executions_service,
            "workflows": mock_workflows,
            "executions": mock_executions,
        }


@pytest.fixture
def service(mock_google_client):
    """Create a WorkflowsService with mocked client."""
    return WorkflowsService(project_id=PROJECT_ID)


@pytest.fixture
def mock_workflows(mock_google_client):
    """Shortcut to mock workflows resource."""
    return mock_google_client["workflows"]


@pytest.fixture
def mock_executions(mock_google_client):
    """Shortcut to mock executions resource."""
    return mock_google_client["executions"]


@pytest.fixture
def sample_workflow_response():
    """Sample Workflows API response."""
    return {
        "name": WORKFLOW_PATH,
        "description": "A test workflow",
        "state": "ACTIVE",
        "revisionId": "000001-abc",
        "sourceContents": SAMPLE_SOURCE,
        "serviceAccount": "workflow-sa@test-project.iam.gserviceaccount.com",
        "labels": {"env": "test", "team": "platform"},
        "createTime": "2026-03-01T10:00:00Z",
        "updateTime": "2026-03-15T12:00:00Z",
    }


@pytest.fixture
def sample_execution_response():
    """Sample Workflow Execution API response."""
    return {
        "name": EXECUTION_PATH,
        "state": "SUCCEEDED",
        "argument": '{"input": "value"}',
        "result": '{"output": "result"}',
        "startTime": "2026-03-31T10:00:00Z",
        "endTime": "2026-03-31T10:00:05Z",
        "callLogLevel": "LOG_ALL_CALLS",
    }


class TestWorkflowsServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the WorkflowsService."""
        svc = WorkflowsService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID

        # The executions service build is called via the local import
        mock_google_client["build"].assert_any_call(
            "workflowexecutions", "v1", credentials=None
        )

    def test_init_with_credentials_file(self, mock_google_client):
        """Test initializing with a credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()

            svc = WorkflowsService(
                project_id=PROJECT_ID,
                credentials_file="/path/to/creds.json",
            )
            assert svc.project_id == PROJECT_ID
            assert mock_creds.call_count >= 1


class TestListWorkflows:
    def test_list_workflows(
        self, service, mock_workflows, sample_workflow_response
    ):
        """Test listing workflows."""
        mock_request = mock.MagicMock()
        mock_workflows.list.return_value = mock_request
        mock_request.execute.return_value = {
            "workflows": [sample_workflow_response, sample_workflow_response]
        }
        mock_workflows.list_next.return_value = None

        workflows = service.list_workflows(LOCATION)

        mock_workflows.list.assert_called_once_with(parent=LOCATION_PATH)
        assert len(workflows) == 2
        assert isinstance(workflows[0], Workflow)
        assert workflows[0].name == WORKFLOW_NAME
        assert workflows[0].project == PROJECT_ID
        assert workflows[0].location == LOCATION

    def test_list_workflows_all_locations(
        self, service, mock_workflows, sample_workflow_response
    ):
        """Test listing workflows across all locations."""
        mock_request = mock.MagicMock()
        mock_workflows.list.return_value = mock_request
        mock_request.execute.return_value = {
            "workflows": [sample_workflow_response]
        }
        mock_workflows.list_next.return_value = None

        workflows = service.list_workflows()

        mock_workflows.list.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/-"
        )
        assert len(workflows) == 1

    def test_list_workflows_empty(self, service, mock_workflows):
        """Test listing workflows when none exist."""
        mock_request = mock.MagicMock()
        mock_workflows.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_workflows.list_next.return_value = None

        workflows = service.list_workflows(LOCATION)

        assert len(workflows) == 0

    def test_list_workflows_pagination(
        self, service, mock_workflows, sample_workflow_response
    ):
        """Test listing workflows with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_workflows.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "workflows": [sample_workflow_response]
        }

        mock_workflows.list_next.side_effect = [mock_request_page2, None]
        mock_request_page2.execute.return_value = {
            "workflows": [sample_workflow_response]
        }

        workflows = service.list_workflows(LOCATION)
        assert len(workflows) == 2


class TestGetWorkflow:
    def test_get_workflow(
        self, service, mock_workflows, sample_workflow_response
    ):
        """Test getting a specific workflow."""
        mock_request = mock.MagicMock()
        mock_workflows.get.return_value = mock_request
        mock_request.execute.return_value = sample_workflow_response

        workflow = service.get_workflow(LOCATION, WORKFLOW_NAME)

        mock_workflows.get.assert_called_once_with(name=WORKFLOW_PATH)
        assert isinstance(workflow, Workflow)
        assert workflow.name == WORKFLOW_NAME
        assert workflow.description == "A test workflow"
        assert workflow.state == "ACTIVE"
        assert workflow.revision_id == "000001-abc"
        assert workflow.source_contents == SAMPLE_SOURCE
        assert workflow.service_account == (
            "workflow-sa@test-project.iam.gserviceaccount.com"
        )

    def test_get_workflow_not_found(self, service, mock_workflows):
        """Test getting a workflow that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_workflows.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_workflow(LOCATION, WORKFLOW_NAME)

    def test_get_workflow_with_full_path(
        self, service, mock_workflows, sample_workflow_response
    ):
        """Test getting a workflow using a full resource path."""
        mock_request = mock.MagicMock()
        mock_workflows.get.return_value = mock_request
        mock_request.execute.return_value = sample_workflow_response

        service.get_workflow(LOCATION, WORKFLOW_PATH)
        mock_workflows.get.assert_called_once_with(name=WORKFLOW_PATH)


class TestCreateWorkflow:
    def test_create_workflow(
        self, service, mock_workflows, sample_workflow_response
    ):
        """Test creating a new workflow."""
        mock_request = mock.MagicMock()
        mock_workflows.create.return_value = mock_request
        mock_request.execute.return_value = sample_workflow_response

        workflow = service.create_workflow(
            LOCATION,
            WORKFLOW_NAME,
            source_contents=SAMPLE_SOURCE,
            description="A test workflow",
            service_account="workflow-sa@test-project.iam.gserviceaccount.com",
            labels={"env": "test"},
        )

        mock_workflows.create.assert_called_once_with(
            parent=LOCATION_PATH,
            body={
                "sourceContents": SAMPLE_SOURCE,
                "description": "A test workflow",
                "serviceAccount": "workflow-sa@test-project.iam.gserviceaccount.com",
                "labels": {"env": "test"},
            },
            workflowId=WORKFLOW_NAME,
        )
        assert isinstance(workflow, Workflow)
        assert workflow.name == WORKFLOW_NAME

    def test_create_workflow_minimal(
        self, service, mock_workflows, sample_workflow_response
    ):
        """Test creating a workflow with minimal parameters."""
        mock_request = mock.MagicMock()
        mock_workflows.create.return_value = mock_request
        mock_request.execute.return_value = sample_workflow_response

        workflow = service.create_workflow(
            LOCATION, WORKFLOW_NAME, SAMPLE_SOURCE
        )

        mock_workflows.create.assert_called_once_with(
            parent=LOCATION_PATH,
            body={"sourceContents": SAMPLE_SOURCE},
            workflowId=WORKFLOW_NAME,
        )
        assert isinstance(workflow, Workflow)

    def test_create_workflow_already_exists(self, service, mock_workflows):
        """Test creating a workflow that already exists."""
        mock_request = mock.MagicMock()
        mock_workflows.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_workflow(
                LOCATION, WORKFLOW_NAME, SAMPLE_SOURCE
            )


class TestUpdateWorkflow:
    def test_update_workflow_source(
        self, service, mock_workflows, sample_workflow_response
    ):
        """Test updating a workflow's source contents."""
        mock_request = mock.MagicMock()
        mock_workflows.patch.return_value = mock_request
        mock_request.execute.return_value = sample_workflow_response

        new_source = "- return_step:\n    return: 'updated'\n"
        workflow = service.update_workflow(
            LOCATION, WORKFLOW_NAME, source_contents=new_source
        )

        mock_workflows.patch.assert_called_once_with(
            name=WORKFLOW_PATH,
            body={
                "name": WORKFLOW_PATH,
                "sourceContents": new_source,
            },
            updateMask="sourceContents",
        )
        assert isinstance(workflow, Workflow)

    def test_update_workflow_description(
        self, service, mock_workflows, sample_workflow_response
    ):
        """Test updating a workflow's description."""
        mock_request = mock.MagicMock()
        mock_workflows.patch.return_value = mock_request
        mock_request.execute.return_value = sample_workflow_response

        workflow = service.update_workflow(
            LOCATION, WORKFLOW_NAME, description="Updated description"
        )

        mock_workflows.patch.assert_called_once_with(
            name=WORKFLOW_PATH,
            body={
                "name": WORKFLOW_PATH,
                "description": "Updated description",
            },
            updateMask="description",
        )
        assert isinstance(workflow, Workflow)

    def test_update_workflow_multiple_fields(
        self, service, mock_workflows, sample_workflow_response
    ):
        """Test updating multiple workflow fields."""
        mock_request = mock.MagicMock()
        mock_workflows.patch.return_value = mock_request
        mock_request.execute.return_value = sample_workflow_response

        new_source = "- return_step:\n    return: 'updated'\n"
        workflow = service.update_workflow(
            LOCATION,
            WORKFLOW_NAME,
            source_contents=new_source,
            description="Updated",
        )

        mock_workflows.patch.assert_called_once_with(
            name=WORKFLOW_PATH,
            body={
                "name": WORKFLOW_PATH,
                "sourceContents": new_source,
                "description": "Updated",
            },
            updateMask="sourceContents,description",
        )
        assert isinstance(workflow, Workflow)

    def test_update_workflow_not_found(self, service, mock_workflows):
        """Test updating a workflow that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_workflows.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_workflow(
                LOCATION, WORKFLOW_NAME, description="Updated"
            )


class TestDeleteWorkflow:
    def test_delete_workflow(self, service, mock_workflows):
        """Test deleting a workflow."""
        mock_request = mock.MagicMock()
        mock_workflows.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_workflow(LOCATION, WORKFLOW_NAME)

        mock_workflows.delete.assert_called_once_with(name=WORKFLOW_PATH)
        assert result is True

    def test_delete_workflow_not_found(self, service, mock_workflows):
        """Test deleting a workflow that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_workflows.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_workflow(LOCATION, WORKFLOW_NAME)


class TestExecuteWorkflow:
    def test_execute_workflow(
        self, service, mock_executions, sample_execution_response
    ):
        """Test executing a workflow."""
        mock_request = mock.MagicMock()
        mock_executions.create.return_value = mock_request
        mock_request.execute.return_value = sample_execution_response

        execution = service.execute_workflow(
            LOCATION, WORKFLOW_NAME, argument='{"input": "value"}'
        )

        mock_executions.create.assert_called_once_with(
            parent=WORKFLOW_PATH,
            body={"argument": '{"input": "value"}'},
        )
        assert isinstance(execution, WorkflowExecution)
        assert execution.state == "SUCCEEDED"
        assert execution.argument == '{"input": "value"}'

    def test_execute_workflow_no_argument(
        self, service, mock_executions, sample_execution_response
    ):
        """Test executing a workflow without arguments."""
        mock_request = mock.MagicMock()
        mock_executions.create.return_value = mock_request
        mock_request.execute.return_value = sample_execution_response

        execution = service.execute_workflow(LOCATION, WORKFLOW_NAME)

        mock_executions.create.assert_called_once_with(
            parent=WORKFLOW_PATH,
            body={},
        )
        assert isinstance(execution, WorkflowExecution)

    def test_execute_workflow_not_found(self, service, mock_executions):
        """Test executing a workflow that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_executions.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.execute_workflow(LOCATION, WORKFLOW_NAME)


class TestGetExecution:
    def test_get_execution(
        self, service, mock_executions, sample_execution_response
    ):
        """Test getting a specific execution."""
        mock_request = mock.MagicMock()
        mock_executions.get.return_value = mock_request
        mock_request.execute.return_value = sample_execution_response

        execution = service.get_execution(
            LOCATION, WORKFLOW_NAME, EXECUTION_ID
        )

        mock_executions.get.assert_called_once_with(name=EXECUTION_PATH)
        assert isinstance(execution, WorkflowExecution)
        assert execution.name == EXECUTION_ID
        assert execution.state == "SUCCEEDED"
        assert execution.result == '{"output": "result"}'

    def test_get_execution_not_found(self, service, mock_executions):
        """Test getting an execution that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_executions.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_execution(
                LOCATION, WORKFLOW_NAME, EXECUTION_ID
            )

    def test_get_execution_with_full_path(
        self, service, mock_executions, sample_execution_response
    ):
        """Test getting an execution using a full resource path."""
        mock_request = mock.MagicMock()
        mock_executions.get.return_value = mock_request
        mock_request.execute.return_value = sample_execution_response

        service.get_execution(LOCATION, WORKFLOW_NAME, EXECUTION_PATH)
        mock_executions.get.assert_called_once_with(name=EXECUTION_PATH)


class TestListExecutions:
    def test_list_executions(
        self, service, mock_executions, sample_execution_response
    ):
        """Test listing executions for a workflow."""
        mock_request = mock.MagicMock()
        mock_executions.list.return_value = mock_request
        mock_request.execute.return_value = {
            "executions": [
                sample_execution_response,
                sample_execution_response,
            ]
        }
        mock_executions.list_next.return_value = None

        executions = service.list_executions(LOCATION, WORKFLOW_NAME)

        mock_executions.list.assert_called_once_with(parent=WORKFLOW_PATH)
        assert len(executions) == 2
        assert isinstance(executions[0], WorkflowExecution)
        assert executions[0].workflow_name == WORKFLOW_NAME

    def test_list_executions_empty(self, service, mock_executions):
        """Test listing executions when none exist."""
        mock_request = mock.MagicMock()
        mock_executions.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_executions.list_next.return_value = None

        executions = service.list_executions(LOCATION, WORKFLOW_NAME)
        assert len(executions) == 0

    def test_list_executions_pagination(
        self, service, mock_executions, sample_execution_response
    ):
        """Test listing executions with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_executions.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "executions": [sample_execution_response]
        }

        mock_executions.list_next.side_effect = [mock_request_page2, None]
        mock_request_page2.execute.return_value = {
            "executions": [sample_execution_response]
        }

        executions = service.list_executions(LOCATION, WORKFLOW_NAME)
        assert len(executions) == 2


class TestCancelExecution:
    def test_cancel_execution(
        self, service, mock_executions, sample_execution_response
    ):
        """Test cancelling an execution."""
        cancelled_response = {
            **sample_execution_response,
            "state": "CANCELLED",
        }
        mock_request = mock.MagicMock()
        mock_executions.cancel.return_value = mock_request
        mock_request.execute.return_value = cancelled_response

        execution = service.cancel_execution(
            LOCATION, WORKFLOW_NAME, EXECUTION_ID
        )

        mock_executions.cancel.assert_called_once_with(
            name=EXECUTION_PATH, body={}
        )
        assert isinstance(execution, WorkflowExecution)
        assert execution.state == "CANCELLED"

    def test_cancel_execution_not_found(self, service, mock_executions):
        """Test cancelling an execution that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_executions.cancel.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.cancel_execution(
                LOCATION, WORKFLOW_NAME, EXECUTION_ID
            )


class TestWorkflowModel:
    def test_from_api_response(self, sample_workflow_response):
        """Test creating a Workflow from API response."""
        workflow = Workflow.from_api_response(sample_workflow_response)

        assert workflow.name == WORKFLOW_NAME
        assert workflow.project == PROJECT_ID
        assert workflow.location == LOCATION
        assert workflow.id == WORKFLOW_PATH
        assert workflow.type == "workflows.workflow"
        assert workflow.description == "A test workflow"
        assert workflow.state == "ACTIVE"
        assert workflow.revision_id == "000001-abc"
        assert workflow.source_contents == SAMPLE_SOURCE
        assert workflow.service_account == (
            "workflow-sa@test-project.iam.gserviceaccount.com"
        )

    def test_from_api_response_minimal(self):
        """Test creating a Workflow from minimal API response."""
        response = {"name": WORKFLOW_PATH}
        workflow = Workflow.from_api_response(response)

        assert workflow.name == WORKFLOW_NAME
        assert workflow.state == "ACTIVE"
        assert workflow.description is None
        assert workflow.revision_id is None
        assert workflow.source_contents is None
        assert workflow.service_account is None

    def test_get_tag(self, sample_workflow_response):
        """Test getting tags from a Workflow."""
        workflow = Workflow.from_api_response(sample_workflow_response)

        assert workflow.get_tag("env") == "test"
        assert workflow.get_tag("team") == "platform"
        assert workflow.get_tag("missing") == ""
        assert workflow.get_tag("missing", "default") == "default"


class TestWorkflowExecutionModel:
    def test_from_api_response(self, sample_execution_response):
        """Test creating a WorkflowExecution from API response."""
        execution = WorkflowExecution.from_api_response(
            sample_execution_response
        )

        assert execution.name == EXECUTION_ID
        assert execution.project == PROJECT_ID
        assert execution.location == LOCATION
        assert execution.workflow_name == WORKFLOW_NAME
        assert execution.id == EXECUTION_PATH
        assert execution.type == "workflows.execution"
        assert execution.state == "SUCCEEDED"
        assert execution.argument == '{"input": "value"}'
        assert execution.result == '{"output": "result"}'
        assert execution.call_log_level == "LOG_ALL_CALLS"

    def test_from_api_response_minimal(self):
        """Test creating a WorkflowExecution from minimal API response."""
        response = {"name": EXECUTION_PATH}
        execution = WorkflowExecution.from_api_response(response)

        assert execution.name == EXECUTION_ID
        assert execution.state == "ACTIVE"
        assert execution.argument is None
        assert execution.result is None
        assert execution.error is None
        assert execution.start_time is None
        assert execution.end_time is None
        assert execution.call_log_level is None

    def test_from_api_response_with_error(self):
        """Test creating a WorkflowExecution with error information."""
        response = {
            "name": EXECUTION_PATH,
            "state": "FAILED",
            "error": {
                "payload": '{"message": "Something went wrong"}',
                "context": "step: my_step",
            },
        }
        execution = WorkflowExecution.from_api_response(response)

        assert execution.state == "FAILED"
        assert execution.error is not None
        assert "payload" in execution.error
        assert execution.result is None


class TestPathFormatting:
    def test_format_workflow_path(self, service):
        """Test workflow path formatting."""
        assert (
            service._format_workflow_path(LOCATION, WORKFLOW_NAME)
            == WORKFLOW_PATH
        )

    def test_format_workflow_path_already_formatted(self, service):
        """Test that already-formatted workflow paths are returned as-is."""
        assert (
            service._format_workflow_path(LOCATION, WORKFLOW_PATH)
            == WORKFLOW_PATH
        )

    def test_format_execution_path(self, service):
        """Test execution path formatting."""
        assert (
            service._format_execution_path(
                LOCATION, WORKFLOW_NAME, EXECUTION_ID
            )
            == EXECUTION_PATH
        )

    def test_format_execution_path_already_formatted(self, service):
        """Test that already-formatted execution paths are returned as-is."""
        assert (
            service._format_execution_path(
                LOCATION, WORKFLOW_NAME, EXECUTION_PATH
            )
            == EXECUTION_PATH
        )

    def test_format_location_path(self, service):
        """Test location path formatting."""
        assert service._format_location_path(LOCATION) == LOCATION_PATH

    def test_format_location_path_all(self, service):
        """Test location path formatting with wildcard."""
        assert (
            service._format_location_path("-")
            == f"projects/{PROJECT_ID}/locations/-"
        )
