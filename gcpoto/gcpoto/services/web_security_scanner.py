"""Service implementation for Google Cloud Web Security Scanner."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.web_security_scanner import ScanConfig, ScanRun
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
)

logger = logging.getLogger(__name__)


class WebSecurityScannerService(GCPService[ScanConfig]):
    """Service for interacting with Google Cloud Web Security Scanner."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Web Security Scanner service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="websecurityscanner",
            version="v1",
            credentials_file=credentials_file,
            resource_model=ScanConfig,
            **kwargs,
        )

    def list_scan_configs(self) -> List[ScanConfig]:
        """List all scan configs in the project.

        Returns:
            A list of ScanConfig instances
        """
        logger.info(
            "Listing scan configs for project %s", self.project_id
        )

        request = self.service.projects().scanConfigs().list(
            parent=f"projects/{self.project_id}"
        )

        configs = []
        while request is not None:
            response = request.execute()
            for config_data in response.get("scanConfigs", []):
                configs.append(ScanConfig.from_api_response(config_data))
            request = self.service.projects().scanConfigs().list_next(
                request, response
            )

        logger.info("Found %s scan configs", len(configs))
        return configs

    def get_scan_config(self, config_id: str) -> ScanConfig:
        """Get a specific scan config.

        Args:
            config_id: The scan config ID

        Returns:
            A ScanConfig instance

        Raises:
            ResourceNotFoundError: If the scan config does not exist
        """
        logger.info("Getting scan config %s", config_id)

        try:
            request = self.service.projects().scanConfigs().get(
                name=f"projects/{self.project_id}/scanConfigs/{config_id}"
            )
            response = request.execute()
            return ScanConfig.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ScanConfig", config_id)
            raise APIError(e.resp.status, str(e))

    def create_scan_config(
        self,
        display_name: str,
        starting_urls: List[str],
        max_qps: Optional[int] = None,
        authentication: Optional[Dict[str, Any]] = None,
        schedule: Optional[Dict[str, Any]] = None,
    ) -> ScanConfig:
        """Create a new scan config.

        Args:
            display_name: The display name for the scan config
            starting_urls: The starting URLs for the scan
            max_qps: Optional maximum queries per second
            authentication: Optional authentication configuration
            schedule: Optional schedule configuration

        Returns:
            The created ScanConfig instance

        Raises:
            APIError: If the API call fails
        """
        logger.info("Creating scan config %s", display_name)

        body: Dict[str, Any] = {
            "displayName": display_name,
            "startingUrls": starting_urls,
        }
        if max_qps is not None:
            body["maxQps"] = max_qps
        if authentication is not None:
            body["authentication"] = authentication
        if schedule is not None:
            body["schedule"] = schedule

        try:
            request = self.service.projects().scanConfigs().create(
                parent=f"projects/{self.project_id}",
                body=body,
            )
            response = request.execute()
            logger.info("Created scan config %s", display_name)
            return ScanConfig.from_api_response(response)
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

    def update_scan_config(
        self,
        config_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> ScanConfig:
        """Update an existing scan config.

        Args:
            config_id: The scan config ID to update
            update_mask: Comma-separated list of fields to update
            update_fields: The fields to update

        Returns:
            The updated ScanConfig instance

        Raises:
            ResourceNotFoundError: If the scan config does not exist
            APIError: If the API call fails
        """
        logger.info("Updating scan config %s", config_id)

        try:
            request = self.service.projects().scanConfigs().patch(
                name=f"projects/{self.project_id}/scanConfigs/{config_id}",
                updateMask=update_mask,
                body=update_fields,
            )
            response = request.execute()
            logger.info("Updated scan config %s", config_id)
            return ScanConfig.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ScanConfig", config_id)
            raise APIError(e.resp.status, str(e))

    def delete_scan_config(self, config_id: str) -> bool:
        """Delete a scan config.

        Args:
            config_id: The scan config ID to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the scan config does not exist
            APIError: If the API call fails
        """
        logger.info("Deleting scan config %s", config_id)

        try:
            self.service.projects().scanConfigs().delete(
                name=f"projects/{self.project_id}/scanConfigs/{config_id}"
            ).execute()
            logger.info("Deleted scan config %s", config_id)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ScanConfig", config_id)
            raise APIError(e.resp.status, str(e))

    def start_scan(self, config_id: str) -> ScanRun:
        """Start a new scan run for a scan config.

        Args:
            config_id: The scan config ID to start a scan for

        Returns:
            The started ScanRun instance

        Raises:
            ResourceNotFoundError: If the scan config does not exist
            APIError: If the API call fails
        """
        logger.info("Starting scan for config %s", config_id)

        try:
            request = self.service.projects().scanConfigs().start(
                name=f"projects/{self.project_id}/scanConfigs/{config_id}",
                body={},
            )
            response = request.execute()
            logger.info("Started scan for config %s", config_id)
            return ScanRun.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ScanConfig", config_id)
            raise APIError(e.resp.status, str(e))

    def list_scan_runs(self, config_id: str) -> List[ScanRun]:
        """List scan runs for a scan config.

        Args:
            config_id: The scan config ID

        Returns:
            A list of ScanRun instances
        """
        logger.info("Listing scan runs for config %s", config_id)

        request = self.service.projects().scanConfigs().scanRuns().list(
            parent=f"projects/{self.project_id}/scanConfigs/{config_id}"
        )

        runs = []
        while request is not None:
            response = request.execute()
            for run_data in response.get("scanRuns", []):
                runs.append(ScanRun.from_api_response(run_data))
            request = (
                self.service.projects()
                .scanConfigs()
                .scanRuns()
                .list_next(request, response)
            )

        logger.info("Found %s scan runs", len(runs))
        return runs

    def get_scan_run(self, config_id: str, run_id: str) -> ScanRun:
        """Get a specific scan run.

        Args:
            config_id: The scan config ID
            run_id: The scan run ID

        Returns:
            A ScanRun instance

        Raises:
            ResourceNotFoundError: If the scan run does not exist
        """
        logger.info("Getting scan run %s for config %s", run_id, config_id)

        try:
            request = (
                self.service.projects()
                .scanConfigs()
                .scanRuns()
                .get(
                    name=f"projects/{self.project_id}/scanConfigs/{config_id}/scanRuns/{run_id}"
                )
            )
            response = request.execute()
            return ScanRun.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ScanRun", run_id)
            raise APIError(e.resp.status, str(e))

    def list_findings_for_run(
        self,
        config_id: str,
        run_id: str,
        filter_str: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List findings for a scan run.

        Args:
            config_id: The scan config ID
            run_id: The scan run ID
            filter_str: Optional filter expression for findings

        Returns:
            A list of finding dictionaries
        """
        logger.info(
            "Listing findings for scan run %s in config %s",
            run_id,
            config_id,
        )

        kwargs: Dict[str, Any] = {
            "parent": f"projects/{self.project_id}/scanConfigs/{config_id}/scanRuns/{run_id}"
        }
        if filter_str:
            kwargs["filter"] = filter_str

        request = (
            self.service.projects()
            .scanConfigs()
            .scanRuns()
            .findings()
            .list(**kwargs)
        )

        findings = []
        while request is not None:
            response = request.execute()
            for finding_data in response.get("findings", []):
                findings.append(finding_data)
            request = (
                self.service.projects()
                .scanConfigs()
                .scanRuns()
                .findings()
                .list_next(request, response)
            )

        logger.info("Found %s findings", len(findings))
        return findings
