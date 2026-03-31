"""Tests for Cloud Run service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.cloud_run import CloudRunServiceManager
from gcpoto.models.cloud_run import CloudRunService, CloudRunRevision


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().locations().services() chain
        mock_services = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.services.return_value = (
            mock_services
        )

        # Set up projects().locations().services().revisions() chain
        mock_revisions = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.services.return_value.revisions.return_value = (
            mock_revisions
        )

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a CloudRunServiceManager with mocked client."""
    return CloudRunServiceManager(project_id="test-project")


@pytest.fixture
def sample_service_response():
    """Sample Cloud Run service API response."""
    return {
        "name": "projects/test-project/locations/us-central1/services/my-service",
        "description": "A test service",
        "uri": "https://my-service-abc123-uc.a.run.app",
        "ingress": "INGRESS_TRAFFIC_ALL",
        "launchStage": "GA",
        "template": {
            "containers": [
                {
                    "image": "gcr.io/test-project/my-image:latest",
                    "ports": [{"containerPort": 8080}],
                    "resources": {
                        "limits": {"memory": "512Mi", "cpu": "1"},
                    },
                    "env": [
                        {"name": "ENV_VAR", "value": "test-value"},
                    ],
                }
            ],
            "scaling": {
                "minInstanceCount": 0,
                "maxInstanceCount": 10,
            },
            "serviceAccount": "my-sa@test-project.iam.gserviceaccount.com",
        },
        "traffic": [
            {"type": "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST", "percent": 100},
        ],
        "conditions": [
            {
                "type": "Ready",
                "state": "CONDITION_SUCCEEDED",
                "lastTransitionTime": "2024-01-15T10:30:00Z",
            },
        ],
        "latestReadyRevision": "projects/test-project/locations/us-central1/services/my-service/revisions/my-service-00001-abc",
        "latestCreatedRevision": "projects/test-project/locations/us-central1/services/my-service/revisions/my-service-00001-abc",
        "labels": {"env": "test", "team": "platform"},
        "createTime": "2024-01-15T10:00:00Z",
        "updateTime": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def sample_revision_response():
    """Sample Cloud Run revision API response."""
    return {
        "name": "projects/test-project/locations/us-central1/services/my-service/revisions/my-service-00001-abc",
        "generation": 1,
        "containers": [
            {
                "image": "gcr.io/test-project/my-image:latest",
                "ports": [{"containerPort": 8080}],
                "resources": {
                    "limits": {"memory": "512Mi", "cpu": "1"},
                },
            }
        ],
        "scaling": {
            "minInstanceCount": 0,
            "maxInstanceCount": 10,
        },
        "serviceAccount": "my-sa@test-project.iam.gserviceaccount.com",
        "conditions": [
            {
                "type": "Ready",
                "state": "CONDITION_SUCCEEDED",
                "lastTransitionTime": "2024-01-15T10:30:00Z",
            },
        ],
        "labels": {"env": "test"},
        "createTime": "2024-01-15T10:00:00Z",
        "updateTime": "2024-01-15T10:30:00Z",
    }


class TestCloudRunServiceModel:
    """Tests for CloudRunService model."""

    def test_from_api_response(self, sample_service_response):
        """Test creating a CloudRunService from an API response."""
        svc = CloudRunService.from_api_response(sample_service_response)

        assert svc.name == "my-service"
        assert svc.project == "test-project"
        assert svc.location == "us-central1"
        assert svc.type == "run.service"
        assert svc.description == "A test service"
        assert svc.uri == "https://my-service-abc123-uc.a.run.app"
        assert svc.ingress == "INGRESS_TRAFFIC_ALL"
        assert svc.launch_stage == "GA"
        assert svc.template is not None
        assert svc.traffic is not None
        assert len(svc.traffic) == 1
        assert svc.conditions is not None
        assert svc.latest_ready_revision is not None
        assert svc.latest_created_revision is not None
        assert svc.labels == {"env": "test", "team": "platform"}

    def test_from_api_response_with_project_id(self, sample_service_response):
        """Test creating a CloudRunService with explicit project_id."""
        svc = CloudRunService.from_api_response(
            sample_service_response, project_id="override-project"
        )
        assert svc.project == "override-project"

    def test_from_api_response_minimal(self):
        """Test creating a CloudRunService from a minimal response."""
        response = {"name": "projects/p/locations/us-east1/services/svc"}
        svc = CloudRunService.from_api_response(response)

        assert svc.name == "svc"
        assert svc.project == "p"
        assert svc.location == "us-east1"
        assert svc.description is None
        assert svc.uri is None
        assert svc.template is None
        assert svc.traffic is None

    def test_from_api_response_empty(self):
        """Test creating a CloudRunService from an empty response."""
        svc = CloudRunService.from_api_response({})
        assert svc.name == ""
        assert svc.project == ""
        assert svc.location == ""

    def test_get_tag(self, sample_service_response):
        """Test get_tag method."""
        svc = CloudRunService.from_api_response(sample_service_response)

        assert svc.get_tag("env") == "test"
        assert svc.get_tag("team") == "platform"
        assert svc.get_tag("nonexistent") == ""
        assert svc.get_tag("nonexistent", "default") == "default"

    def test_to_dict(self, sample_service_response):
        """Test to_dict method."""
        svc = CloudRunService.from_api_response(sample_service_response)
        d = svc.to_dict()

        assert d["name"] == "my-service"
        assert d["location"] == "us-central1"
        assert "description" in d


class TestCloudRunRevisionModel:
    """Tests for CloudRunRevision model."""

    def test_from_api_response(self, sample_revision_response):
        """Test creating a CloudRunRevision from an API response."""
        rev = CloudRunRevision.from_api_response(sample_revision_response)

        assert rev.name == "my-service-00001-abc"
        assert rev.project == "test-project"
        assert rev.location == "us-central1"
        assert rev.service_name == "my-service"
        assert rev.type == "run.revision"
        assert rev.generation == 1
        assert rev.containers is not None
        assert len(rev.containers) == 1
        assert rev.scaling == {"minInstanceCount": 0, "maxInstanceCount": 10}
        assert rev.service_account == "my-sa@test-project.iam.gserviceaccount.com"
        assert rev.conditions is not None

    def test_from_api_response_minimal(self):
        """Test creating a CloudRunRevision from a minimal response."""
        response = {
            "name": "projects/p/locations/us-east1/services/svc/revisions/rev-001"
        }
        rev = CloudRunRevision.from_api_response(response)

        assert rev.name == "rev-001"
        assert rev.project == "p"
        assert rev.location == "us-east1"
        assert rev.service_name == "svc"
        assert rev.generation is None
        assert rev.containers is None

    def test_get_tag(self, sample_revision_response):
        """Test get_tag method on revision."""
        rev = CloudRunRevision.from_api_response(sample_revision_response)

        assert rev.get_tag("env") == "test"
        assert rev.get_tag("missing") == ""
        assert rev.get_tag("missing", "fallback") == "fallback"


class TestCloudRunServiceManager:
    """Tests for CloudRunServiceManager service class."""

    def test_init(self, mock_google_client):
        """Test initializing the CloudRunServiceManager."""
        from googleapiclient.discovery import build

        svc = CloudRunServiceManager(project_id="test-project")

        assert svc.project_id == "test-project"
        build.assert_called_once_with("run", "v2", credentials=None)

    def test_list_services(self, service, mock_google_client, sample_service_response):
        """Test listing Cloud Run services."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request = mock.MagicMock()
        mock_services.list.return_value = mock_request
        mock_request.execute.return_value = {
            "services": [sample_service_response, sample_service_response],
        }
        mock_services.list_next.return_value = None

        results = service.list_services(location="us-central1")

        mock_services.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1"
        )
        assert len(results) == 2
        assert isinstance(results[0], CloudRunService)
        assert results[0].name == "my-service"

    def test_list_services_default_location(self, service, mock_google_client, sample_service_response):
        """Test listing Cloud Run services with default all-location."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request = mock.MagicMock()
        mock_services.list.return_value = mock_request
        mock_request.execute.return_value = {"services": [sample_service_response]}
        mock_services.list_next.return_value = None

        results = service.list_services()

        mock_services.list.assert_called_once_with(
            parent="projects/test-project/locations/-"
        )
        assert len(results) == 1

    def test_list_services_pagination(self, service, mock_google_client, sample_service_response):
        """Test listing Cloud Run services with pagination."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()
        mock_services.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "services": [sample_service_response],
        }
        mock_request_page2.execute.return_value = {
            "services": [sample_service_response],
        }
        mock_services.list_next.side_effect = [mock_request_page2, None]

        results = service.list_services(location="us-central1")

        assert len(results) == 2

    def test_list_services_empty(self, service, mock_google_client):
        """Test listing Cloud Run services with no results."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request = mock.MagicMock()
        mock_services.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_services.list_next.return_value = None

        results = service.list_services()

        assert results == []

    def test_get_service(self, service, mock_google_client, sample_service_response):
        """Test getting a specific Cloud Run service."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request = mock.MagicMock()
        mock_services.get.return_value = mock_request
        mock_request.execute.return_value = sample_service_response

        result = service.get_service("us-central1", "my-service")

        mock_services.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/services/my-service"
        )
        assert isinstance(result, CloudRunService)
        assert result.name == "my-service"
        assert result.location == "us-central1"

    def test_get_service_full_path(self, service, mock_google_client, sample_service_response):
        """Test getting a service using a full resource path."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request = mock.MagicMock()
        mock_services.get.return_value = mock_request
        mock_request.execute.return_value = sample_service_response

        full_path = "projects/test-project/locations/us-central1/services/my-service"
        result = service.get_service("us-central1", full_path)

        mock_services.get.assert_called_once_with(name=full_path)
        assert result.name == "my-service"

    def test_create_service(self, service, mock_google_client, sample_service_response):
        """Test creating a Cloud Run service."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request = mock.MagicMock()
        mock_services.create.return_value = mock_request
        mock_request.execute.return_value = sample_service_response

        result = service.create_service(
            location="us-central1",
            service_name="my-service",
            image="gcr.io/test-project/my-image:latest",
            port=8080,
            env_vars={"ENV_VAR": "test-value"},
            memory="512Mi",
            cpu="1",
            max_instances=10,
            min_instances=0,
            labels={"env": "test"},
        )

        mock_services.create.assert_called_once()
        call_kwargs = mock_services.create.call_args
        assert call_kwargs[1]["parent"] == "projects/test-project/locations/us-central1"
        assert call_kwargs[1]["serviceId"] == "my-service"

        body = call_kwargs[1]["body"]
        assert body["labels"] == {"env": "test"}
        assert body["template"]["containers"][0]["image"] == "gcr.io/test-project/my-image:latest"
        assert body["template"]["containers"][0]["ports"] == [{"containerPort": 8080}]
        assert body["template"]["containers"][0]["resources"]["limits"]["memory"] == "512Mi"
        assert body["template"]["containers"][0]["resources"]["limits"]["cpu"] == "1"
        assert body["template"]["containers"][0]["env"] == [
            {"name": "ENV_VAR", "value": "test-value"}
        ]
        assert body["template"]["scaling"]["maxInstanceCount"] == 10
        assert body["template"]["scaling"]["minInstanceCount"] == 0

        assert isinstance(result, CloudRunService)
        assert result.name == "my-service"

    def test_create_service_minimal(self, service, mock_google_client, sample_service_response):
        """Test creating a Cloud Run service with minimal parameters."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request = mock.MagicMock()
        mock_services.create.return_value = mock_request
        mock_request.execute.return_value = sample_service_response

        result = service.create_service(
            location="us-central1",
            service_name="my-service",
            image="gcr.io/test-project/my-image:latest",
        )

        call_kwargs = mock_services.create.call_args[1]
        body = call_kwargs["body"]
        assert "labels" not in body
        assert "scaling" not in body["template"]
        assert "env" not in body["template"]["containers"][0]
        assert isinstance(result, CloudRunService)

    def test_update_service(self, service, mock_google_client, sample_service_response):
        """Test updating a Cloud Run service."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request = mock.MagicMock()
        mock_services.patch.return_value = mock_request
        mock_request.execute.return_value = sample_service_response

        update_fields = {
            "template": {
                "containers": [
                    {"image": "gcr.io/test-project/my-image:v2"}
                ],
            },
        }
        result = service.update_service("us-central1", "my-service", update_fields)

        mock_services.patch.assert_called_once_with(
            name="projects/test-project/locations/us-central1/services/my-service",
            body=update_fields,
        )
        assert isinstance(result, CloudRunService)
        assert result.name == "my-service"

    def test_delete_service(self, service, mock_google_client):
        """Test deleting a Cloud Run service."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request = mock.MagicMock()
        mock_services.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_service("us-central1", "my-service")

        mock_services.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/services/my-service"
        )
        assert result is True

    def test_list_revisions(self, service, mock_google_client, sample_revision_response):
        """Test listing revisions for a Cloud Run service."""
        mock_revisions = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
            .revisions.return_value
        )
        mock_request = mock.MagicMock()
        mock_revisions.list.return_value = mock_request
        mock_request.execute.return_value = {
            "revisions": [sample_revision_response],
        }
        mock_revisions.list_next.return_value = None

        results = service.list_revisions("us-central1", "my-service")

        mock_revisions.list.assert_called_once_with(
            parent="projects/test-project/locations/us-central1/services/my-service"
        )
        assert len(results) == 1
        assert isinstance(results[0], CloudRunRevision)
        assert results[0].name == "my-service-00001-abc"
        assert results[0].service_name == "my-service"

    def test_list_revisions_empty(self, service, mock_google_client):
        """Test listing revisions with no results."""
        mock_revisions = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
            .revisions.return_value
        )
        mock_request = mock.MagicMock()
        mock_revisions.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_revisions.list_next.return_value = None

        results = service.list_revisions("us-central1", "my-service")
        assert results == []

    def test_get_revision(self, service, mock_google_client, sample_revision_response):
        """Test getting a specific Cloud Run revision."""
        mock_revisions = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
            .revisions.return_value
        )
        mock_request = mock.MagicMock()
        mock_revisions.get.return_value = mock_request
        mock_request.execute.return_value = sample_revision_response

        result = service.get_revision("us-central1", "my-service-00001-abc")

        mock_revisions.get.assert_called_once_with(
            name="projects/test-project/locations/us-central1/revisions/my-service-00001-abc"
        )
        assert isinstance(result, CloudRunRevision)
        assert result.name == "my-service-00001-abc"

    def test_delete_revision(self, service, mock_google_client):
        """Test deleting a Cloud Run revision."""
        mock_revisions = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
            .revisions.return_value
        )
        mock_request = mock.MagicMock()
        mock_revisions.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_revision("us-central1", "my-service-00001-abc")

        mock_revisions.delete.assert_called_once_with(
            name="projects/test-project/locations/us-central1/revisions/my-service-00001-abc"
        )
        assert result is True

    def test_get_iam_policy(self, service, mock_google_client):
        """Test getting the IAM policy for a Cloud Run service."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request = mock.MagicMock()
        mock_services.getIamPolicy.return_value = mock_request
        expected_policy = {
            "version": 3,
            "bindings": [
                {
                    "role": "roles/run.invoker",
                    "members": ["allUsers"],
                }
            ],
        }
        mock_request.execute.return_value = expected_policy

        result = service.get_iam_policy("us-central1", "my-service")

        mock_services.getIamPolicy.assert_called_once_with(
            resource="projects/test-project/locations/us-central1/services/my-service"
        )
        assert result == expected_policy
        assert result["bindings"][0]["role"] == "roles/run.invoker"

    def test_set_iam_policy(self, service, mock_google_client):
        """Test setting the IAM policy for a Cloud Run service."""
        mock_services = (
            mock_google_client.projects.return_value
            .locations.return_value
            .services.return_value
        )
        mock_request = mock.MagicMock()
        mock_services.setIamPolicy.return_value = mock_request

        policy = {
            "version": 3,
            "bindings": [
                {
                    "role": "roles/run.invoker",
                    "members": ["user:test@example.com"],
                }
            ],
        }
        mock_request.execute.return_value = policy

        result = service.set_iam_policy("us-central1", "my-service", policy)

        mock_services.setIamPolicy.assert_called_once_with(
            resource="projects/test-project/locations/us-central1/services/my-service",
            body={"policy": policy},
        )
        assert result == policy

    def test_format_parent(self, service):
        """Test _format_parent helper."""
        assert (
            service._format_parent("us-central1")
            == "projects/test-project/locations/us-central1"
        )
        assert (
            service._format_parent("-")
            == "projects/test-project/locations/-"
        )

    def test_format_service_name_short(self, service):
        """Test _format_service_name with a short name."""
        result = service._format_service_name("us-central1", "my-service")
        assert result == "projects/test-project/locations/us-central1/services/my-service"

    def test_format_service_name_full_path(self, service):
        """Test _format_service_name with a full resource path."""
        full_path = "projects/test-project/locations/us-central1/services/my-service"
        result = service._format_service_name("us-central1", full_path)
        assert result == full_path

    def test_format_revision_name_short(self, service):
        """Test _format_revision_name with a short name."""
        result = service._format_revision_name("us-central1", "my-rev-001")
        assert result == "projects/test-project/locations/us-central1/revisions/my-rev-001"

    def test_format_revision_name_full_path(self, service):
        """Test _format_revision_name with a full resource path."""
        full_path = "projects/test-project/locations/us-central1/revisions/my-rev-001"
        result = service._format_revision_name("us-central1", full_path)
        assert result == full_path
