"""Tests for Cloud Functions service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.cloud_functions import CloudFunctionsService
from gcpoto.models.cloud_functions import CloudFunction
from gcpoto.exceptions import ResourceNotFoundError, APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().locations().functions() chain
        mock_functions = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.functions.return_value = (
            mock_functions
        )

        yield mock_service


@pytest.fixture
def sample_function_response():
    """Sample Cloud Functions API response."""
    return {
        "name": "projects/test-project/locations/us-central1/functions/my-function",
        "runtime": "python39",
        "entryPoint": "hello_world",
        "sourceArchiveUrl": "gs://my-bucket/source.zip",
        "status": "ACTIVE",
        "httpsTrigger": {
            "url": "https://us-central1-test-project.cloudfunctions.net/my-function",
            "securityLevel": "SECURE_ALWAYS",
        },
        "timeout": "60s",
        "availableMemoryMb": 256,
        "serviceAccountEmail": "test-project@appspot.gserviceaccount.com",
        "environmentVariables": {"ENV": "production", "DEBUG": "false"},
        "buildEnvironmentVariables": {"GOOGLE_BUILDABLE": "source"},
        "maxInstances": 100,
        "minInstances": 1,
        "vpcConnector": "projects/test-project/locations/us-central1/connectors/my-connector",
        "ingressSettings": "ALLOW_ALL",
        "labels": {"env": "test", "team": "backend"},
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-06-15T12:00:00Z",
    }


@pytest.fixture
def sample_event_function_response():
    """Sample Cloud Functions API response for an event-triggered function."""
    return {
        "name": "projects/test-project/locations/us-east1/functions/event-function",
        "runtime": "nodejs16",
        "entryPoint": "handleEvent",
        "sourceArchiveUrl": "gs://my-bucket/event-source.zip",
        "status": "ACTIVE",
        "eventTrigger": {
            "eventType": "google.storage.object.finalize",
            "resource": "projects/test-project/buckets/my-bucket",
            "service": "storage.googleapis.com",
            "failurePolicy": {"retry": {}},
        },
        "timeout": "120s",
        "availableMemoryMb": 512,
        "labels": {"env": "staging"},
        "createTime": "2025-03-01T00:00:00Z",
        "updateTime": "2025-03-10T00:00:00Z",
    }


@pytest.fixture
def service(mock_google_client):
    """Create a CloudFunctionsService with mocked client."""
    svc = CloudFunctionsService(project_id="test-project")
    return svc


class TestCloudFunctionModel:
    """Tests for the CloudFunction model."""

    def test_from_api_response_https_trigger(self, sample_function_response):
        """Test creating a CloudFunction from an HTTPS-triggered API response."""
        func = CloudFunction.from_api_response(sample_function_response)

        assert func.name == "my-function"
        assert func.project == "test-project"
        assert func.location == "us-central1"
        assert func.runtime == "python39"
        assert func.entry_point == "hello_world"
        assert func.source_archive_url == "gs://my-bucket/source.zip"
        assert func.status == "ACTIVE"
        assert func.timeout == "60s"
        assert func.available_memory_mb == 256
        assert func.service_account_email == "test-project@appspot.gserviceaccount.com"
        assert func.environment_variables == {"ENV": "production", "DEBUG": "false"}
        assert func.build_environment_variables == {"GOOGLE_BUILDABLE": "source"}
        assert func.max_instances == 100
        assert func.min_instances == 1
        assert func.vpc_connector is not None
        assert func.ingress_settings == "ALLOW_ALL"
        assert func.trigger == {"httpsTrigger": sample_function_response["httpsTrigger"]}
        assert func.labels == {"env": "test", "team": "backend"}
        assert func.type == "cloudfunctions.function"
        assert func.id == sample_function_response["name"]

    def test_from_api_response_event_trigger(self, sample_event_function_response):
        """Test creating a CloudFunction from an event-triggered API response."""
        func = CloudFunction.from_api_response(sample_event_function_response)

        assert func.name == "event-function"
        assert func.project == "test-project"
        assert func.location == "us-east1"
        assert func.runtime == "nodejs16"
        assert func.entry_point == "handleEvent"
        assert func.trigger == {
            "eventTrigger": sample_event_function_response["eventTrigger"]
        }

    def test_from_api_response_minimal(self):
        """Test creating a CloudFunction from a minimal API response."""
        response = {
            "name": "projects/p/locations/l/functions/f",
            "runtime": "python39",
            "entryPoint": "main",
            "status": "ACTIVE",
        }
        func = CloudFunction.from_api_response(response)

        assert func.name == "f"
        assert func.project == "p"
        assert func.location == "l"
        assert func.runtime == "python39"
        assert func.entry_point == "main"
        assert func.source_archive_url is None
        assert func.environment_variables is None
        assert func.trigger is None

    def test_get_tag_from_tags(self, sample_function_response):
        """Test get_tag returns value from _tags."""
        func = CloudFunction.from_api_response(sample_function_response)
        assert func.get_tag("env") == "test"
        assert func.get_tag("team") == "backend"

    def test_get_tag_from_labels(self, sample_function_response):
        """Test get_tag falls back to labels."""
        func = CloudFunction.from_api_response(sample_function_response)
        # _tags and labels are the same here, so it should still work
        assert func.get_tag("env") == "test"

    def test_get_tag_default(self, sample_function_response):
        """Test get_tag returns default for missing key."""
        func = CloudFunction.from_api_response(sample_function_response)
        assert func.get_tag("nonexistent") == ""
        assert func.get_tag("nonexistent", "fallback") == "fallback"

    def test_to_dict(self, sample_function_response):
        """Test converting a CloudFunction to a dictionary."""
        func = CloudFunction.from_api_response(sample_function_response)
        result = func.to_dict()

        assert result["name"] == "my-function"
        assert result["runtime"] == "python39"
        assert result["entry_point"] == "hello_world"
        assert "location" in result


class TestCloudFunctionsService:
    """Tests for the CloudFunctionsService."""

    def test_init(self, mock_google_client):
        """Test initializing the CloudFunctionsService."""
        from googleapiclient.discovery import build

        service = CloudFunctionsService(project_id="test-project")

        assert service.project_id == "test-project"
        build.assert_called_once_with(
            "cloudfunctions", "v1", credentials=None
        )

    def test_format_function_path(self, service):
        """Test formatting a function resource path."""
        path = service._format_function_path("us-central1", "my-function")
        assert path == "projects/test-project/locations/us-central1/functions/my-function"

    def test_format_location_path(self, service):
        """Test formatting a location path."""
        path = service._format_location_path("us-central1")
        assert path == "projects/test-project/locations/us-central1"

        path_all = service._format_location_path("-")
        assert path_all == "projects/test-project/locations/-"

    def test_list_functions(self, service, sample_function_response):
        """Test listing Cloud Functions."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.list.return_value = mock_request
        mock_request.execute.return_value = {
            "functions": [sample_function_response, sample_function_response]
        }
        mock_functions.list_next.return_value = None

        results = service.list_functions(location="us-central1")

        mock_functions.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )
        assert len(results) == 2
        assert isinstance(results[0], CloudFunction)
        assert results[0].name == "my-function"
        assert results[0].runtime == "python39"

    def test_list_functions_all_locations(self, service, sample_function_response):
        """Test listing Cloud Functions across all locations."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.list.return_value = mock_request
        mock_request.execute.return_value = {
            "functions": [sample_function_response]
        }
        mock_functions.list_next.return_value = None

        results = service.list_functions()

        mock_functions.list.assert_called_once_with(
            parent="projects/test-project/locations/-"
        )
        assert len(results) == 1

    def test_list_functions_empty(self, service):
        """Test listing Cloud Functions when none exist."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_functions.list_next.return_value = None

        results = service.list_functions()
        assert results == []

    def test_list_functions_pagination(self, service, sample_function_response):
        """Test listing Cloud Functions with pagination."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )

        # First page
        mock_request_1 = mock.MagicMock()
        mock_functions.list.return_value = mock_request_1
        mock_request_1.execute.return_value = {
            "functions": [sample_function_response]
        }

        # Second page
        mock_request_2 = mock.MagicMock()
        mock_request_2.execute.return_value = {
            "functions": [sample_function_response]
        }

        # list_next returns second page, then None
        mock_functions.list_next.side_effect = [mock_request_2, None]

        results = service.list_functions()
        assert len(results) == 2

    def test_get_function(self, service, sample_function_response):
        """Test getting a specific Cloud Function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.get.return_value = mock_request
        mock_request.execute.return_value = sample_function_response

        result = service.get_function("us-central1", "my-function")

        mock_functions.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/functions/my-function"
        )
        assert isinstance(result, CloudFunction)
        assert result.name == "my-function"
        assert result.runtime == "python39"

    def test_get_function_not_found(self, service):
        """Test getting a non-existent Cloud Function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not Found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_function("us-central1", "nonexistent")

    def test_get_function_api_error(self, service):
        """Test getting a function with an API error."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal Server Error"
        )

        with pytest.raises(APIError):
            service.get_function("us-central1", "my-function")

    def test_create_function(self, service, sample_function_response):
        """Test creating a Cloud Function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.create.return_value = mock_request
        mock_request.execute.return_value = sample_function_response

        result = service.create_function(
            location="us-central1",
            function_name="my-function",
            runtime="python39",
            entry_point="hello_world",
            source_archive_url="gs://my-bucket/source.zip",
            trigger={"httpsTrigger": {"securityLevel": "SECURE_ALWAYS"}},
            environment_variables={"ENV": "production"},
            timeout="60s",
            memory_mb=256,
            labels={"env": "test"},
        )

        mock_functions.create.assert_called_once()
        call_kwargs = mock_functions.create.call_args
        assert call_kwargs[1]["location"] == "projects/test-project/locations/us-central1"
        body = call_kwargs[1]["body"]
        assert body["runtime"] == "python39"
        assert body["entryPoint"] == "hello_world"
        assert body["sourceArchiveUrl"] == "gs://my-bucket/source.zip"
        assert body["httpsTrigger"] == {"securityLevel": "SECURE_ALWAYS"}
        assert body["environmentVariables"] == {"ENV": "production"}
        assert body["timeout"] == "60s"
        assert body["availableMemoryMb"] == 256

        assert isinstance(result, CloudFunction)
        assert result.name == "my-function"

    def test_create_function_default_https_trigger(self, service, sample_function_response):
        """Test creating a Cloud Function with default HTTPS trigger."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.create.return_value = mock_request
        mock_request.execute.return_value = sample_function_response

        service.create_function(
            location="us-central1",
            function_name="my-function",
            runtime="python39",
            entry_point="hello_world",
        )

        call_kwargs = mock_functions.create.call_args
        body = call_kwargs[1]["body"]
        assert "httpsTrigger" in body

    def test_create_function_conflict(self, service):
        """Test creating a function that already exists."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(APIError) as exc_info:
            service.create_function(
                location="us-central1",
                function_name="my-function",
                runtime="python39",
                entry_point="hello_world",
            )
        assert exc_info.value.status_code == 409

    def test_update_function(self, service, sample_function_response):
        """Test updating a Cloud Function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.patch.return_value = mock_request
        mock_request.execute.return_value = sample_function_response

        update_fields = {
            "runtime": "python311",
            "timeout": "120s",
            "availableMemoryMb": 512,
        }

        result = service.update_function(
            location="us-central1",
            function_name="my-function",
            update_fields=update_fields,
        )

        mock_functions.patch.assert_called_once()
        call_kwargs = mock_functions.patch.call_args
        assert call_kwargs[1]["name"] == (
            "projects/test-project/locations/us-central1/functions/my-function"
        )
        assert "runtime" in call_kwargs[1]["updateMask"]
        assert "timeout" in call_kwargs[1]["updateMask"]
        assert "availableMemoryMb" in call_kwargs[1]["updateMask"]

        assert isinstance(result, CloudFunction)

    def test_update_function_not_found(self, service):
        """Test updating a non-existent function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not Found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_function(
                location="us-central1",
                function_name="nonexistent",
                update_fields={"runtime": "python311"},
            )

    def test_delete_function(self, service):
        """Test deleting a Cloud Function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_function("us-central1", "my-function")

        mock_functions.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/functions/my-function"
        )
        assert result is True

    def test_delete_function_not_found(self, service):
        """Test deleting a non-existent function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not Found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_function("us-central1", "nonexistent")

    def test_call_function(self, service):
        """Test calling a Cloud Function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.call.return_value = mock_request
        mock_request.execute.return_value = {
            "executionId": "exec-123",
            "result": '{"message": "Hello World"}',
        }

        result = service.call_function(
            "us-central1", "my-function", data='{"name": "test"}'
        )

        mock_functions.call.assert_called_once_with(
            name="projects/test-project/locations/us-central1/functions/my-function",
            body={"data": '{"name": "test"}'},
        )
        assert result["executionId"] == "exec-123"
        assert result["result"] == '{"message": "Hello World"}'

    def test_call_function_no_data(self, service):
        """Test calling a Cloud Function without data."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.call.return_value = mock_request
        mock_request.execute.return_value = {
            "executionId": "exec-456",
            "result": "OK",
        }

        result = service.call_function("us-central1", "my-function")

        mock_functions.call.assert_called_once_with(
            name="projects/test-project/locations/us-central1/functions/my-function",
            body={},
        )
        assert result["executionId"] == "exec-456"

    def test_call_function_not_found(self, service):
        """Test calling a non-existent function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.call.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not Found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.call_function("us-central1", "nonexistent")

    def test_get_iam_policy(self, service):
        """Test getting the IAM policy for a Cloud Function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.getIamPolicy.return_value = mock_request
        mock_request.execute.return_value = {
            "version": 1,
            "bindings": [
                {
                    "role": "roles/cloudfunctions.invoker",
                    "members": ["allUsers"],
                }
            ],
        }

        result = service.get_iam_policy("us-central1", "my-function")

        mock_functions.getIamPolicy.assert_called_once_with(
            resource="projects/test-project/locations/us-central1/functions/my-function"
        )
        assert result["version"] == 1
        assert len(result["bindings"]) == 1
        assert result["bindings"][0]["role"] == "roles/cloudfunctions.invoker"

    def test_get_iam_policy_not_found(self, service):
        """Test getting IAM policy for a non-existent function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.getIamPolicy.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not Found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_iam_policy("us-central1", "nonexistent")

    def test_set_iam_policy(self, service):
        """Test setting the IAM policy for a Cloud Function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.setIamPolicy.return_value = mock_request

        policy = {
            "version": 1,
            "bindings": [
                {
                    "role": "roles/cloudfunctions.invoker",
                    "members": ["user:test@example.com"],
                }
            ],
        }
        mock_request.execute.return_value = policy

        result = service.set_iam_policy("us-central1", "my-function", policy)

        mock_functions.setIamPolicy.assert_called_once_with(
            resource="projects/test-project/locations/us-central1/functions/my-function",
            body={"policy": policy},
        )
        assert result["version"] == 1
        assert result["bindings"][0]["members"] == ["user:test@example.com"]

    def test_set_iam_policy_not_found(self, service):
        """Test setting IAM policy for a non-existent function."""
        mock_functions = (
            service.service.projects.return_value
            .locations.return_value
            .functions.return_value
        )
        mock_request = mock.MagicMock()
        mock_functions.setIamPolicy.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not Found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.set_iam_policy("us-central1", "nonexistent", {"version": 1})
