"""Models for Google Cloud Web Security Scanner resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.web_security_scanner import get_schema


class ScanConfig(GCPResource):
    """Model for a Web Security Scanner Scan Config."""

    display_name: str = Field("", description="The display name of the scan config")
    starting_urls: List[str] = Field(
        default_factory=list, description="The starting URLs for the scan"
    )
    max_qps: Optional[int] = Field(
        None, description="Maximum queries per second during scanning"
    )
    authentication: Optional[Dict[str, Any]] = Field(
        None, description="Authentication configuration"
    )
    user_agent: Optional[str] = Field(
        None, description="The user agent string for the scanner"
    )
    blacklist_patterns: Optional[List[str]] = Field(
        None, description="URL patterns to exclude from the scan"
    )
    schedule: Optional[Dict[str, Any]] = Field(
        None, description="The schedule for automatic scanning"
    )
    target_platforms: Optional[List[str]] = Field(
        None, description="Target platforms for the scan"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("scan_config")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "ScanConfig":
        """Create a ScanConfig from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ScanConfig instance
        """
        return cls(
            id=response.get("name", "").split("/")[-1]
            if response.get("name")
            else "",
            name=response.get("name", ""),
            type="websecurityscanner.scanconfig",
            project=response.get("name", "").split("/")[1]
            if len(response.get("name", "").split("/")) > 1
            else "",
            display_name=response.get("displayName", ""),
            starting_urls=response.get("startingUrls", []),
            max_qps=response.get("maxQps"),
            authentication=response.get("authentication"),
            user_agent=response.get("userAgent"),
            blacklist_patterns=response.get("blacklistPatterns"),
            schedule=response.get("schedule"),
            target_platforms=response.get("targetPlatforms"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )


class ScanRun(GCPResource):
    """Model for a Web Security Scanner Scan Run."""

    scan_config_name: str = Field(
        "", description="The resource name of the parent scan config"
    )
    execution_state: str = Field(
        "", description="The execution state of the scan run"
    )
    result_state: Optional[str] = Field(
        None, description="The result state of the scan run"
    )
    start_time: Optional[datetime] = Field(
        None, description="The time the scan run started"
    )
    end_time: Optional[datetime] = Field(
        None, description="The time the scan run ended"
    )
    urls_crawled_count: Optional[int] = Field(
        None, description="The number of URLs crawled during the scan"
    )
    urls_tested_count: Optional[int] = Field(
        None, description="The number of URLs tested during the scan"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("scan_run")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "ScanRun":
        """Create a ScanRun from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new ScanRun instance
        """
        # Extract scan config name from the scan run name
        name = response.get("name", "")
        parts = name.split("/")
        scan_config_name = ""
        if len(parts) >= 4:
            scan_config_name = "/".join(parts[:4])

        return cls(
            id=parts[-1] if parts else "",
            name=name,
            type="websecurityscanner.scanrun",
            project=parts[1] if len(parts) > 1 else "",
            scan_config_name=scan_config_name,
            execution_state=response.get("executionState", ""),
            result_state=response.get("resultState"),
            start_time=response.get("startTime"),
            end_time=response.get("endTime"),
            urls_crawled_count=response.get("urlsCrawledCount"),
            urls_tested_count=response.get("urlsTestedCount"),
        )
