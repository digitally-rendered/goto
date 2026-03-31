"""Service implementation for Google Cloud Security Command Center."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.security_center import Finding, Source
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
)

logger = logging.getLogger(__name__)


class SecurityCenterService(GCPService[Finding]):
    """Service for interacting with Google Cloud Security Command Center."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Security Command Center service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="securitycenter",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Finding,
            **kwargs,
        )

    def list_sources(self, organization_id: str) -> List[Source]:
        """List Security Command Center sources for an organization.

        Args:
            organization_id: The organization ID to list sources for

        Returns:
            A list of Source instances
        """
        logger.info(
            "Listing SCC sources for organization %s", organization_id
        )

        request = self.service.organizations().sources().list(
            parent=f"organizations/{organization_id}"
        )

        sources = []
        while request is not None:
            response = request.execute()
            for source_data in response.get("sources", []):
                sources.append(Source.from_api_response(source_data))
            request = self.service.organizations().sources().list_next(
                request, response
            )

        logger.info("Found %s SCC sources", len(sources))
        return sources

    def get_source(self, source_name: str) -> Source:
        """Get a specific Security Command Center source.

        Args:
            source_name: The full resource name of the source
                (e.g. "organizations/123/sources/456")

        Returns:
            A Source instance

        Raises:
            ResourceNotFoundError: If the source does not exist
        """
        logger.info("Getting SCC source %s", source_name)

        try:
            request = self.service.organizations().sources().get(
                name=source_name
            )
            response = request.execute()
            return Source.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("Source", source_name)
            raise APIError(e.resp.status, str(e))

    def list_findings(
        self, source_name: str, filter_str: Optional[str] = None
    ) -> List[Finding]:
        """List findings for a source.

        Args:
            source_name: The full resource name of the source
                (e.g. "organizations/123/sources/456")
            filter_str: Optional filter expression for findings

        Returns:
            A list of Finding instances
        """
        logger.info("Listing findings for source %s", source_name)

        kwargs = {"parent": source_name}
        if filter_str:
            kwargs["filter"] = filter_str

        request = self.service.organizations().sources().findings().list(
            **kwargs
        )

        findings = []
        while request is not None:
            response = request.execute()
            for finding_data in response.get("listFindingsResults", []):
                finding_response = finding_data.get("finding", finding_data)
                findings.append(Finding.from_api_response(finding_response))
            request = (
                self.service.organizations()
                .sources()
                .findings()
                .list_next(request, response)
            )

        logger.info("Found %s findings", len(findings))
        return findings

    def get_finding(self, finding_name: str) -> Finding:
        """Get a specific finding.

        Args:
            finding_name: The full resource name of the finding

        Returns:
            A Finding instance

        Raises:
            ResourceNotFoundError: If the finding does not exist
        """
        logger.info("Getting finding %s", finding_name)

        try:
            request = (
                self.service.organizations()
                .sources()
                .findings()
                .get(name=finding_name)
            )
            response = request.execute()
            return Finding.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("Finding", finding_name)
            raise APIError(e.resp.status, str(e))

    def set_finding_state(self, finding_name: str, state: str) -> Finding:
        """Set the state of a finding.

        Args:
            finding_name: The full resource name of the finding
            state: The new state (ACTIVE or INACTIVE)

        Returns:
            The updated Finding instance

        Raises:
            ResourceNotFoundError: If the finding does not exist
            APIError: If the API call fails
        """
        logger.info("Setting finding %s state to %s", finding_name, state)

        try:
            body = {"state": state}
            request = (
                self.service.organizations()
                .sources()
                .findings()
                .setState(name=finding_name, body=body)
            )
            response = request.execute()
            return Finding.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("Finding", finding_name)
            raise APIError(e.resp.status, str(e))

    def update_security_marks(
        self, finding_name: str, marks: Dict[str, str]
    ) -> Finding:
        """Update security marks on a finding.

        Args:
            finding_name: The full resource name of the finding
            marks: Dictionary of security marks to set

        Returns:
            The updated Finding instance

        Raises:
            ResourceNotFoundError: If the finding does not exist
            APIError: If the API call fails
        """
        logger.info("Updating security marks on finding %s", finding_name)

        try:
            body = {"securityMarks": {"marks": marks}}
            request = (
                self.service.organizations()
                .sources()
                .findings()
                .updateSecurityMarks(
                    name=f"{finding_name}/securityMarks", body=body
                )
            )
            response = request.execute()
            return Finding.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("Finding", finding_name)
            raise APIError(e.resp.status, str(e))

    def create_source(
        self,
        organization_id: str,
        display_name: str,
        description: Optional[str] = None,
    ) -> Source:
        """Create a new Security Command Center source.

        Args:
            organization_id: The organization ID to create the source in
            display_name: The display name for the source
            description: Optional description for the source

        Returns:
            The created Source instance

        Raises:
            APIError: If the API call fails
        """
        logger.info(
            "Creating SCC source %s in organization %s",
            display_name,
            organization_id,
        )

        body = {"displayName": display_name}
        if description:
            body["description"] = description

        try:
            request = self.service.organizations().sources().create(
                parent=f"organizations/{organization_id}", body=body
            )
            response = request.execute()
            logger.info("Created SCC source %s", display_name)
            return Source.from_api_response(response)
        except HttpError as e:
            raise APIError(e.resp.status, str(e))
