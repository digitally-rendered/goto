"""Tests for Vertex AI service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.vertex_ai import VertexAIService
from gcpoto.models.vertex_ai import (
    VertexDataset,
    VertexModel,
    VertexEndpoint,
    TrainingPipeline,
)
from gcpoto.exceptions import ResourceNotFoundError, APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects

        mock_locations = mock.MagicMock()
        mock_projects.locations.return_value = mock_locations

        mock_datasets = mock.MagicMock()
        mock_locations.datasets.return_value = mock_datasets

        mock_models = mock.MagicMock()
        mock_locations.models.return_value = mock_models

        mock_endpoints = mock.MagicMock()
        mock_locations.endpoints.return_value = mock_endpoints

        mock_training_pipelines = mock.MagicMock()
        mock_locations.trainingPipelines.return_value = mock_training_pipelines

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a VertexAIService with mocked client."""
    return VertexAIService(project_id="test-project")


@pytest.fixture
def sample_dataset_response():
    """Sample Vertex AI dataset API response."""
    return {
        "name": "projects/test-project/locations/us-central1/datasets/123",
        "displayName": "test-dataset",
        "metadataSchemaUri": "gs://google-cloud-aiplatform/schema/dataset/metadata/tabular_1.0.0.yaml",
        "metadata": {"inputConfig": {"gcsSource": {"uri": ["gs://bucket/data.csv"]}}},
        "dataItemCount": 1000,
        "labels": {"env": "test", "team": "ml"},
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-01-02T00:00:00Z",
    }


@pytest.fixture
def sample_model_response():
    """Sample Vertex AI model API response."""
    return {
        "name": "projects/test-project/locations/us-central1/models/456",
        "displayName": "test-model",
        "description": "A test model",
        "versionId": "1",
        "artifactUri": "gs://bucket/model/",
        "containerSpec": {
            "imageUri": "gcr.io/test-project/model:latest",
            "predictRoute": "/predict",
            "healthRoute": "/health",
        },
        "deployedModels": [
            {
                "endpoint": "projects/test-project/locations/us-central1/endpoints/789",
                "deployedModelId": "dm-001",
            }
        ],
        "labels": {"env": "test"},
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-01-02T00:00:00Z",
    }


@pytest.fixture
def sample_endpoint_response():
    """Sample Vertex AI endpoint API response."""
    return {
        "name": "projects/test-project/locations/us-central1/endpoints/789",
        "displayName": "test-endpoint",
        "description": "A test endpoint",
        "deployedModels": [
            {
                "id": "dm-001",
                "model": "projects/test-project/locations/us-central1/models/456",
                "displayName": "deployed-test-model",
                "dedicatedResources": {
                    "machineSpec": {"machineType": "n1-standard-2"},
                    "minReplicaCount": 1,
                    "maxReplicaCount": 2,
                },
            }
        ],
        "trafficSplit": {"dm-001": 100},
        "labels": {"env": "test"},
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-01-02T00:00:00Z",
    }


@pytest.fixture
def sample_training_pipeline_response():
    """Sample Vertex AI training pipeline API response."""
    return {
        "name": "projects/test-project/locations/us-central1/trainingPipelines/999",
        "displayName": "test-pipeline",
        "state": "PIPELINE_STATE_SUCCEEDED",
        "trainingTaskDefinition": "gs://google-cloud-aiplatform/schema/trainingjob/definition/automl_tabular_1.0.0.yaml",
        "trainingTaskInputs": {"targetColumn": "label"},
        "modelToUpload": {"displayName": "trained-model"},
        "startTime": "2025-01-01T00:00:00Z",
        "endTime": "2025-01-01T02:00:00Z",
        "labels": {"env": "test"},
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-01-01T02:00:00Z",
    }


def _make_http_error(status_code, reason="error"):
    """Create a mock HttpError with the given status code."""
    resp = mock.MagicMock()
    resp.status = status_code
    return HttpError(resp, b'{"error": {"message": "' + reason.encode() + b'"}}')


# ---- Dataset Model Tests ----


class TestVertexDatasetModel:
    def test_from_api_response(self, sample_dataset_response):
        dataset = VertexDataset.from_api_response(sample_dataset_response)
        assert dataset.id == "123"
        assert dataset.display_name == "test-dataset"
        assert dataset.location == "us-central1"
        assert dataset.project == "test-project"
        assert dataset.type == "vertex_ai.dataset"
        assert dataset.metadata_schema_uri is not None
        assert dataset.data_item_count == 1000

    def test_from_api_response_minimal(self):
        response = {
            "name": "projects/p/locations/loc/datasets/1",
            "displayName": "minimal",
        }
        dataset = VertexDataset.from_api_response(response)
        assert dataset.id == "1"
        assert dataset.display_name == "minimal"
        assert dataset.metadata is None
        assert dataset.data_item_count is None

    def test_get_tag(self, sample_dataset_response):
        dataset = VertexDataset.from_api_response(sample_dataset_response)
        assert dataset.get_tag("env") == "test"
        assert dataset.get_tag("team") == "ml"
        assert dataset.get_tag("missing", "default") == "default"


# ---- Model Model Tests ----


class TestVertexModelModel:
    def test_from_api_response(self, sample_model_response):
        model = VertexModel.from_api_response(sample_model_response)
        assert model.id == "456"
        assert model.display_name == "test-model"
        assert model.description == "A test model"
        assert model.location == "us-central1"
        assert model.version_id == "1"
        assert model.artifact_uri == "gs://bucket/model/"
        assert model.container_spec is not None
        assert model.deployed_models is not None
        assert len(model.deployed_models) == 1

    def test_get_tag(self, sample_model_response):
        model = VertexModel.from_api_response(sample_model_response)
        assert model.get_tag("env") == "test"
        assert model.get_tag("missing", "default") == "default"


# ---- Endpoint Model Tests ----


class TestVertexEndpointModel:
    def test_from_api_response(self, sample_endpoint_response):
        endpoint = VertexEndpoint.from_api_response(sample_endpoint_response)
        assert endpoint.id == "789"
        assert endpoint.display_name == "test-endpoint"
        assert endpoint.description == "A test endpoint"
        assert endpoint.location == "us-central1"
        assert endpoint.deployed_models is not None
        assert len(endpoint.deployed_models) == 1
        assert endpoint.traffic_split == {"dm-001": 100}

    def test_get_tag(self, sample_endpoint_response):
        endpoint = VertexEndpoint.from_api_response(sample_endpoint_response)
        assert endpoint.get_tag("env") == "test"
        assert endpoint.get_tag("missing", "default") == "default"


# ---- Training Pipeline Model Tests ----


class TestTrainingPipelineModel:
    def test_from_api_response(self, sample_training_pipeline_response):
        pipeline = TrainingPipeline.from_api_response(
            sample_training_pipeline_response
        )
        assert pipeline.id == "999"
        assert pipeline.display_name == "test-pipeline"
        assert pipeline.state == "PIPELINE_STATE_SUCCEEDED"
        assert pipeline.location == "us-central1"
        assert pipeline.training_task_definition is not None
        assert pipeline.training_task_inputs == {"targetColumn": "label"}
        assert pipeline.model_to_upload == {"displayName": "trained-model"}


# ---- Dataset Service Tests ----


class TestVertexAIServiceDatasets:
    def test_list_datasets(self, service, sample_dataset_response):
        mock_datasets = (
            service.service.projects()
            .locations()
            .datasets()
        )
        mock_datasets.list().execute.return_value = {
            "datasets": [sample_dataset_response]
        }
        mock_datasets.list_next.return_value = None

        results = service.list_datasets("us-central1")
        assert len(results) == 1
        assert results[0].display_name == "test-dataset"
        assert isinstance(results[0], VertexDataset)

    def test_list_datasets_empty(self, service):
        mock_datasets = (
            service.service.projects()
            .locations()
            .datasets()
        )
        mock_datasets.list().execute.return_value = {}
        mock_datasets.list_next.return_value = None

        results = service.list_datasets("us-central1")
        assert len(results) == 0

    def test_list_datasets_pagination(self, service, sample_dataset_response):
        mock_datasets = (
            service.service.projects()
            .locations()
            .datasets()
        )
        second_response = sample_dataset_response.copy()
        second_response["name"] = (
            "projects/test-project/locations/us-central1/datasets/124"
        )
        second_response["displayName"] = "test-dataset-2"

        mock_datasets.list().execute.return_value = {
            "datasets": [sample_dataset_response]
        }
        # Simulate pagination: first call returns a request, second returns None
        next_request = mock.MagicMock()
        next_request.execute.return_value = {
            "datasets": [second_response]
        }
        mock_datasets.list_next.side_effect = [next_request, None]

        results = service.list_datasets("us-central1")
        assert len(results) == 2
        assert results[0].display_name == "test-dataset"
        assert results[1].display_name == "test-dataset-2"

    def test_get_dataset(self, service, sample_dataset_response):
        mock_datasets = (
            service.service.projects()
            .locations()
            .datasets()
        )
        mock_datasets.get().execute.return_value = sample_dataset_response

        result = service.get_dataset("us-central1", "123")
        assert result.display_name == "test-dataset"
        assert result.id == "123"

    def test_get_dataset_not_found(self, service):
        mock_datasets = (
            service.service.projects()
            .locations()
            .datasets()
        )
        mock_datasets.get().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.get_dataset("us-central1", "nonexistent")

    def test_get_dataset_api_error(self, service):
        mock_datasets = (
            service.service.projects()
            .locations()
            .datasets()
        )
        mock_datasets.get().execute.side_effect = _make_http_error(500)

        with pytest.raises(APIError):
            service.get_dataset("us-central1", "123")

    def test_create_dataset(self, service, sample_dataset_response):
        mock_datasets = (
            service.service.projects()
            .locations()
            .datasets()
        )
        mock_datasets.create().execute.return_value = sample_dataset_response

        result = service.create_dataset(
            location="us-central1",
            display_name="test-dataset",
            metadata_schema_uri="gs://schema/uri.yaml",
            metadata={"key": "value"},
            labels={"env": "test"},
        )
        assert result.display_name == "test-dataset"
        assert isinstance(result, VertexDataset)

    def test_create_dataset_minimal(self, service, sample_dataset_response):
        mock_datasets = (
            service.service.projects()
            .locations()
            .datasets()
        )
        mock_datasets.create().execute.return_value = sample_dataset_response

        result = service.create_dataset(
            location="us-central1",
            display_name="test-dataset",
            metadata_schema_uri="gs://schema/uri.yaml",
        )
        assert result.display_name == "test-dataset"

    def test_create_dataset_api_error(self, service):
        mock_datasets = (
            service.service.projects()
            .locations()
            .datasets()
        )
        mock_datasets.create().execute.side_effect = _make_http_error(400)

        with pytest.raises(APIError):
            service.create_dataset(
                location="us-central1",
                display_name="bad",
                metadata_schema_uri="gs://schema/uri.yaml",
            )

    def test_delete_dataset(self, service):
        mock_datasets = (
            service.service.projects()
            .locations()
            .datasets()
        )
        mock_datasets.delete().execute.return_value = {}

        assert service.delete_dataset("us-central1", "123") is True

    def test_delete_dataset_not_found(self, service):
        mock_datasets = (
            service.service.projects()
            .locations()
            .datasets()
        )
        mock_datasets.delete().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.delete_dataset("us-central1", "nonexistent")


# ---- Model Service Tests ----


class TestVertexAIServiceModels:
    def test_list_models(self, service, sample_model_response):
        mock_models = (
            service.service.projects()
            .locations()
            .models()
        )
        mock_models.list().execute.return_value = {
            "models": [sample_model_response]
        }
        mock_models.list_next.return_value = None

        results = service.list_models("us-central1")
        assert len(results) == 1
        assert results[0].display_name == "test-model"
        assert isinstance(results[0], VertexModel)

    def test_list_models_empty(self, service):
        mock_models = (
            service.service.projects()
            .locations()
            .models()
        )
        mock_models.list().execute.return_value = {}
        mock_models.list_next.return_value = None

        results = service.list_models("us-central1")
        assert len(results) == 0

    def test_get_model(self, service, sample_model_response):
        mock_models = (
            service.service.projects()
            .locations()
            .models()
        )
        mock_models.get().execute.return_value = sample_model_response

        result = service.get_model("us-central1", "456")
        assert result.display_name == "test-model"
        assert result.id == "456"

    def test_get_model_not_found(self, service):
        mock_models = (
            service.service.projects()
            .locations()
            .models()
        )
        mock_models.get().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.get_model("us-central1", "nonexistent")

    def test_upload_model(self, service, sample_model_response):
        mock_models = (
            service.service.projects()
            .locations()
            .models()
        )
        mock_models.upload().execute.return_value = sample_model_response

        result = service.upload_model(
            location="us-central1",
            display_name="test-model",
            artifact_uri="gs://bucket/model/",
            container_spec={"imageUri": "gcr.io/test/model:latest"},
            description="A test model",
            labels={"env": "test"},
        )
        assert result.display_name == "test-model"
        assert isinstance(result, VertexModel)

    def test_upload_model_minimal(self, service, sample_model_response):
        mock_models = (
            service.service.projects()
            .locations()
            .models()
        )
        mock_models.upload().execute.return_value = sample_model_response

        result = service.upload_model(
            location="us-central1",
            display_name="test-model",
        )
        assert result.display_name == "test-model"

    def test_upload_model_api_error(self, service):
        mock_models = (
            service.service.projects()
            .locations()
            .models()
        )
        mock_models.upload().execute.side_effect = _make_http_error(400)

        with pytest.raises(APIError):
            service.upload_model(
                location="us-central1",
                display_name="bad-model",
            )

    def test_delete_model(self, service):
        mock_models = (
            service.service.projects()
            .locations()
            .models()
        )
        mock_models.delete().execute.return_value = {}

        assert service.delete_model("us-central1", "456") is True

    def test_delete_model_not_found(self, service):
        mock_models = (
            service.service.projects()
            .locations()
            .models()
        )
        mock_models.delete().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.delete_model("us-central1", "nonexistent")


# ---- Endpoint Service Tests ----


class TestVertexAIServiceEndpoints:
    def test_list_endpoints(self, service, sample_endpoint_response):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.list().execute.return_value = {
            "endpoints": [sample_endpoint_response]
        }
        mock_endpoints.list_next.return_value = None

        results = service.list_endpoints("us-central1")
        assert len(results) == 1
        assert results[0].display_name == "test-endpoint"
        assert isinstance(results[0], VertexEndpoint)

    def test_list_endpoints_empty(self, service):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.list().execute.return_value = {}
        mock_endpoints.list_next.return_value = None

        results = service.list_endpoints("us-central1")
        assert len(results) == 0

    def test_get_endpoint(self, service, sample_endpoint_response):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.get().execute.return_value = sample_endpoint_response

        result = service.get_endpoint("us-central1", "789")
        assert result.display_name == "test-endpoint"
        assert result.id == "789"

    def test_get_endpoint_not_found(self, service):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.get().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.get_endpoint("us-central1", "nonexistent")

    def test_create_endpoint(self, service, sample_endpoint_response):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.create().execute.return_value = sample_endpoint_response

        result = service.create_endpoint(
            location="us-central1",
            display_name="test-endpoint",
            description="A test endpoint",
            labels={"env": "test"},
        )
        assert result.display_name == "test-endpoint"
        assert isinstance(result, VertexEndpoint)

    def test_create_endpoint_minimal(self, service, sample_endpoint_response):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.create().execute.return_value = sample_endpoint_response

        result = service.create_endpoint(
            location="us-central1",
            display_name="test-endpoint",
        )
        assert result.display_name == "test-endpoint"

    def test_create_endpoint_api_error(self, service):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.create().execute.side_effect = _make_http_error(400)

        with pytest.raises(APIError):
            service.create_endpoint(
                location="us-central1",
                display_name="bad",
            )

    def test_delete_endpoint(self, service):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.delete().execute.return_value = {}

        assert service.delete_endpoint("us-central1", "789") is True

    def test_delete_endpoint_not_found(self, service):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.delete().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.delete_endpoint("us-central1", "nonexistent")

    def test_deploy_model(self, service, sample_endpoint_response):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.deployModel().execute.return_value = (
            sample_endpoint_response
        )

        result = service.deploy_model(
            location="us-central1",
            endpoint_id="789",
            model_id="456",
            display_name="deployed-test-model",
            machine_type="n1-standard-4",
            min_replica_count=1,
            max_replica_count=3,
        )
        assert isinstance(result, VertexEndpoint)

    def test_deploy_model_default_params(self, service, sample_endpoint_response):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.deployModel().execute.return_value = (
            sample_endpoint_response
        )

        result = service.deploy_model(
            location="us-central1",
            endpoint_id="789",
            model_id="456",
            display_name="deployed-test-model",
        )
        assert isinstance(result, VertexEndpoint)

    def test_deploy_model_not_found(self, service):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.deployModel().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.deploy_model(
                location="us-central1",
                endpoint_id="nonexistent",
                model_id="456",
                display_name="deployed-model",
            )

    def test_undeploy_model(self, service, sample_endpoint_response):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.undeployModel().execute.return_value = (
            sample_endpoint_response
        )

        result = service.undeploy_model(
            location="us-central1",
            endpoint_id="789",
            deployed_model_id="dm-001",
        )
        assert isinstance(result, VertexEndpoint)

    def test_undeploy_model_not_found(self, service):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.undeployModel().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.undeploy_model(
                location="us-central1",
                endpoint_id="nonexistent",
                deployed_model_id="dm-001",
            )

    def test_predict(self, service):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.predict().execute.return_value = {
            "predictions": [{"output": 0.95}],
            "deployedModelId": "dm-001",
        }

        result = service.predict(
            location="us-central1",
            endpoint_id="789",
            instances=[{"feature1": 1.0, "feature2": 2.0}],
            parameters={"confidenceThreshold": 0.5},
        )
        assert "predictions" in result
        assert result["predictions"][0]["output"] == 0.95

    def test_predict_without_parameters(self, service):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.predict().execute.return_value = {
            "predictions": [{"output": 0.8}],
        }

        result = service.predict(
            location="us-central1",
            endpoint_id="789",
            instances=[{"feature1": 1.0}],
        )
        assert "predictions" in result

    def test_predict_not_found(self, service):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.predict().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.predict(
                location="us-central1",
                endpoint_id="nonexistent",
                instances=[{"feature1": 1.0}],
            )

    def test_predict_api_error(self, service):
        mock_endpoints = (
            service.service.projects()
            .locations()
            .endpoints()
        )
        mock_endpoints.predict().execute.side_effect = _make_http_error(500)

        with pytest.raises(APIError):
            service.predict(
                location="us-central1",
                endpoint_id="789",
                instances=[{"feature1": 1.0}],
            )


# ---- Training Pipeline Service Tests ----


class TestVertexAIServiceTrainingPipelines:
    def test_list_training_pipelines(
        self, service, sample_training_pipeline_response
    ):
        mock_pipelines = (
            service.service.projects()
            .locations()
            .trainingPipelines()
        )
        mock_pipelines.list().execute.return_value = {
            "trainingPipelines": [sample_training_pipeline_response]
        }
        mock_pipelines.list_next.return_value = None

        results = service.list_training_pipelines("us-central1")
        assert len(results) == 1
        assert results[0].display_name == "test-pipeline"
        assert isinstance(results[0], TrainingPipeline)

    def test_list_training_pipelines_empty(self, service):
        mock_pipelines = (
            service.service.projects()
            .locations()
            .trainingPipelines()
        )
        mock_pipelines.list().execute.return_value = {}
        mock_pipelines.list_next.return_value = None

        results = service.list_training_pipelines("us-central1")
        assert len(results) == 0

    def test_create_training_pipeline(
        self, service, sample_training_pipeline_response
    ):
        mock_pipelines = (
            service.service.projects()
            .locations()
            .trainingPipelines()
        )
        mock_pipelines.create().execute.return_value = (
            sample_training_pipeline_response
        )

        result = service.create_training_pipeline(
            location="us-central1",
            display_name="test-pipeline",
            training_task_definition="gs://google-cloud-aiplatform/schema/trainingjob/definition/automl_tabular_1.0.0.yaml",
            training_task_inputs={"targetColumn": "label"},
            model_display_name="trained-model",
        )
        assert result.display_name == "test-pipeline"
        assert isinstance(result, TrainingPipeline)

    def test_create_training_pipeline_without_model(
        self, service, sample_training_pipeline_response
    ):
        mock_pipelines = (
            service.service.projects()
            .locations()
            .trainingPipelines()
        )
        mock_pipelines.create().execute.return_value = (
            sample_training_pipeline_response
        )

        result = service.create_training_pipeline(
            location="us-central1",
            display_name="test-pipeline",
            training_task_definition="gs://schema/def.yaml",
            training_task_inputs={"targetColumn": "label"},
        )
        assert result.display_name == "test-pipeline"

    def test_create_training_pipeline_api_error(self, service):
        mock_pipelines = (
            service.service.projects()
            .locations()
            .trainingPipelines()
        )
        mock_pipelines.create().execute.side_effect = _make_http_error(400)

        with pytest.raises(APIError):
            service.create_training_pipeline(
                location="us-central1",
                display_name="bad",
                training_task_definition="gs://schema/def.yaml",
                training_task_inputs={},
            )


# ---- Path Formatting Tests ----


class TestVertexAIServicePathFormatting:
    def test_format_parent(self, service):
        assert service._format_parent("us-central1") == (
            "projects/test-project/locations/us-central1"
        )

    def test_format_dataset_name(self, service):
        assert service._format_dataset_name("us-central1", "123") == (
            "projects/test-project/locations/us-central1/datasets/123"
        )

    def test_format_dataset_name_full_path(self, service):
        full_path = "projects/other/locations/us-east1/datasets/456"
        assert service._format_dataset_name("us-central1", full_path) == full_path

    def test_format_model_name(self, service):
        assert service._format_model_name("us-central1", "456") == (
            "projects/test-project/locations/us-central1/models/456"
        )

    def test_format_model_name_full_path(self, service):
        full_path = "projects/other/locations/us-east1/models/789"
        assert service._format_model_name("us-central1", full_path) == full_path

    def test_format_endpoint_name(self, service):
        assert service._format_endpoint_name("us-central1", "789") == (
            "projects/test-project/locations/us-central1/endpoints/789"
        )

    def test_format_endpoint_name_full_path(self, service):
        full_path = "projects/other/locations/us-east1/endpoints/123"
        assert (
            service._format_endpoint_name("us-central1", full_path) == full_path
        )


# ---- Service Initialization Tests ----


class TestVertexAIServiceInit:
    def test_service_init(self, service):
        assert service.project_id == "test-project"
        assert service.service_name == "aiplatform"
        assert service.version == "v1"
        assert service.resource_model == VertexDataset
