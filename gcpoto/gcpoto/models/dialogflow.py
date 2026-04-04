"""Models for Google Cloud Dialogflow CX resources."""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.dialogflow import get_schema


class Agent(GCPResource):
    """Model for a Dialogflow CX Agent."""

    location: str = ""
    display_name: str = ""
    default_language_code: str = ""
    supported_language_codes: Optional[List[str]] = None
    time_zone: str = ""
    description: Optional[str] = None
    start_flow: Optional[str] = None
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("agent")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "Agent":
        """Create an Agent from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Agent instance
        """
        name = response.get("name", "")
        # name format: projects/{project}/locations/{location}/agents/{id}
        parts = name.split("/")
        agent_id = parts[-1] if len(parts) >= 6 else ""
        project = parts[1] if len(parts) >= 2 else ""
        location = parts[3] if len(parts) >= 4 else ""

        instance = cls(
            id=agent_id,
            name=name,
            type="dialogflow.agent",
            project=project,
            location=location,
            display_name=response.get("displayName", ""),
            default_language_code=response.get("defaultLanguageCode", ""),
            supported_language_codes=response.get("supportedLanguageCodes"),
            time_zone=response.get("timeZone", ""),
            description=response.get("description"),
            start_flow=response.get("startFlow"),
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


class Flow(GCPResource):
    """Model for a Dialogflow CX Flow."""

    agent_name: str = ""
    location: str = ""
    display_name: str = ""
    description: Optional[str] = None
    transition_routes: Optional[List[Dict]] = None
    event_handlers: Optional[List[Dict]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("flow")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "Flow":
        """Create a Flow from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Flow instance
        """
        name = response.get("name", "")
        # name format: projects/{project}/locations/{location}/agents/{aid}/flows/{fid}
        parts = name.split("/")
        flow_id = parts[-1] if len(parts) >= 8 else ""
        project = parts[1] if len(parts) >= 2 else ""
        location = parts[3] if len(parts) >= 4 else ""
        agent_name = "/".join(parts[:6]) if len(parts) >= 6 else ""

        return cls(
            id=flow_id,
            name=name,
            type="dialogflow.flow",
            project=project,
            agent_name=agent_name,
            location=location,
            display_name=response.get("displayName", ""),
            description=response.get("description"),
            transition_routes=response.get("transitionRoutes"),
            event_handlers=response.get("eventHandlers"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )


class Intent(GCPResource):
    """Model for a Dialogflow CX Intent."""

    agent_name: str = ""
    location: str = ""
    display_name: str = ""
    training_phrases: Optional[List[Dict]] = None
    parameters: Optional[List[Dict]] = None
    priority: Optional[int] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("intent")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "Intent":
        """Create an Intent from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Intent instance
        """
        name = response.get("name", "")
        # name format: projects/{project}/locations/{location}/agents/{aid}/intents/{iid}
        parts = name.split("/")
        intent_id = parts[-1] if len(parts) >= 8 else ""
        project = parts[1] if len(parts) >= 2 else ""
        location = parts[3] if len(parts) >= 4 else ""
        agent_name = "/".join(parts[:6]) if len(parts) >= 6 else ""

        return cls(
            id=intent_id,
            name=name,
            type="dialogflow.intent",
            project=project,
            agent_name=agent_name,
            location=location,
            display_name=response.get("displayName", ""),
            training_phrases=response.get("trainingPhrases"),
            parameters=response.get("parameters"),
            priority=response.get("priority"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
