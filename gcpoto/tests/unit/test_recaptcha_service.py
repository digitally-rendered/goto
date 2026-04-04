"""Tests for the reCAPTCHA Enterprise service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.recaptcha import RecaptchaService
from gcpoto.models.recaptcha import RecaptchaKey, Assessment
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
)


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_service


@pytest.fixture
def sample_recaptcha_key_response():
    """Sample reCAPTCHA key response."""
    return {
        "name": "projects/test-project/keys/recaptcha-key-123",
        "displayName": "My Website Key",
        "webSettings": {
            "allowAllDomains": False,
            "allowedDomains": ["example.com", "www.example.com"],
            "integrationType": "SCORE",
        },
        "labels": {"env": "test", "team": "security"},
        "project": "test-project",
        "createTime": "2024-06-01T10:00:00.000Z",
        "updateTime": "2024-06-01T12:00:00.000Z",
    }


@pytest.fixture
def sample_assessment_response():
    """Sample assessment response."""
    return {
        "name": "projects/test-project/assessments/assessment-abc-123",
        "event": {
            "token": "token-xyz",
            "siteKey": "recaptcha-key-123",
            "userAgent": "Mozilla/5.0",
            "userIpAddress": "192.168.1.1",
            "expectedAction": "login",
        },
        "tokenProperties": {
            "valid": True,
            "hostname": "example.com",
            "action": "login",
            "createTime": "2024-06-01T10:00:00.000Z",
        },
        "riskAnalysis": {
            "score": 0.9,
            "reasons": [],
        },
        "project": "test-project",
    }


@pytest.fixture
def service(mock_google_client):
    """Create a RecaptchaService instance with mocked API client."""
    return RecaptchaService(project_id="test-project")


# ------------------------------------------------------------------ #
#  Service init
# ------------------------------------------------------------------ #


class TestRecaptchaServiceInit:
    """Tests for RecaptchaService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the reCAPTCHA Enterprise service."""
        from googleapiclient.discovery import build

        svc = RecaptchaService(project_id="test-project")

        assert svc.project_id == "test-project"
        assert svc.service_name == "recaptchaenterprise"
        assert svc.version == "v1"
        build.assert_called_once_with(
            "recaptchaenterprise", "v1", credentials=None
        )

    def test_init_with_credentials(self, mock_google_client):
        """Test initializing with credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            svc = RecaptchaService(
                project_id="test-project",
                credentials_file="/path/to/creds.json",
            )
            assert svc.project_id == "test-project"
            mock_creds.assert_called_once()


# ------------------------------------------------------------------ #
#  Key operations
# ------------------------------------------------------------------ #


class TestListKeys:
    """Tests for listing reCAPTCHA keys."""

    def test_list_keys(self, service, sample_recaptcha_key_response):
        """Test listing reCAPTCHA keys."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.list.return_value = mock_request
        mock_request.execute.return_value = {
            "keys": [sample_recaptcha_key_response]
        }
        mock_keys.list_next.return_value = None

        keys = service.list_keys()

        mock_keys.list.assert_called_once_with(
            parent="projects/test-project"
        )
        assert len(keys) == 1
        assert isinstance(keys[0], RecaptchaKey)
        assert keys[0].display_name == "My Website Key"

    def test_list_keys_empty(self, service):
        """Test listing keys when none exist."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.list.return_value = mock_request
        mock_request.execute.return_value = {"keys": []}
        mock_keys.list_next.return_value = None

        keys = service.list_keys()
        assert len(keys) == 0

    def test_list_keys_pagination(
        self, service, sample_recaptcha_key_response
    ):
        """Test listing keys with pagination."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_keys.list.return_value = mock_request_page1
        mock_request_page1.execute.return_value = {
            "keys": [sample_recaptcha_key_response]
        }

        second_key = dict(sample_recaptcha_key_response)
        second_key["name"] = "projects/test-project/keys/recaptcha-key-456"
        second_key["displayName"] = "Mobile Key"
        mock_request_page2.execute.return_value = {
            "keys": [second_key]
        }

        mock_keys.list_next.side_effect = [mock_request_page2, None]

        keys = service.list_keys()
        assert len(keys) == 2


class TestGetKey:
    """Tests for getting a reCAPTCHA key."""

    def test_get_key(self, service, sample_recaptcha_key_response):
        """Test getting a specific reCAPTCHA key."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.get.return_value = mock_request
        mock_request.execute.return_value = sample_recaptcha_key_response

        key = service.get_key("recaptcha-key-123")

        mock_keys.get.assert_called_once_with(
            name="projects/test-project/keys/recaptcha-key-123"
        )
        assert isinstance(key, RecaptchaKey)
        assert key.display_name == "My Website Key"
        assert key.web_settings is not None

    def test_get_key_not_found(self, service):
        """Test getting a key that does not exist."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_key("nonexistent")

    def test_get_key_api_error(self, service):
        """Test getting a key with an API error."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_key("recaptcha-key-123")


class TestCreateKey:
    """Tests for creating a reCAPTCHA key."""

    def test_create_key_web(self, service, sample_recaptcha_key_response):
        """Test creating a web reCAPTCHA key."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.create.return_value = mock_request
        mock_request.execute.return_value = sample_recaptcha_key_response

        web_settings = {
            "allowedDomains": ["example.com"],
            "integrationType": "SCORE",
        }

        key = service.create_key(
            display_name="My Website Key",
            web_settings=web_settings,
            labels={"env": "test"},
        )

        mock_keys.create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "displayName": "My Website Key",
                "webSettings": web_settings,
                "labels": {"env": "test"},
            },
        )
        assert isinstance(key, RecaptchaKey)
        assert key.display_name == "My Website Key"

    def test_create_key_android(self, service, sample_recaptcha_key_response):
        """Test creating an Android reCAPTCHA key."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.create.return_value = mock_request
        android_response = dict(sample_recaptcha_key_response)
        android_response["androidSettings"] = {
            "allowedPackageNames": ["com.example.app"]
        }
        android_response["webSettings"] = None
        mock_request.execute.return_value = android_response

        android_settings = {
            "allowedPackageNames": ["com.example.app"]
        }

        service.create_key(
            display_name="My Android Key",
            android_settings=android_settings,
        )

        mock_keys.create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "displayName": "My Android Key",
                "androidSettings": android_settings,
            },
        )

    def test_create_key_ios(self, service, sample_recaptcha_key_response):
        """Test creating an iOS reCAPTCHA key."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.create.return_value = mock_request
        ios_response = dict(sample_recaptcha_key_response)
        ios_response["iosSettings"] = {
            "allowedBundleIds": ["com.example.app"]
        }
        ios_response["webSettings"] = None
        mock_request.execute.return_value = ios_response

        ios_settings = {
            "allowedBundleIds": ["com.example.app"]
        }

        service.create_key(
            display_name="My iOS Key",
            ios_settings=ios_settings,
        )

        mock_keys.create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "displayName": "My iOS Key",
                "iosSettings": ios_settings,
            },
        )

    def test_create_key_minimal(self, service, sample_recaptcha_key_response):
        """Test creating a key with minimal parameters."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.create.return_value = mock_request
        mock_request.execute.return_value = sample_recaptcha_key_response

        service.create_key(display_name="Simple Key")

        mock_keys.create.assert_called_once_with(
            parent="projects/test-project",
            body={"displayName": "Simple Key"},
        )

    def test_create_key_api_error(self, service):
        """Test creating a key with an API error."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_key(display_name="Test Key")


class TestUpdateKey:
    """Tests for updating a reCAPTCHA key."""

    def test_update_key(self, service, sample_recaptcha_key_response):
        """Test updating a reCAPTCHA key."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.patch.return_value = mock_request
        updated_response = dict(sample_recaptcha_key_response)
        updated_response["displayName"] = "Updated Key"
        mock_request.execute.return_value = updated_response

        key = service.update_key(
            key_id="recaptcha-key-123",
            update_mask="displayName",
            update_fields={"displayName": "Updated Key"},
        )

        mock_keys.patch.assert_called_once_with(
            name="projects/test-project/keys/recaptcha-key-123",
            updateMask="displayName",
            body={"displayName": "Updated Key"},
        )
        assert isinstance(key, RecaptchaKey)

    def test_update_key_not_found(self, service):
        """Test updating a key that does not exist."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_key(
                key_id="nonexistent",
                update_mask="displayName",
                update_fields={"displayName": "Test"},
            )

    def test_update_key_api_error(self, service):
        """Test updating a key with an API error."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.update_key(
                key_id="recaptcha-key-123",
                update_mask="displayName",
                update_fields={"displayName": "Test"},
            )


class TestDeleteKey:
    """Tests for deleting a reCAPTCHA key."""

    def test_delete_key(self, service):
        """Test deleting a reCAPTCHA key."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_key("recaptcha-key-123")

        mock_keys.delete.assert_called_once_with(
            name="projects/test-project/keys/recaptcha-key-123"
        )
        assert result is True

    def test_delete_key_not_found(self, service):
        """Test deleting a key that does not exist."""
        mock_keys = (
            service.service.projects.return_value.keys.return_value
        )
        mock_request = mock.MagicMock()
        mock_keys.delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_key("nonexistent")


# ------------------------------------------------------------------ #
#  Assessment operations
# ------------------------------------------------------------------ #


class TestCreateAssessment:
    """Tests for creating assessments."""

    def test_create_assessment(self, service, sample_assessment_response):
        """Test creating a reCAPTCHA assessment."""
        mock_assessments = (
            service.service.projects.return_value
            .assessments.return_value
        )
        mock_request = mock.MagicMock()
        mock_assessments.create.return_value = mock_request
        mock_request.execute.return_value = sample_assessment_response

        event = {
            "token": "token-xyz",
            "siteKey": "recaptcha-key-123",
            "expectedAction": "login",
        }

        assessment = service.create_assessment(event)

        mock_assessments.create.assert_called_once_with(
            parent="projects/test-project",
            body={"event": event},
        )
        assert isinstance(assessment, Assessment)
        assert assessment.risk_analysis is not None
        assert assessment.risk_analysis["score"] == 0.9
        assert assessment.token_properties["valid"] is True
        assert assessment.event["token"] == "token-xyz"

    def test_create_assessment_invalid_token(
        self, service
    ):
        """Test creating an assessment with an invalid token."""
        mock_assessments = (
            service.service.projects.return_value
            .assessments.return_value
        )
        mock_request = mock.MagicMock()
        mock_assessments.create.return_value = mock_request
        mock_request.execute.return_value = {
            "name": "projects/test-project/assessments/assessment-def-456",
            "event": {
                "token": "invalid-token",
                "siteKey": "recaptcha-key-123",
            },
            "tokenProperties": {
                "valid": False,
                "invalidReason": "EXPIRED",
            },
            "riskAnalysis": {
                "score": 0.0,
                "reasons": ["AUTOMATION"],
            },
            "project": "test-project",
        }

        event = {
            "token": "invalid-token",
            "siteKey": "recaptcha-key-123",
        }

        assessment = service.create_assessment(event)

        assert isinstance(assessment, Assessment)
        assert assessment.token_properties["valid"] is False
        assert assessment.risk_analysis["score"] == 0.0

    def test_create_assessment_api_error(self, service):
        """Test creating an assessment with an API error."""
        mock_assessments = (
            service.service.projects.return_value
            .assessments.return_value
        )
        mock_request = mock.MagicMock()
        mock_assessments.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_assessment({"token": "bad"})


# ------------------------------------------------------------------ #
#  Model tests
# ------------------------------------------------------------------ #


class TestRecaptchaKeyModel:
    """Tests for the RecaptchaKey model."""

    def test_from_api_response(self, sample_recaptcha_key_response):
        """Test creating a RecaptchaKey from an API response."""
        key = RecaptchaKey.from_api_response(sample_recaptcha_key_response)

        assert key.id == "recaptcha-key-123"
        assert key.name == "projects/test-project/keys/recaptcha-key-123"
        assert key.type == "recaptcha.key"
        assert key.display_name == "My Website Key"
        assert key.web_settings is not None
        assert key.web_settings["integrationType"] == "SCORE"
        assert key.android_settings is None
        assert key.ios_settings is None
        assert key.labels == {"env": "test", "team": "security"}

    def test_from_api_response_minimal(self):
        """Test creating a RecaptchaKey from a minimal response."""
        key = RecaptchaKey.from_api_response({"name": "simple-key"})

        assert key.id == "simple-key"
        assert key.name == "simple-key"
        assert key.display_name == ""
        assert key.web_settings is None
        assert key.android_settings is None
        assert key.ios_settings is None

    def test_get_tag(self, sample_recaptcha_key_response):
        """Test the get_tag method."""
        key = RecaptchaKey.from_api_response(sample_recaptcha_key_response)

        assert key.get_tag("env") == "test"
        assert key.get_tag("team") == "security"
        assert key.get_tag("missing") == ""
        assert key.get_tag("missing", "default") == "default"


class TestAssessmentModel:
    """Tests for the Assessment model."""

    def test_from_api_response(self, sample_assessment_response):
        """Test creating an Assessment from an API response."""
        assessment = Assessment.from_api_response(
            sample_assessment_response
        )

        assert assessment.id == "assessment-abc-123"
        assert assessment.name == (
            "projects/test-project/assessments/assessment-abc-123"
        )
        assert assessment.type == "recaptcha.assessment"
        assert assessment.token_properties is not None
        assert assessment.token_properties["valid"] is True
        assert assessment.risk_analysis is not None
        assert assessment.risk_analysis["score"] == 0.9
        assert assessment.event is not None
        assert assessment.event["token"] == "token-xyz"

    def test_from_api_response_minimal(self):
        """Test creating an Assessment from a minimal response."""
        assessment = Assessment.from_api_response({"name": "simple-assessment"})

        assert assessment.id == "simple-assessment"
        assert assessment.name == "simple-assessment"
        assert assessment.token_properties is None
        assert assessment.risk_analysis is None
        assert assessment.event is None
