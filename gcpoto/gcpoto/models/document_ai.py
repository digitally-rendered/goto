"""Models for Google Cloud Document AI resources."""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.document_ai import get_schema


class Processor(GCPResource):
    """Model for a Document AI Processor."""

    location: str = ""
    display_name: str = ""
    processor_type: str = ""
    state: str = ""
    default_processor_version: Optional[str] = None
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("processor")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "Processor":
        """Create a Processor from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Processor instance
        """
        name = response.get("name", "")
        # name format: projects/{project}/locations/{location}/processors/{id}
        parts = name.split("/")
        processor_id = parts[-1] if len(parts) >= 6 else ""
        project = parts[1] if len(parts) >= 2 else ""
        location = parts[3] if len(parts) >= 4 else ""

        instance = cls(
            id=processor_id,
            name=name,
            type="documentai.processor",
            project=project,
            location=location,
            display_name=response.get("displayName", ""),
            processor_type=response.get("type", ""),
            state=response.get("state", ""),
            default_processor_version=response.get("defaultProcessorVersion"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key.

        Args:
            key: The tag key to look up
            default: Default value if the key is not found

        Returns:
            The tag value or the default
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default


class ProcessorVersion(GCPResource):
    """Model for a Document AI Processor Version."""

    processor_name: str = ""
    location: str = ""
    display_name: Optional[str] = None
    state: str = ""

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("processor_version")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "ProcessorVersion":
        """Create a ProcessorVersion from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ProcessorVersion instance
        """
        name = response.get("name", "")
        # name format: projects/{project}/locations/{location}/processors/{pid}/processorVersions/{vid}
        parts = name.split("/")
        version_id = parts[-1] if len(parts) >= 8 else ""
        project = parts[1] if len(parts) >= 2 else ""
        location = parts[3] if len(parts) >= 4 else ""
        processor_name = (
            "/".join(parts[:6]) if len(parts) >= 6 else ""
        )

        return cls(
            id=version_id,
            name=name,
            type="documentai.processor_version",
            project=project,
            processor_name=processor_name,
            location=location,
            display_name=response.get("displayName"),
            state=response.get("state", ""),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )


class ProcessResult(GCPResource):
    """Model for a Document AI process result."""

    document: Dict = Field(default_factory=dict)
    human_review_status: Optional[Dict] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("process_result")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "ProcessResult":
        """Create a ProcessResult from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ProcessResult instance
        """
        return cls(
            id="",
            name="",
            type="documentai.process_result",
            project="",
            document=response.get("document", {}),
            human_review_status=response.get("humanReviewStatus"),
        )
