"""Service implementation for Google Cloud Profiler."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.profiler import Profile

logger = logging.getLogger(__name__)

class ProfilerService(GCPService[Profile]):
    """Service for interacting with Google Cloud Profiler."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Profiler service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="cloudprofiler",
            version="v2",
            credentials_file=credentials_file,
            resource_model=Profile,
            **kwargs,
        )

    def create_profile(
        self,
        deployment: Dict[str, Any],
        profile_type: str,
    ) -> Profile:
        """Create a new online profile.

        The API will return a profile with a token that the agent uses
        to upload profile data.

        Args:
            deployment: Deployment information for the profile.
            profile_type: The type of profile (CPU, HEAP, THREADS, CONTENTION, WALL).

        Returns:
            The newly created Profile instance.
        """
        logger.debug(
            "Creating profile of type %s for project %s",
            profile_type,
            self.project_id,
        )

        parent = f"projects/{self.project_id}"
        body: Dict[str, Any] = {
            "deployment": deployment,
            "profileType": [profile_type],
        }

        request = self.service.projects().profiles().create(
            parent=parent, body=body
        )
        response = self._execute(request)

        return Profile.from_api_response(response)

    def create_offline_profile(
        self,
        deployment: Dict[str, Any],
        profile_type: str,
        profile_bytes: str,
    ) -> Profile:
        """Create an offline profile for data that has already been collected.

        Args:
            deployment: Deployment information for the profile.
            profile_type: The type of profile (CPU, HEAP, THREADS, CONTENTION, WALL).
            profile_bytes: Base64-encoded profile data.

        Returns:
            The newly created Profile instance.
        """
        logger.debug(
            "Creating offline profile of type %s for project %s",
            profile_type,
            self.project_id,
        )

        parent = f"projects/{self.project_id}"
        body: Dict[str, Any] = {
            "deployment": deployment,
            "profileType": profile_type,
            "profileBytes": profile_bytes,
        }

        request = self.service.projects().profiles().createOffline(
            parent=parent, body=body
        )
        response = self._execute(request)

        return Profile.from_api_response(response)

    def update_profile(
        self,
        profile_name: str,
        profile_bytes: str,
    ) -> Profile:
        """Update a profile with collected data.

        Args:
            profile_name: The resource name of the profile to update.
            profile_bytes: Base64-encoded profile data.

        Returns:
            The updated Profile instance.
        """
        if "/" not in profile_name:
            name = f"projects/{self.project_id}/profiles/{profile_name}"
        else:
            name = profile_name

        logger.debug("Updating profile %s", name)

        body: Dict[str, Any] = {
            "profileBytes": profile_bytes,
        }

        request = self.service.projects().profiles().patch(
            name=name, body=body
        )
        response = self._execute(request)

        return Profile.from_api_response(response)

    def list_profiles(
        self,
        deployment: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[Profile]:
        """List profiles for the project.

        Args:
            deployment: Optional deployment to filter profiles by.
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of Profile instances.
        """
        logger.debug("Listing profiles for project %s", self.project_id)

        parent = f"projects/{self.project_id}"
        params: Dict[str, Any] = {"parent": parent}
        params.update(kwargs)

        profiles = []
        request = self.service.projects().profiles().list(**params)
        while request is not None:
            response = self._execute(request)
            for item in response.get("profiles", []):
                if deployment is not None:
                    item_deployment = item.get("deployment", {})
                    if item_deployment.get("target") != deployment.get("target"):
                        continue
                profiles.append(Profile.from_api_response(item))
            request = (
                self.service.projects()
                .profiles()
                .list_next(request, response)
            )

        return profiles
