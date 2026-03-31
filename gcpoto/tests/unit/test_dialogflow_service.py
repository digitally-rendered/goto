"""Tests for Dialogflow CX service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.dialogflow import DialogflowService
from gcpoto.models.dialogflow import Agent, Flow, Intent
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

        mock_agents = mock.MagicMock()
        mock_locations.agents.return_value = mock_agents

        mock_flows = mock.MagicMock()
        mock_agents.flows.return_value = mock_flows

        mock_intents = mock.MagicMock()
        mock_agents.intents.return_value = mock_intents

        mock_sessions = mock.MagicMock()
        mock_agents.sessions.return_value = mock_sessions

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a DialogflowService with mocked client."""
    return DialogflowService(project_id="test-project")


@pytest.fixture
def sample_agent_response():
    """Sample Dialogflow CX agent API response."""
    return {
        "name": "projects/test-project/locations/us-central1/agents/agent-123",
        "displayName": "test-agent",
        "defaultLanguageCode": "en",
        "supportedLanguageCodes": ["es", "fr"],
        "timeZone": "America/New_York",
        "description": "A test agent",
        "startFlow": "projects/test-project/locations/us-central1/agents/agent-123/flows/00000000-0000-0000-0000-000000000000",
        "labels": {"env": "test"},
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-01-02T00:00:00Z",
    }


@pytest.fixture
def sample_flow_response():
    """Sample Dialogflow CX flow API response."""
    return {
        "name": "projects/test-project/locations/us-central1/agents/agent-123/flows/flow-456",
        "displayName": "test-flow",
        "description": "A test flow",
        "transitionRoutes": [
            {
                "intent": "projects/test-project/locations/us-central1/agents/agent-123/intents/intent-789",
                "triggerFulfillment": {"messages": [{"text": {"text": ["Hello"]}}]},
            }
        ],
        "eventHandlers": [
            {"event": "sys.no-match-default", "triggerFulfillment": {"messages": []}}
        ],
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-01-02T00:00:00Z",
    }


@pytest.fixture
def sample_intent_response():
    """Sample Dialogflow CX intent API response."""
    return {
        "name": "projects/test-project/locations/us-central1/agents/agent-123/intents/intent-789",
        "displayName": "test-intent",
        "trainingPhrases": [
            {
                "id": "tp-1",
                "parts": [{"text": "hello"}],
                "repeatCount": 1,
            }
        ],
        "parameters": [
            {
                "id": "param-1",
                "entityType": "sys.any",
                "isList": False,
            }
        ],
        "priority": 500000,
        "createTime": "2025-01-01T00:00:00Z",
        "updateTime": "2025-01-02T00:00:00Z",
    }


def _make_http_error(status_code, reason="error"):
    """Create a mock HttpError with the given status code."""
    resp = mock.MagicMock()
    resp.status = status_code
    return HttpError(resp, b'{"error": {"message": "' + reason.encode() + b'"}}')


# ---- Agent Model Tests ----


class TestAgentModel:
    def test_from_api_response(self, sample_agent_response):
        agent = Agent.from_api_response(sample_agent_response)
        assert agent.id == "agent-123"
        assert agent.display_name == "test-agent"
        assert agent.location == "us-central1"
        assert agent.project == "test-project"
        assert agent.type == "dialogflow.agent"
        assert agent.default_language_code == "en"
        assert agent.supported_language_codes == ["es", "fr"]
        assert agent.time_zone == "America/New_York"
        assert agent.description == "A test agent"
        assert agent.start_flow is not None

    def test_from_api_response_minimal(self):
        response = {
            "name": "projects/p/locations/loc/agents/1",
            "displayName": "minimal",
            "defaultLanguageCode": "en",
            "timeZone": "UTC",
        }
        agent = Agent.from_api_response(response)
        assert agent.id == "1"
        assert agent.display_name == "minimal"
        assert agent.supported_language_codes is None
        assert agent.description is None
        assert agent.start_flow is None

    def test_get_tag(self, sample_agent_response):
        agent = Agent.from_api_response(sample_agent_response)
        assert agent.get_tag("env") == "test"
        assert agent.get_tag("missing", "default") == "default"


class TestFlowModel:
    def test_from_api_response(self, sample_flow_response):
        flow = Flow.from_api_response(sample_flow_response)
        assert flow.id == "flow-456"
        assert flow.display_name == "test-flow"
        assert flow.description == "A test flow"
        assert flow.location == "us-central1"
        assert flow.agent_name == "projects/test-project/locations/us-central1/agents/agent-123"
        assert flow.transition_routes is not None
        assert len(flow.transition_routes) == 1
        assert flow.event_handlers is not None
        assert len(flow.event_handlers) == 1

    def test_from_api_response_minimal(self):
        response = {
            "name": "projects/p/locations/loc/agents/a/flows/f",
            "displayName": "minimal-flow",
        }
        flow = Flow.from_api_response(response)
        assert flow.id == "f"
        assert flow.display_name == "minimal-flow"
        assert flow.description is None
        assert flow.transition_routes is None
        assert flow.event_handlers is None


class TestIntentModel:
    def test_from_api_response(self, sample_intent_response):
        intent = Intent.from_api_response(sample_intent_response)
        assert intent.id == "intent-789"
        assert intent.display_name == "test-intent"
        assert intent.location == "us-central1"
        assert intent.agent_name == "projects/test-project/locations/us-central1/agents/agent-123"
        assert intent.training_phrases is not None
        assert len(intent.training_phrases) == 1
        assert intent.parameters is not None
        assert len(intent.parameters) == 1
        assert intent.priority == 500000

    def test_from_api_response_minimal(self):
        response = {
            "name": "projects/p/locations/loc/agents/a/intents/i",
            "displayName": "minimal-intent",
        }
        intent = Intent.from_api_response(response)
        assert intent.id == "i"
        assert intent.display_name == "minimal-intent"
        assert intent.training_phrases is None
        assert intent.parameters is None
        assert intent.priority is None


# ---- Agent Service Tests ----


class TestDialogflowServiceAgents:
    def test_list_agents(self, service, sample_agent_response):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.list().execute.return_value = {
            "agents": [sample_agent_response]
        }
        mock_agents.list_next.return_value = None

        results = service.list_agents("us-central1")
        assert len(results) == 1
        assert results[0].display_name == "test-agent"
        assert isinstance(results[0], Agent)

    def test_list_agents_empty(self, service):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.list().execute.return_value = {}
        mock_agents.list_next.return_value = None

        results = service.list_agents("us-central1")
        assert len(results) == 0

    def test_list_agents_pagination(self, service, sample_agent_response):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        second_response = sample_agent_response.copy()
        second_response["name"] = (
            "projects/test-project/locations/us-central1/agents/agent-456"
        )
        second_response["displayName"] = "test-agent-2"

        mock_agents.list().execute.return_value = {
            "agents": [sample_agent_response]
        }
        next_request = mock.MagicMock()
        next_request.execute.return_value = {
            "agents": [second_response]
        }
        mock_agents.list_next.side_effect = [next_request, None]

        results = service.list_agents("us-central1")
        assert len(results) == 2
        assert results[0].display_name == "test-agent"
        assert results[1].display_name == "test-agent-2"

    def test_get_agent(self, service, sample_agent_response):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.get().execute.return_value = sample_agent_response

        result = service.get_agent("us-central1", "agent-123")
        assert result.display_name == "test-agent"
        assert result.id == "agent-123"

    def test_get_agent_not_found(self, service):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.get().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.get_agent("us-central1", "nonexistent")

    def test_get_agent_api_error(self, service):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.get().execute.side_effect = _make_http_error(500)

        with pytest.raises(APIError):
            service.get_agent("us-central1", "agent-123")

    def test_create_agent(self, service, sample_agent_response):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.create().execute.return_value = sample_agent_response

        result = service.create_agent(
            location="us-central1",
            display_name="test-agent",
            default_language_code="en",
            time_zone="America/New_York",
            description="A test agent",
        )
        assert result.display_name == "test-agent"
        assert isinstance(result, Agent)

    def test_create_agent_minimal(self, service, sample_agent_response):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.create().execute.return_value = sample_agent_response

        result = service.create_agent(
            location="us-central1",
            display_name="test-agent",
            default_language_code="en",
            time_zone="UTC",
        )
        assert result.display_name == "test-agent"

    def test_create_agent_api_error(self, service):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.create().execute.side_effect = _make_http_error(400)

        with pytest.raises(APIError):
            service.create_agent(
                location="us-central1",
                display_name="bad",
                default_language_code="en",
                time_zone="UTC",
            )

    def test_update_agent(self, service, sample_agent_response):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.patch().execute.return_value = sample_agent_response

        result = service.update_agent(
            location="us-central1",
            agent_id="agent-123",
            update_mask="displayName,description",
            update_fields={
                "displayName": "updated-agent",
                "description": "Updated description",
            },
        )
        assert isinstance(result, Agent)

    def test_update_agent_not_found(self, service):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.patch().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.update_agent(
                location="us-central1",
                agent_id="nonexistent",
                update_mask="displayName",
                update_fields={"displayName": "new-name"},
            )

    def test_delete_agent(self, service):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.delete().execute.return_value = {}

        assert service.delete_agent("us-central1", "agent-123") is True

    def test_delete_agent_not_found(self, service):
        mock_agents = (
            service.service.projects()
            .locations()
            .agents()
        )
        mock_agents.delete().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.delete_agent("us-central1", "nonexistent")


# ---- Flow Service Tests ----


class TestDialogflowServiceFlows:
    def test_list_flows(self, service, sample_flow_response):
        mock_flows = (
            service.service.projects()
            .locations()
            .agents()
            .flows()
        )
        mock_flows.list().execute.return_value = {
            "flows": [sample_flow_response]
        }
        mock_flows.list_next.return_value = None

        results = service.list_flows("us-central1", "agent-123")
        assert len(results) == 1
        assert results[0].display_name == "test-flow"
        assert isinstance(results[0], Flow)

    def test_list_flows_empty(self, service):
        mock_flows = (
            service.service.projects()
            .locations()
            .agents()
            .flows()
        )
        mock_flows.list().execute.return_value = {}
        mock_flows.list_next.return_value = None

        results = service.list_flows("us-central1", "agent-123")
        assert len(results) == 0

    def test_get_flow(self, service, sample_flow_response):
        mock_flows = (
            service.service.projects()
            .locations()
            .agents()
            .flows()
        )
        mock_flows.get().execute.return_value = sample_flow_response

        result = service.get_flow("us-central1", "agent-123", "flow-456")
        assert result.display_name == "test-flow"
        assert result.id == "flow-456"

    def test_get_flow_not_found(self, service):
        mock_flows = (
            service.service.projects()
            .locations()
            .agents()
            .flows()
        )
        mock_flows.get().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.get_flow("us-central1", "agent-123", "nonexistent")

    def test_create_flow(self, service, sample_flow_response):
        mock_flows = (
            service.service.projects()
            .locations()
            .agents()
            .flows()
        )
        mock_flows.create().execute.return_value = sample_flow_response

        result = service.create_flow(
            location="us-central1",
            agent_id="agent-123",
            display_name="test-flow",
            description="A test flow",
        )
        assert result.display_name == "test-flow"
        assert isinstance(result, Flow)

    def test_create_flow_minimal(self, service, sample_flow_response):
        mock_flows = (
            service.service.projects()
            .locations()
            .agents()
            .flows()
        )
        mock_flows.create().execute.return_value = sample_flow_response

        result = service.create_flow(
            location="us-central1",
            agent_id="agent-123",
            display_name="test-flow",
        )
        assert result.display_name == "test-flow"

    def test_create_flow_api_error(self, service):
        mock_flows = (
            service.service.projects()
            .locations()
            .agents()
            .flows()
        )
        mock_flows.create().execute.side_effect = _make_http_error(400)

        with pytest.raises(APIError):
            service.create_flow(
                location="us-central1",
                agent_id="agent-123",
                display_name="bad",
            )

    def test_delete_flow(self, service):
        mock_flows = (
            service.service.projects()
            .locations()
            .agents()
            .flows()
        )
        mock_flows.delete().execute.return_value = {}

        assert service.delete_flow("us-central1", "agent-123", "flow-456") is True

    def test_delete_flow_not_found(self, service):
        mock_flows = (
            service.service.projects()
            .locations()
            .agents()
            .flows()
        )
        mock_flows.delete().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.delete_flow("us-central1", "agent-123", "nonexistent")


# ---- Intent Service Tests ----


class TestDialogflowServiceIntents:
    def test_list_intents(self, service, sample_intent_response):
        mock_intents = (
            service.service.projects()
            .locations()
            .agents()
            .intents()
        )
        mock_intents.list().execute.return_value = {
            "intents": [sample_intent_response]
        }
        mock_intents.list_next.return_value = None

        results = service.list_intents("us-central1", "agent-123")
        assert len(results) == 1
        assert results[0].display_name == "test-intent"
        assert isinstance(results[0], Intent)

    def test_list_intents_empty(self, service):
        mock_intents = (
            service.service.projects()
            .locations()
            .agents()
            .intents()
        )
        mock_intents.list().execute.return_value = {}
        mock_intents.list_next.return_value = None

        results = service.list_intents("us-central1", "agent-123")
        assert len(results) == 0

    def test_get_intent(self, service, sample_intent_response):
        mock_intents = (
            service.service.projects()
            .locations()
            .agents()
            .intents()
        )
        mock_intents.get().execute.return_value = sample_intent_response

        result = service.get_intent("us-central1", "agent-123", "intent-789")
        assert result.display_name == "test-intent"
        assert result.id == "intent-789"

    def test_get_intent_not_found(self, service):
        mock_intents = (
            service.service.projects()
            .locations()
            .agents()
            .intents()
        )
        mock_intents.get().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.get_intent("us-central1", "agent-123", "nonexistent")

    def test_create_intent(self, service, sample_intent_response):
        mock_intents = (
            service.service.projects()
            .locations()
            .agents()
            .intents()
        )
        mock_intents.create().execute.return_value = sample_intent_response

        result = service.create_intent(
            location="us-central1",
            agent_id="agent-123",
            display_name="test-intent",
            training_phrases=[
                {"parts": [{"text": "hello"}], "repeatCount": 1}
            ],
        )
        assert result.display_name == "test-intent"
        assert isinstance(result, Intent)

    def test_create_intent_minimal(self, service, sample_intent_response):
        mock_intents = (
            service.service.projects()
            .locations()
            .agents()
            .intents()
        )
        mock_intents.create().execute.return_value = sample_intent_response

        result = service.create_intent(
            location="us-central1",
            agent_id="agent-123",
            display_name="test-intent",
        )
        assert result.display_name == "test-intent"

    def test_create_intent_api_error(self, service):
        mock_intents = (
            service.service.projects()
            .locations()
            .agents()
            .intents()
        )
        mock_intents.create().execute.side_effect = _make_http_error(400)

        with pytest.raises(APIError):
            service.create_intent(
                location="us-central1",
                agent_id="agent-123",
                display_name="bad",
            )

    def test_delete_intent(self, service):
        mock_intents = (
            service.service.projects()
            .locations()
            .agents()
            .intents()
        )
        mock_intents.delete().execute.return_value = {}

        assert service.delete_intent(
            "us-central1", "agent-123", "intent-789"
        ) is True

    def test_delete_intent_not_found(self, service):
        mock_intents = (
            service.service.projects()
            .locations()
            .agents()
            .intents()
        )
        mock_intents.delete().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.delete_intent("us-central1", "agent-123", "nonexistent")


# ---- Session / Detect Intent Tests ----


class TestDialogflowServiceSessions:
    def test_detect_intent(self, service):
        mock_sessions = (
            service.service.projects()
            .locations()
            .agents()
            .sessions()
        )
        mock_sessions.detectIntent().execute.return_value = {
            "queryResult": {
                "text": "hello",
                "languageCode": "en",
                "responseMessages": [
                    {"text": {"text": ["Hi there!"]}}
                ],
                "match": {
                    "intent": {
                        "name": "projects/test-project/locations/us-central1/agents/agent-123/intents/intent-789",
                        "displayName": "test-intent",
                    },
                    "matchType": "INTENT",
                },
            },
        }

        result = service.detect_intent(
            location="us-central1",
            agent_id="agent-123",
            session_id="session-001",
            text="hello",
            language_code="en",
        )
        assert "queryResult" in result
        assert result["queryResult"]["text"] == "hello"

    def test_detect_intent_default_language(self, service):
        mock_sessions = (
            service.service.projects()
            .locations()
            .agents()
            .sessions()
        )
        mock_sessions.detectIntent().execute.return_value = {
            "queryResult": {"text": "hi", "languageCode": "en"},
        }

        result = service.detect_intent(
            location="us-central1",
            agent_id="agent-123",
            session_id="session-001",
            text="hi",
        )
        assert "queryResult" in result

    def test_detect_intent_not_found(self, service):
        mock_sessions = (
            service.service.projects()
            .locations()
            .agents()
            .sessions()
        )
        mock_sessions.detectIntent().execute.side_effect = _make_http_error(404)

        with pytest.raises(ResourceNotFoundError):
            service.detect_intent(
                location="us-central1",
                agent_id="nonexistent",
                session_id="session-001",
                text="hello",
            )

    def test_detect_intent_api_error(self, service):
        mock_sessions = (
            service.service.projects()
            .locations()
            .agents()
            .sessions()
        )
        mock_sessions.detectIntent().execute.side_effect = _make_http_error(500)

        with pytest.raises(APIError):
            service.detect_intent(
                location="us-central1",
                agent_id="agent-123",
                session_id="session-001",
                text="hello",
            )


# ---- Path Formatting Tests ----


class TestDialogflowServicePathFormatting:
    def test_format_parent(self, service):
        assert service._format_parent("us-central1") == (
            "projects/test-project/locations/us-central1"
        )

    def test_format_agent_name(self, service):
        assert service._format_agent_name("us-central1", "agent-123") == (
            "projects/test-project/locations/us-central1/agents/agent-123"
        )

    def test_format_agent_name_full_path(self, service):
        full_path = "projects/other/locations/eu/agents/xyz"
        assert service._format_agent_name("us-central1", full_path) == full_path

    def test_format_flow_name(self, service):
        assert service._format_flow_name(
            "us-central1", "agent-123", "flow-456"
        ) == (
            "projects/test-project/locations/us-central1/agents/agent-123/flows/flow-456"
        )

    def test_format_flow_name_full_path(self, service):
        full_path = "projects/other/locations/eu/agents/a/flows/f"
        assert (
            service._format_flow_name("us-central1", "agent-123", full_path)
            == full_path
        )

    def test_format_intent_name(self, service):
        assert service._format_intent_name(
            "us-central1", "agent-123", "intent-789"
        ) == (
            "projects/test-project/locations/us-central1/agents/agent-123/intents/intent-789"
        )

    def test_format_intent_name_full_path(self, service):
        full_path = "projects/other/locations/eu/agents/a/intents/i"
        assert (
            service._format_intent_name("us-central1", "agent-123", full_path)
            == full_path
        )

    def test_format_session_name(self, service):
        assert service._format_session_name(
            "us-central1", "agent-123", "session-001"
        ) == (
            "projects/test-project/locations/us-central1/agents/agent-123/sessions/session-001"
        )


# ---- Service Initialization Tests ----


class TestDialogflowServiceInit:
    def test_service_init(self, service):
        assert service.project_id == "test-project"
        assert service.service_name == "dialogflow"
        assert service.version == "v3"
        assert service.resource_model == Agent
