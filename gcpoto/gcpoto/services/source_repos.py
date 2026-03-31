"""Service implementation for Google Cloud Source Repositories."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.source_repos import Repo
from gcpoto.exceptions import (
    APIError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


class SourceReposService(GCPService[Repo]):
    """Service for interacting with Google Cloud Source Repositories."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Source Repositories service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="sourcerepo",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Repo,
            **kwargs,
        )

    def list_repos(self) -> List[Repo]:
        """List Cloud Source Repositories.

        Returns:
            A list of Repo instances
        """
        logger.info(
            "Listing source repositories for project %s", self.project_id
        )

        parent = f"projects/{self.project_id}"
        request = self.service.projects().repos().list(name=parent)

        repos = []
        while request is not None:
            response = self._execute(request)
            for repo_data in response.get("repos", []):
                repos.append(Repo.from_api_response(repo_data))
            request = self.service.projects().repos().list_next(
                request, response
            )

        logger.info("Found %s repositories", len(repos))
        return repos

    def get_repo(self, repo_name: str) -> Repo:
        """Get a specific Cloud Source Repository.

        Args:
            repo_name: The name of the repository

        Returns:
            A Repo instance

        Raises:
            ResourceNotFoundError: If the repository does not exist
        """
        logger.info("Getting repository %s", repo_name)

        name = f"projects/{self.project_id}/repos/{repo_name}"

        request = self.service.projects().repos().get(name=name)
        response = self._execute(request, "Repo", repo_name)
        return Repo.from_api_response(response)
    def create_repo(self, repo_name: str) -> Repo:
        """Create a Cloud Source Repository.

        Args:
            repo_name: The name for the repository

        Returns:
            The created Repo instance

        Raises:
            APIError: If the API call fails
        """
        logger.info("Creating repository %s", repo_name)

        parent = f"projects/{self.project_id}"
        body = {
            "name": f"projects/{self.project_id}/repos/{repo_name}",
        }

        request = self.service.projects().repos().create(
            parent=parent, body=body
        )
        response = self._execute(request)
        logger.info("Created repository %s", repo_name)
        return Repo.from_api_response(response)
    def delete_repo(self, repo_name: str) -> bool:
        """Delete a Cloud Source Repository.

        Args:
            repo_name: The name of the repository to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the repository does not exist
            APIError: If the API call fails
        """
        logger.info("Deleting repository %s", repo_name)

        name = f"projects/{self.project_id}/repos/{repo_name}"

        self.service.projects().repos().delete(name=name).execute()
        logger.info("Deleted repository %s", repo_name)
        return True
    def get_iam_policy(self, repo_name: str) -> Dict[str, Any]:
        """Get the IAM policy for a repository.

        Args:
            repo_name: The name of the repository

        Returns:
            The IAM policy dictionary

        Raises:
            ResourceNotFoundError: If the repository does not exist
            APIError: If the API call fails
        """
        logger.info("Getting IAM policy for repository %s", repo_name)

        resource = f"projects/{self.project_id}/repos/{repo_name}"

        request = self.service.projects().repos().getIamPolicy(
            resource=resource
        )
        response = self._execute(request, "Repo", repo_name)
        return response
    def set_iam_policy(
        self, repo_name: str, policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set the IAM policy for a repository.

        Args:
            repo_name: The name of the repository
            policy: The IAM policy to set

        Returns:
            The updated IAM policy dictionary

        Raises:
            ResourceNotFoundError: If the repository does not exist
            APIError: If the API call fails
        """
        logger.info("Setting IAM policy for repository %s", repo_name)

        resource = f"projects/{self.project_id}/repos/{repo_name}"
        body = {"policy": policy}

        request = self.service.projects().repos().setIamPolicy(
            resource=resource, body=body
        )
        response = self._execute(request, "Repo", repo_name)
        logger.info("Updated IAM policy for repository %s", repo_name)
        return response