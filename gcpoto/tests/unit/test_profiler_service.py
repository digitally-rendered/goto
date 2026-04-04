"""Tests for Cloud Profiler service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.profiler import ProfilerService
from gcpoto.models.profiler import Profile
from gcpoto.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().profiles() chain
        mock_profiles = mock.MagicMock()
        mock_service.projects.return_value.profiles.return_value = mock_profiles

        yield mock_service


@pytest.fixture
def sample_profile_response():
    """Sample Cloud Profiler profile API response."""
    return {
        "name": "projects/test-project/profiles/prof-001",
        "profileType": "CPU",
        "deployment": {
            "projectId": "test-project",
            "target": "my-service",
            "labels": {"zone": "us-central1-a"},
        },
        "duration": "10s",
        "profileBytes": "base64encodeddata==",
        "labels": {"env": "production"},
    }


# ---- Model Tests ----


class TestProfileModel:
    def test_from_api_response(self, sample_profile_response):
        """Test creating a Profile from an API response."""
        profile = Profile.from_api_response(sample_profile_response)

        assert profile.name == "prof-001"
        assert profile.id == "projects/test-project/profiles/prof-001"
        assert profile.project == "test-project"
        assert profile.profile_type == "CPU"
        assert profile.type == "cloudprofiler.profile"
        assert profile.deployment["target"] == "my-service"
        assert profile.duration == "10s"
        assert profile.profile_bytes == "base64encodeddata=="

    def test_from_api_response_minimal(self):
        """Test creating a Profile from a minimal API response."""
        profile = Profile.from_api_response({})

        assert profile.name == ""
        assert profile.profile_type == ""
        assert profile.deployment is None
        assert profile.duration is None
        assert profile.profile_bytes is None

    def test_get_tag(self, sample_profile_response):
        """Test get_tag on Profile."""
        profile = Profile.from_api_response(sample_profile_response)

        assert profile.get_tag("env") == "production"
        assert profile.get_tag("missing", "default") == "default"


# ---- Service Init ----


class TestProfilerServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the ProfilerService."""
        from googleapiclient.discovery import build

        service = ProfilerService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "cloudprofiler"
        assert service.version == "v2"
        build.assert_called_once_with("cloudprofiler", "v2", credentials=None)


# ---- Create Profile ----


class TestCreateProfile:
    def test_create_profile(self, mock_google_client, sample_profile_response):
        """Test creating an online profile."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.profiles.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_profile_response

        service = ProfilerService(project_id="test-project")
        deployment = {"projectId": "test-project", "target": "my-service"}
        profile = service.create_profile(
            deployment=deployment, profile_type="CPU"
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "deployment": deployment,
                "profileType": ["CPU"],
            },
        )

        assert isinstance(profile, Profile)
        assert profile.profile_type == "CPU"


# ---- Create Offline Profile ----


class TestCreateOfflineProfile:
    def test_create_offline_profile(
        self, mock_google_client, sample_profile_response
    ):
        """Test creating an offline profile."""
        mock_request = mock.MagicMock()
        mock_create_offline = (
            mock_google_client.projects.return_value.profiles.return_value.createOffline
        )
        mock_create_offline.return_value = mock_request
        mock_request.execute.return_value = sample_profile_response

        service = ProfilerService(project_id="test-project")
        deployment = {"projectId": "test-project", "target": "my-service"}
        profile = service.create_offline_profile(
            deployment=deployment,
            profile_type="CPU",
            profile_bytes="base64data==",
        )

        mock_create_offline.assert_called_once_with(
            parent="projects/test-project",
            body={
                "deployment": deployment,
                "profileType": "CPU",
                "profileBytes": "base64data==",
            },
        )

        assert isinstance(profile, Profile)
        assert profile.profile_type == "CPU"


# ---- Update Profile ----


class TestUpdateProfile:
    def test_update_profile(self, mock_google_client, sample_profile_response):
        """Test updating a profile with collected data."""
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.profiles.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_profile_response

        service = ProfilerService(project_id="test-project")
        profile = service.update_profile(
            profile_name="prof-001",
            profile_bytes="newbase64data==",
        )

        mock_patch.assert_called_once_with(
            name="projects/test-project/profiles/prof-001",
            body={"profileBytes": "newbase64data=="},
        )

        assert isinstance(profile, Profile)

    def test_update_profile_full_path(
        self, mock_google_client, sample_profile_response
    ):
        """Test updating a profile with a full resource name."""
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.profiles.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_profile_response

        service = ProfilerService(project_id="test-project")
        service.update_profile(
            profile_name="projects/test-project/profiles/prof-001",
            profile_bytes="newbase64data==",
        )

        mock_patch.assert_called_with(
            name="projects/test-project/profiles/prof-001",
            body={"profileBytes": "newbase64data=="},
        )


# ---- List Profiles ----


class TestListProfiles:
    def test_list_profiles(self, mock_google_client, sample_profile_response):
        """Test listing profiles."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.profiles.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "profiles": [sample_profile_response]
        }
        mock_list_next = (
            mock_google_client.projects.return_value.profiles.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ProfilerService(project_id="test-project")
        profiles = service.list_profiles()

        mock_list.assert_called_once_with(parent="projects/test-project")

        assert len(profiles) == 1
        assert isinstance(profiles[0], Profile)
        assert profiles[0].profile_type == "CPU"

    def test_list_profiles_empty(self, mock_google_client):
        """Test listing profiles when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.profiles.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_list_next = (
            mock_google_client.projects.return_value.profiles.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ProfilerService(project_id="test-project")
        profiles = service.list_profiles()

        assert profiles == []

    def test_list_profiles_with_deployment_filter(
        self, mock_google_client, sample_profile_response
    ):
        """Test listing profiles filtered by deployment."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.profiles.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "profiles": [sample_profile_response]
        }
        mock_list_next = (
            mock_google_client.projects.return_value.profiles.return_value.list_next
        )
        mock_list_next.return_value = None

        service = ProfilerService(project_id="test-project")
        profiles = service.list_profiles(
            deployment={"target": "my-service"}
        )

        assert len(profiles) == 1
        assert profiles[0].deployment["target"] == "my-service"
