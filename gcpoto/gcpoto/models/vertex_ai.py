"""Models for Google Cloud Vertex AI resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.vertex_ai import get_schema


class VertexDataset(GCPResource):
    """Model for a Vertex AI Dataset."""

    location: str = ""
    display_name: str = ""
    metadata_schema_uri: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    data_item_count: Optional[int] = None
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("dataset")}

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "VertexDataset":
        """Create a VertexDataset from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new VertexDataset instance
        """
        name = response.get("name", "")
        # Extract dataset ID and location from resource name
        # Format: projects/{project}/locations/{location}/datasets/{dataset_id}
        parts = name.split("/")
        dataset_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""
        proj = parts[1] if len(parts) >= 2 else project_id

        instance = cls(
            id=dataset_id,
            name=name,
            type="vertex_ai.dataset",
            project=proj,
            location=location,
            display_name=response.get("displayName", ""),
            metadata_schema_uri=response.get("metadataSchemaUri"),
            metadata=response.get("metadata"),
            data_item_count=response.get("dataItemCount"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class VertexModel(GCPResource):
    """Model for a Vertex AI Model."""

    location: str = ""
    display_name: str = ""
    description: Optional[str] = None
    version_id: Optional[str] = None
    artifact_uri: Optional[str] = None
    container_spec: Optional[Dict[str, Any]] = None
    deployed_models: Optional[List[Dict[str, Any]]] = None
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("model")}

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "VertexModel":
        """Create a VertexModel from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new VertexModel instance
        """
        name = response.get("name", "")
        # Format: projects/{project}/locations/{location}/models/{model_id}
        parts = name.split("/")
        model_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""
        proj = parts[1] if len(parts) >= 2 else project_id

        instance = cls(
            id=model_id,
            name=name,
            type="vertex_ai.model",
            project=proj,
            location=location,
            display_name=response.get("displayName", ""),
            description=response.get("description"),
            version_id=response.get("versionId"),
            artifact_uri=response.get("artifactUri"),
            container_spec=response.get("containerSpec"),
            deployed_models=response.get("deployedModels"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class VertexEndpoint(GCPResource):
    """Model for a Vertex AI Endpoint."""

    location: str = ""
    display_name: str = ""
    description: Optional[str] = None
    deployed_models: Optional[List[Dict[str, Any]]] = None
    traffic_split: Optional[Dict[str, Any]] = None
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("endpoint")}

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "VertexEndpoint":
        """Create a VertexEndpoint from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new VertexEndpoint instance
        """
        name = response.get("name", "")
        # Format: projects/{project}/locations/{location}/endpoints/{endpoint_id}
        parts = name.split("/")
        endpoint_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""
        proj = parts[1] if len(parts) >= 2 else project_id

        instance = cls(
            id=endpoint_id,
            name=name,
            type="vertex_ai.endpoint",
            project=proj,
            location=location,
            display_name=response.get("displayName", ""),
            description=response.get("description"),
            deployed_models=response.get("deployedModels"),
            traffic_split=response.get("trafficSplit"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class TrainingPipeline(GCPResource):
    """Model for a Vertex AI Training Pipeline."""

    location: str = ""
    display_name: str = ""
    state: str = ""
    training_task_definition: Optional[str] = None
    training_task_inputs: Optional[Dict[str, Any]] = None
    model_to_upload: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("training_pipeline")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "TrainingPipeline":
        """Create a TrainingPipeline from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new TrainingPipeline instance
        """
        name = response.get("name", "")
        # Format: projects/{project}/locations/{location}/trainingPipelines/{id}
        parts = name.split("/")
        pipeline_id = parts[-1] if len(parts) >= 6 else ""
        location = parts[3] if len(parts) >= 4 else ""
        proj = parts[1] if len(parts) >= 2 else project_id

        instance = cls(
            id=pipeline_id,
            name=name,
            type="vertex_ai.training_pipeline",
            project=proj,
            location=location,
            display_name=response.get("displayName", ""),
            state=response.get("state", ""),
            training_task_definition=response.get("trainingTaskDefinition"),
            training_task_inputs=response.get("trainingTaskInputs"),
            model_to_upload=response.get("modelToUpload"),
            start_time=response.get("startTime"),
            end_time=response.get("endTime"),
            error=response.get("error"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        return instance
