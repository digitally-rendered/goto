"""Models for Google Cloud CDN / Backend Services resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.cdn import get_schema


class BackendService(GCPResource):
    """Model for a Google Cloud Backend Service."""

    description: Optional[str] = Field(
        None, description="A description of the backend service"
    )
    backends: List[Dict] = Field(
        default_factory=list,
        description="The list of backends that serve this backend service",
    )
    health_checks: List[str] = Field(
        default_factory=list,
        description="URLs of health checks for the backend service",
    )
    protocol: str = Field(
        "HTTP", description="The protocol used to communicate with backends"
    )
    port: Optional[int] = Field(
        None, description="The TCP port to connect on the backend"
    )
    port_name: Optional[str] = Field(
        None, description="A named port on the backend instance groups"
    )
    timeout_sec: Optional[int] = Field(
        None, description="Backend service timeout in seconds"
    )
    enable_cdn: bool = Field(
        False, description="Whether Cloud CDN is enabled for this backend service"
    )
    cdn_policy: Optional[Dict] = Field(
        None, description="Cloud CDN configuration for this backend service"
    )
    load_balancing_scheme: Optional[str] = Field(
        None, description="The load balancing scheme (EXTERNAL, INTERNAL, etc.)"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("backend_service")}

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "BackendService":
        """Create a BackendService from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new BackendService instance
        """
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="compute.backendService",
            project=response.get("project", ""),
            description=response.get("description"),
            backends=response.get("backends", []),
            health_checks=response.get("healthChecks", []),
            protocol=response.get("protocol", "HTTP"),
            port=response.get("port"),
            port_name=response.get("portName"),
            timeout_sec=response.get("timeoutSec"),
            enable_cdn=response.get("enableCDN", False),
            cdn_policy=response.get("cdnPolicy"),
            load_balancing_scheme=response.get("loadBalancingScheme"),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance


class UrlMap(GCPResource):
    """Model for a Google Cloud URL Map."""

    description: Optional[str] = Field(
        None, description="A description of the URL map"
    )
    default_service: str = Field(
        "", description="The full URL of the default backend service"
    )
    host_rules: Optional[List[Dict]] = Field(
        None, description="Host rules for routing requests"
    )
    path_matchers: Optional[List[Dict]] = Field(
        None, description="Path matchers for routing requests"
    )
    fingerprint: Optional[str] = Field(
        None, description="Fingerprint of this resource for optimistic locking"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("url_map")}

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "UrlMap":
        """Create a UrlMap from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new UrlMap instance
        """
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="compute.urlMap",
            project=response.get("project", ""),
            description=response.get("description"),
            default_service=response.get("defaultService", ""),
            host_rules=response.get("hostRules"),
            path_matchers=response.get("pathMatchers"),
            fingerprint=response.get("fingerprint"),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance


class HealthCheck(GCPResource):
    """Model for a Google Cloud Health Check."""

    description: Optional[str] = Field(
        None, description="A description of the health check"
    )
    check_type: str = Field(
        "HTTP", description="The type of health check (HTTP, HTTPS, TCP, SSL, HTTP2)"
    )
    check_interval_sec: Optional[int] = Field(
        None, description="How often (in seconds) to send a health check"
    )
    timeout_sec: Optional[int] = Field(
        None, description="How long to wait before claiming failure"
    )
    healthy_threshold: Optional[int] = Field(
        None, description="Consecutive successes required to mark healthy"
    )
    unhealthy_threshold: Optional[int] = Field(
        None, description="Consecutive failures required to mark unhealthy"
    )
    http_health_check: Optional[Dict] = Field(
        None, description="HTTP health check configuration"
    )
    https_health_check: Optional[Dict] = Field(
        None, description="HTTPS health check configuration"
    )
    tcp_health_check: Optional[Dict] = Field(
        None, description="TCP health check configuration"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("health_check")}

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "HealthCheck":
        """Create a HealthCheck from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new HealthCheck instance
        """
        # Determine check type from the response
        check_type = "HTTP"
        if response.get("type"):
            check_type = response["type"]
        elif response.get("httpsHealthCheck"):
            check_type = "HTTPS"
        elif response.get("tcpHealthCheck"):
            check_type = "TCP"
        elif response.get("sslHealthCheck"):
            check_type = "SSL"
        elif response.get("http2HealthCheck"):
            check_type = "HTTP2"

        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="compute.healthCheck",
            project=response.get("project", ""),
            description=response.get("description"),
            check_type=check_type,
            check_interval_sec=response.get("checkIntervalSec"),
            timeout_sec=response.get("timeoutSec"),
            healthy_threshold=response.get("healthyThreshold"),
            unhealthy_threshold=response.get("unhealthyThreshold"),
            http_health_check=response.get("httpHealthCheck"),
            https_health_check=response.get("httpsHealthCheck"),
            tcp_health_check=response.get("tcpHealthCheck"),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance
