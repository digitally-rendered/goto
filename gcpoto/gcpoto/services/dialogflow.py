"""Service implementation for Google Cloud Dialogflow CX."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.dialogflow import Agent, Flow, Intent
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class DialogflowService(GCPService[Agent]):
    """Service for interacting with Google Cloud Dialogflow CX."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Dialogflow CX service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="dialogflow",
            version="v3",
            credentials_file=credentials_file,
            resource_model=Agent,
            **kwargs,
        )

    def _format_parent(self, location: str) -> str:
        """Format the parent path for Dialogflow CX resources.

        Args:
            location: The GCP location/region

        Returns:
            The formatted parent path
        """
        return f"projects/{self.project_id}/locations/{location}"

    def _format_agent_name(self, location: str, agent_id: str) -> str:
        """Format the full agent resource name.

        Args:
            location: The GCP location/region
            agent_id: The agent ID or full resource path

        Returns:
            The fully qualified agent resource name
        """
        if "/" in agent_id:
            return agent_id
        return f"projects/{self.project_id}/locations/{location}/agents/{agent_id}"

    def _format_flow_name(
        self, location: str, agent_id: str, flow_id: str
    ) -> str:
        """Format the full flow resource name.

        Args:
            location: The GCP location/region
            agent_id: The agent ID
            flow_id: The flow ID or full resource path

        Returns:
            The fully qualified flow resource name
        """
        if "/" in flow_id:
            return flow_id
        agent_name = self._format_agent_name(location, agent_id)
        return f"{agent_name}/flows/{flow_id}"

    def _format_intent_name(
        self, location: str, agent_id: str, intent_id: str
    ) -> str:
        """Format the full intent resource name.

        Args:
            location: The GCP location/region
            agent_id: The agent ID
            intent_id: The intent ID or full resource path

        Returns:
            The fully qualified intent resource name
        """
        if "/" in intent_id:
            return intent_id
        agent_name = self._format_agent_name(location, agent_id)
        return f"{agent_name}/intents/{intent_id}"

    def _format_session_name(
        self, location: str, agent_id: str, session_id: str
    ) -> str:
        """Format the full session resource name.

        Args:
            location: The GCP location/region
            agent_id: The agent ID
            session_id: The session ID

        Returns:
            The fully qualified session resource name
        """
        agent_name = self._format_agent_name(location, agent_id)
        return f"{agent_name}/sessions/{session_id}"

    # ---- Agent methods ----

    def list_agents(self, location: str, **kwargs) -> List[Agent]:
        """List Dialogflow CX agents in a location.

        Args:
            location: The GCP location/region
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of Agent instances
        """
        logger.debug(
            "Listing agents in %s for project %s",
            location,
            self.project_id,
        )

        parent = self._format_parent(location)
        agents = []
        request = (
            self.service.projects()
            .locations()
            .agents()
            .list(parent=parent, **kwargs)
        )

        while request is not None:
            response = request.execute()
            for item in response.get("agents", []):
                agents.append(Agent.from_api_response(item))
            request = (
                self.service.projects()
                .locations()
                .agents()
                .list_next(request, response)
            )

        logger.debug("Found %s agents", len(agents))
        return agents

    def get_agent(self, location: str, agent_id: str) -> Agent:
        """Get a specific Dialogflow CX agent.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent to retrieve

        Returns:
            An Agent instance
        """
        logger.debug(
            "Getting agent %s in %s for project %s",
            agent_id,
            location,
            self.project_id,
        )

        name = self._format_agent_name(location, agent_id)
        try:
            request = (
                self.service.projects()
                .locations()
                .agents()
                .get(name=name)
            )
            response = request.execute()
            return Agent.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("agent", agent_id)
            raise APIError(e.resp.status, str(e))

    def create_agent(
        self,
        location: str,
        display_name: str,
        default_language_code: str,
        time_zone: str,
        description: Optional[str] = None,
    ) -> Agent:
        """Create a new Dialogflow CX agent.

        Args:
            location: The GCP location/region
            display_name: The display name of the agent
            default_language_code: The default language code (e.g., "en")
            time_zone: The time zone (e.g., "America/New_York")
            description: Optional description of the agent

        Returns:
            An Agent instance for the newly created agent
        """
        logger.info(
            "Creating agent %s in %s for project %s",
            display_name,
            location,
            self.project_id,
        )

        parent = self._format_parent(location)
        body: Dict[str, Any] = {
            "displayName": display_name,
            "defaultLanguageCode": default_language_code,
            "timeZone": time_zone,
        }

        if description is not None:
            body["description"] = description

        try:
            request = (
                self.service.projects()
                .locations()
                .agents()
                .create(parent=parent, body=body)
            )
            response = request.execute()
            return Agent.from_api_response(response)
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

    def update_agent(
        self,
        location: str,
        agent_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> Agent:
        """Update a Dialogflow CX agent.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent to update
            update_mask: Comma-separated list of fields to update
            update_fields: Dictionary of fields and their new values

        Returns:
            An Agent instance with the updated values
        """
        logger.info(
            "Updating agent %s in %s for project %s",
            agent_id,
            location,
            self.project_id,
        )

        name = self._format_agent_name(location, agent_id)
        body: Dict[str, Any] = {"name": name}
        body.update(update_fields)

        try:
            request = (
                self.service.projects()
                .locations()
                .agents()
                .patch(name=name, updateMask=update_mask, body=body)
            )
            response = request.execute()
            return Agent.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("agent", agent_id)
            raise APIError(e.resp.status, str(e))

    def delete_agent(self, location: str, agent_id: str) -> bool:
        """Delete a Dialogflow CX agent.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting agent %s in %s for project %s",
            agent_id,
            location,
            self.project_id,
        )

        name = self._format_agent_name(location, agent_id)
        try:
            self.service.projects().locations().agents().delete(
                name=name
            ).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("agent", agent_id)
            raise APIError(e.resp.status, str(e))

    # ---- Flow methods ----

    def list_flows(
        self, location: str, agent_id: str, **kwargs
    ) -> List[Flow]:
        """List flows for a Dialogflow CX agent.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of Flow instances
        """
        logger.debug(
            "Listing flows for agent %s in %s for project %s",
            agent_id,
            location,
            self.project_id,
        )

        parent = self._format_agent_name(location, agent_id)
        flows = []
        request = (
            self.service.projects()
            .locations()
            .agents()
            .flows()
            .list(parent=parent, **kwargs)
        )

        while request is not None:
            response = request.execute()
            for item in response.get("flows", []):
                flows.append(Flow.from_api_response(item))
            request = (
                self.service.projects()
                .locations()
                .agents()
                .flows()
                .list_next(request, response)
            )

        logger.debug("Found %s flows", len(flows))
        return flows

    def get_flow(
        self, location: str, agent_id: str, flow_id: str
    ) -> Flow:
        """Get a specific flow for a Dialogflow CX agent.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent
            flow_id: The ID of the flow to retrieve

        Returns:
            A Flow instance
        """
        logger.debug(
            "Getting flow %s for agent %s in %s for project %s",
            flow_id,
            agent_id,
            location,
            self.project_id,
        )

        name = self._format_flow_name(location, agent_id, flow_id)
        try:
            request = (
                self.service.projects()
                .locations()
                .agents()
                .flows()
                .get(name=name)
            )
            response = request.execute()
            return Flow.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("flow", flow_id)
            raise APIError(e.resp.status, str(e))

    def create_flow(
        self,
        location: str,
        agent_id: str,
        display_name: str,
        description: Optional[str] = None,
    ) -> Flow:
        """Create a new flow for a Dialogflow CX agent.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent
            display_name: The display name of the flow
            description: Optional description of the flow

        Returns:
            A Flow instance for the newly created flow
        """
        logger.info(
            "Creating flow %s for agent %s in %s for project %s",
            display_name,
            agent_id,
            location,
            self.project_id,
        )

        parent = self._format_agent_name(location, agent_id)
        body: Dict[str, Any] = {
            "displayName": display_name,
        }

        if description is not None:
            body["description"] = description

        try:
            request = (
                self.service.projects()
                .locations()
                .agents()
                .flows()
                .create(parent=parent, body=body)
            )
            response = request.execute()
            return Flow.from_api_response(response)
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

    def delete_flow(
        self, location: str, agent_id: str, flow_id: str
    ) -> bool:
        """Delete a flow from a Dialogflow CX agent.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent
            flow_id: The ID of the flow to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting flow %s for agent %s in %s for project %s",
            flow_id,
            agent_id,
            location,
            self.project_id,
        )

        name = self._format_flow_name(location, agent_id, flow_id)
        try:
            (
                self.service.projects()
                .locations()
                .agents()
                .flows()
                .delete(name=name)
                .execute()
            )
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("flow", flow_id)
            raise APIError(e.resp.status, str(e))

    # ---- Intent methods ----

    def list_intents(
        self, location: str, agent_id: str, **kwargs
    ) -> List[Intent]:
        """List intents for a Dialogflow CX agent.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of Intent instances
        """
        logger.debug(
            "Listing intents for agent %s in %s for project %s",
            agent_id,
            location,
            self.project_id,
        )

        parent = self._format_agent_name(location, agent_id)
        intents = []
        request = (
            self.service.projects()
            .locations()
            .agents()
            .intents()
            .list(parent=parent, **kwargs)
        )

        while request is not None:
            response = request.execute()
            for item in response.get("intents", []):
                intents.append(Intent.from_api_response(item))
            request = (
                self.service.projects()
                .locations()
                .agents()
                .intents()
                .list_next(request, response)
            )

        logger.debug("Found %s intents", len(intents))
        return intents

    def get_intent(
        self, location: str, agent_id: str, intent_id: str
    ) -> Intent:
        """Get a specific intent for a Dialogflow CX agent.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent
            intent_id: The ID of the intent to retrieve

        Returns:
            An Intent instance
        """
        logger.debug(
            "Getting intent %s for agent %s in %s for project %s",
            intent_id,
            agent_id,
            location,
            self.project_id,
        )

        name = self._format_intent_name(location, agent_id, intent_id)
        try:
            request = (
                self.service.projects()
                .locations()
                .agents()
                .intents()
                .get(name=name)
            )
            response = request.execute()
            return Intent.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("intent", intent_id)
            raise APIError(e.resp.status, str(e))

    def create_intent(
        self,
        location: str,
        agent_id: str,
        display_name: str,
        training_phrases: Optional[List[Dict[str, Any]]] = None,
    ) -> Intent:
        """Create a new intent for a Dialogflow CX agent.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent
            display_name: The display name of the intent
            training_phrases: Optional list of training phrases

        Returns:
            An Intent instance for the newly created intent
        """
        logger.info(
            "Creating intent %s for agent %s in %s for project %s",
            display_name,
            agent_id,
            location,
            self.project_id,
        )

        parent = self._format_agent_name(location, agent_id)
        body: Dict[str, Any] = {
            "displayName": display_name,
        }

        if training_phrases is not None:
            body["trainingPhrases"] = training_phrases

        try:
            request = (
                self.service.projects()
                .locations()
                .agents()
                .intents()
                .create(parent=parent, body=body)
            )
            response = request.execute()
            return Intent.from_api_response(response)
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

    def delete_intent(
        self, location: str, agent_id: str, intent_id: str
    ) -> bool:
        """Delete an intent from a Dialogflow CX agent.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent
            intent_id: The ID of the intent to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting intent %s for agent %s in %s for project %s",
            intent_id,
            agent_id,
            location,
            self.project_id,
        )

        name = self._format_intent_name(location, agent_id, intent_id)
        try:
            (
                self.service.projects()
                .locations()
                .agents()
                .intents()
                .delete(name=name)
                .execute()
            )
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("intent", intent_id)
            raise APIError(e.resp.status, str(e))

    # ---- Session methods ----

    def detect_intent(
        self,
        location: str,
        agent_id: str,
        session_id: str,
        text: str,
        language_code: str = "en",
    ) -> Dict[str, Any]:
        """Detect intent from a text input.

        Args:
            location: The GCP location/region
            agent_id: The ID of the agent
            session_id: The session ID for the conversation
            text: The user text input
            language_code: The language code for the input (default: "en")

        Returns:
            A dictionary containing the detect intent response
        """
        logger.info(
            "Detecting intent for agent %s in %s for project %s",
            agent_id,
            location,
            self.project_id,
        )

        session = self._format_session_name(location, agent_id, session_id)
        body: Dict[str, Any] = {
            "queryInput": {
                "text": {
                    "text": text,
                },
                "languageCode": language_code,
            },
        }

        try:
            request = (
                self.service.projects()
                .locations()
                .agents()
                .sessions()
                .detectIntent(session=session, body=body)
            )
            response = request.execute()
            return response
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("agent", agent_id)
            raise APIError(e.resp.status, str(e))
