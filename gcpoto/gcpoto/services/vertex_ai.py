"""Service implementation for Google Cloud Vertex AI."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.vertex_ai import (
    VertexDataset,
    VertexModel,
    VertexEndpoint,
    TrainingPipeline,
)

logger = logging.getLogger(__name__)

class VertexAIService(GCPService[VertexDataset]):
    """Service for interacting with Google Cloud Vertex AI."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Vertex AI service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="aiplatform",
            version="v1",
            credentials_file=credentials_file,
            resource_model=VertexDataset,
            **kwargs,
        )

    def _format_parent(self, location: str) -> str:
        """Format the parent path for Vertex AI resources.

        Args:
            location: The GCP location/region

        Returns:
            The formatted parent path
        """
        return f"projects/{self.project_id}/locations/{location}"

    def _format_dataset_name(self, location: str, dataset_id: str) -> str:
        """Format the full dataset resource name.

        Args:
            location: The GCP location/region
            dataset_id: The dataset ID or full resource path

        Returns:
            The fully qualified dataset resource name
        """
        if "/" in dataset_id:
            return dataset_id
        return f"projects/{self.project_id}/locations/{location}/datasets/{dataset_id}"

    def _format_model_name(self, location: str, model_id: str) -> str:
        """Format the full model resource name.

        Args:
            location: The GCP location/region
            model_id: The model ID or full resource path

        Returns:
            The fully qualified model resource name
        """
        if "/" in model_id:
            return model_id
        return f"projects/{self.project_id}/locations/{location}/models/{model_id}"

    def _format_endpoint_name(self, location: str, endpoint_id: str) -> str:
        """Format the full endpoint resource name.

        Args:
            location: The GCP location/region
            endpoint_id: The endpoint ID or full resource path

        Returns:
            The fully qualified endpoint resource name
        """
        if "/" in endpoint_id:
            return endpoint_id
        return f"projects/{self.project_id}/locations/{location}/endpoints/{endpoint_id}"

    # ---- Dataset methods ----

    def list_datasets(self, location: str, **kwargs) -> List[VertexDataset]:
        """List Vertex AI datasets in a location.

        Args:
            location: The GCP location/region
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of VertexDataset instances
        """
        logger.debug(
            "Listing datasets in %s for project %s", location, self.project_id
        )

        parent = self._format_parent(location)
        datasets = []
        request = self.service.projects().locations().datasets().list(
            parent=parent, **kwargs
        )

        while request is not None:
            response = self._execute(request)
            for item in response.get("datasets", []):
                datasets.append(
                    VertexDataset.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .datasets()
                .list_next(request, response)
            )

        logger.debug("Found %s datasets", len(datasets))
        return datasets

    def get_dataset(self, location: str, dataset_id: str) -> VertexDataset:
        """Get a specific Vertex AI dataset.

        Args:
            location: The GCP location/region
            dataset_id: The ID of the dataset to retrieve

        Returns:
            A VertexDataset instance
        """
        logger.debug(
            "Getting dataset %s in %s for project %s",
            dataset_id,
            location,
            self.project_id,
        )

        name = self._format_dataset_name(location, dataset_id)
        request = self.service.projects().locations().datasets().get(
            name=name
        )
        response = self._execute(request, "dataset", dataset_id)
        return VertexDataset.from_api_response(response, self.project_id)
    def create_dataset(
        self,
        location: str,
        display_name: str,
        metadata_schema_uri: str,
        metadata: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> VertexDataset:
        """Create a new Vertex AI dataset.

        Args:
            location: The GCP location/region
            display_name: The display name of the dataset
            metadata_schema_uri: The schema URI for the dataset metadata
            metadata: Optional metadata for the dataset
            labels: Optional labels to apply to the dataset

        Returns:
            A VertexDataset instance for the newly created dataset
        """
        logger.info(
            "Creating dataset %s in %s for project %s",
            display_name,
            location,
            self.project_id,
        )

        parent = self._format_parent(location)
        body: Dict[str, Any] = {
            "displayName": display_name,
            "metadataSchemaUri": metadata_schema_uri,
        }

        if metadata is not None:
            body["metadata"] = metadata

        if labels is not None:
            body["labels"] = labels

        request = self.service.projects().locations().datasets().create(
            parent=parent, body=body
        )
        response = self._execute(request)
        return VertexDataset.from_api_response(response, self.project_id)
    def delete_dataset(self, location: str, dataset_id: str) -> bool:
        """Delete a Vertex AI dataset.

        Args:
            location: The GCP location/region
            dataset_id: The ID of the dataset to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting dataset %s in %s for project %s",
            dataset_id,
            location,
            self.project_id,
        )

        name = self._format_dataset_name(location, dataset_id)
        self.service.projects().locations().datasets().delete(
            name=name
        ).execute()
        return True
    def list_models(self, location: str, **kwargs) -> List[VertexModel]:
        """List Vertex AI models in a location.

        Args:
            location: The GCP location/region
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of VertexModel instances
        """
        logger.debug(
            "Listing models in %s for project %s", location, self.project_id
        )

        parent = self._format_parent(location)
        models = []
        request = self.service.projects().locations().models().list(
            parent=parent, **kwargs
        )

        while request is not None:
            response = self._execute(request)
            for item in response.get("models", []):
                models.append(
                    VertexModel.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .models()
                .list_next(request, response)
            )

        logger.debug("Found %s models", len(models))
        return models

    def get_model(self, location: str, model_id: str) -> VertexModel:
        """Get a specific Vertex AI model.

        Args:
            location: The GCP location/region
            model_id: The ID of the model to retrieve

        Returns:
            A VertexModel instance
        """
        logger.debug(
            "Getting model %s in %s for project %s",
            model_id,
            location,
            self.project_id,
        )

        name = self._format_model_name(location, model_id)
        request = self.service.projects().locations().models().get(
            name=name
        )
        response = self._execute(request, "model", model_id)
        return VertexModel.from_api_response(response, self.project_id)
    def upload_model(
        self,
        location: str,
        display_name: str,
        artifact_uri: Optional[str] = None,
        container_spec: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> VertexModel:
        """Upload a new Vertex AI model.

        Args:
            location: The GCP location/region
            display_name: The display name of the model
            artifact_uri: Optional path to the model artifacts
            container_spec: Optional container specification for serving
            description: Optional description of the model
            labels: Optional labels to apply to the model

        Returns:
            A VertexModel instance for the newly uploaded model
        """
        logger.info(
            "Uploading model %s in %s for project %s",
            display_name,
            location,
            self.project_id,
        )

        parent = self._format_parent(location)
        model_body: Dict[str, Any] = {
            "displayName": display_name,
        }

        if artifact_uri is not None:
            model_body["artifactUri"] = artifact_uri

        if container_spec is not None:
            model_body["containerSpec"] = container_spec

        if description is not None:
            model_body["description"] = description

        if labels is not None:
            model_body["labels"] = labels

        body: Dict[str, Any] = {"model": model_body}

        request = self.service.projects().locations().models().upload(
            parent=parent, body=body
        )
        response = self._execute(request)
        return VertexModel.from_api_response(response, self.project_id)
    def delete_model(self, location: str, model_id: str) -> bool:
        """Delete a Vertex AI model.

        Args:
            location: The GCP location/region
            model_id: The ID of the model to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting model %s in %s for project %s",
            model_id,
            location,
            self.project_id,
        )

        name = self._format_model_name(location, model_id)
        self.service.projects().locations().models().delete(
            name=name
        ).execute()
        return True
    def list_endpoints(self, location: str, **kwargs) -> List[VertexEndpoint]:
        """List Vertex AI endpoints in a location.

        Args:
            location: The GCP location/region
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of VertexEndpoint instances
        """
        logger.debug(
            "Listing endpoints in %s for project %s",
            location,
            self.project_id,
        )

        parent = self._format_parent(location)
        endpoints = []
        request = self.service.projects().locations().endpoints().list(
            parent=parent, **kwargs
        )

        while request is not None:
            response = self._execute(request)
            for item in response.get("endpoints", []):
                endpoints.append(
                    VertexEndpoint.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .endpoints()
                .list_next(request, response)
            )

        logger.debug("Found %s endpoints", len(endpoints))
        return endpoints

    def get_endpoint(self, location: str, endpoint_id: str) -> VertexEndpoint:
        """Get a specific Vertex AI endpoint.

        Args:
            location: The GCP location/region
            endpoint_id: The ID of the endpoint to retrieve

        Returns:
            A VertexEndpoint instance
        """
        logger.debug(
            "Getting endpoint %s in %s for project %s",
            endpoint_id,
            location,
            self.project_id,
        )

        name = self._format_endpoint_name(location, endpoint_id)
        request = self.service.projects().locations().endpoints().get(
            name=name
        )
        response = self._execute(request, "endpoint", endpoint_id)
        return VertexEndpoint.from_api_response(
            response, self.project_id
        )
    def create_endpoint(
        self,
        location: str,
        display_name: str,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> VertexEndpoint:
        """Create a new Vertex AI endpoint.

        Args:
            location: The GCP location/region
            display_name: The display name of the endpoint
            description: Optional description of the endpoint
            labels: Optional labels to apply to the endpoint

        Returns:
            A VertexEndpoint instance for the newly created endpoint
        """
        logger.info(
            "Creating endpoint %s in %s for project %s",
            display_name,
            location,
            self.project_id,
        )

        parent = self._format_parent(location)
        body: Dict[str, Any] = {
            "displayName": display_name,
        }

        if description is not None:
            body["description"] = description

        if labels is not None:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .endpoints()
            .create(parent=parent, body=body)
        )
        response = self._execute(request)
        return VertexEndpoint.from_api_response(
            response, self.project_id
        )
    def delete_endpoint(self, location: str, endpoint_id: str) -> bool:
        """Delete a Vertex AI endpoint.

        Args:
            location: The GCP location/region
            endpoint_id: The ID of the endpoint to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting endpoint %s in %s for project %s",
            endpoint_id,
            location,
            self.project_id,
        )

        name = self._format_endpoint_name(location, endpoint_id)
        self.service.projects().locations().endpoints().delete(
            name=name
        ).execute()
        return True
    def deploy_model(
        self,
        location: str,
        endpoint_id: str,
        model_id: str,
        display_name: str,
        machine_type: str = "n1-standard-2",
        min_replica_count: int = 1,
        max_replica_count: int = 1,
    ) -> VertexEndpoint:
        """Deploy a model to an endpoint.

        Args:
            location: The GCP location/region
            endpoint_id: The ID of the endpoint to deploy to
            model_id: The ID of the model to deploy
            display_name: The display name for the deployed model
            machine_type: The machine type for serving
            min_replica_count: Minimum number of replicas
            max_replica_count: Maximum number of replicas

        Returns:
            A VertexEndpoint instance with the updated deployment
        """
        logger.info(
            "Deploying model %s to endpoint %s in %s for project %s",
            model_id,
            endpoint_id,
            location,
            self.project_id,
        )

        endpoint_name = self._format_endpoint_name(location, endpoint_id)
        model_name = self._format_model_name(location, model_id)

        body: Dict[str, Any] = {
            "deployedModel": {
                "model": model_name,
                "displayName": display_name,
                "dedicatedResources": {
                    "machineSpec": {
                        "machineType": machine_type,
                    },
                    "minReplicaCount": min_replica_count,
                    "maxReplicaCount": max_replica_count,
                },
            },
        }

        request = (
            self.service.projects()
            .locations()
            .endpoints()
            .deployModel(endpoint=endpoint_name, body=body)
        )
        response = self._execute(request, "endpoint", endpoint_id)
        return VertexEndpoint.from_api_response(
            response, self.project_id
        )
    def undeploy_model(
        self,
        location: str,
        endpoint_id: str,
        deployed_model_id: str,
    ) -> VertexEndpoint:
        """Undeploy a model from an endpoint.

        Args:
            location: The GCP location/region
            endpoint_id: The ID of the endpoint
            deployed_model_id: The ID of the deployed model to undeploy

        Returns:
            A VertexEndpoint instance with the updated deployment
        """
        logger.info(
            "Undeploying model %s from endpoint %s in %s for project %s",
            deployed_model_id,
            endpoint_id,
            location,
            self.project_id,
        )

        endpoint_name = self._format_endpoint_name(location, endpoint_id)
        body: Dict[str, Any] = {
            "deployedModelId": deployed_model_id,
        }

        request = (
            self.service.projects()
            .locations()
            .endpoints()
            .undeployModel(endpoint=endpoint_name, body=body)
        )
        response = self._execute(request, "endpoint", endpoint_id)
        return VertexEndpoint.from_api_response(
            response, self.project_id
        )
    def predict(
        self,
        location: str,
        endpoint_id: str,
        instances: List[Dict[str, Any]],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a prediction using a deployed model.

        Args:
            location: The GCP location/region
            endpoint_id: The ID of the endpoint to call
            instances: The prediction instances to send
            parameters: Optional parameters for the prediction

        Returns:
            A dictionary containing the prediction results
        """
        logger.info(
            "Making prediction on endpoint %s in %s for project %s",
            endpoint_id,
            location,
            self.project_id,
        )

        endpoint_name = self._format_endpoint_name(location, endpoint_id)
        body: Dict[str, Any] = {
            "instances": instances,
        }

        if parameters is not None:
            body["parameters"] = parameters

        request = (
            self.service.projects()
            .locations()
            .endpoints()
            .predict(endpoint=endpoint_name, body=body)
        )
        response = self._execute(request, "endpoint", endpoint_id)
        return response
    def list_training_pipelines(
        self, location: str, **kwargs
    ) -> List[TrainingPipeline]:
        """List Vertex AI training pipelines in a location.

        Args:
            location: The GCP location/region
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of TrainingPipeline instances
        """
        logger.debug(
            "Listing training pipelines in %s for project %s",
            location,
            self.project_id,
        )

        parent = self._format_parent(location)
        pipelines = []
        request = (
            self.service.projects()
            .locations()
            .trainingPipelines()
            .list(parent=parent, **kwargs)
        )

        while request is not None:
            response = self._execute(request)
            for item in response.get("trainingPipelines", []):
                pipelines.append(
                    TrainingPipeline.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .trainingPipelines()
                .list_next(request, response)
            )

        logger.debug("Found %s training pipelines", len(pipelines))
        return pipelines

    def create_training_pipeline(
        self,
        location: str,
        display_name: str,
        training_task_definition: str,
        training_task_inputs: Dict[str, Any],
        model_display_name: Optional[str] = None,
    ) -> TrainingPipeline:
        """Create a new Vertex AI training pipeline.

        Args:
            location: The GCP location/region
            display_name: The display name of the training pipeline
            training_task_definition: The training task definition resource name
            training_task_inputs: The inputs for the training task
            model_display_name: Optional display name for the model to upload

        Returns:
            A TrainingPipeline instance for the newly created pipeline
        """
        logger.info(
            "Creating training pipeline %s in %s for project %s",
            display_name,
            location,
            self.project_id,
        )

        parent = self._format_parent(location)
        body: Dict[str, Any] = {
            "displayName": display_name,
            "trainingTaskDefinition": training_task_definition,
            "trainingTaskInputs": training_task_inputs,
        }

        if model_display_name is not None:
            body["modelToUpload"] = {"displayName": model_display_name}

        request = (
            self.service.projects()
            .locations()
            .trainingPipelines()
            .create(parent=parent, body=body)
        )
        response = self._execute(request)
        return TrainingPipeline.from_api_response(
            response, self.project_id
        )