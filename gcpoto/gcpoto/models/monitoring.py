"""Models for Google Cloud Monitoring resources."""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource


class MetricDescriptor(GCPResource):
    """Model for a Google Cloud Monitoring metric descriptor."""

    display_name: str = Field("", description="A concise name for the metric")
    description: Optional[str] = Field(
        None, description="A detailed description of the metric"
    )
    metric_kind: str = Field(
        "GAUGE",
        description="The kind of measurement (GAUGE, DELTA, CUMULATIVE)",
    )
    value_type: str = Field(
        "DOUBLE",
        description="The value type (BOOL, INT64, DOUBLE, STRING, DISTRIBUTION)",
    )
    unit: Optional[str] = Field(
        None, description="The units in which the metric value is reported"
    )
    _tags: Optional[Dict[str, str]] = None

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
    def from_api_response(cls, response: Dict[str, Any]) -> "MetricDescriptor":
        """Create a MetricDescriptor from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new MetricDescriptor instance
        """
        full_type = response.get("type", "")
        # Use the metric type as both id and name
        metric_name = full_type.split("/")[-1] if "/" in full_type else full_type

        # Extract project from name: projects/{project}/metricDescriptors/{type}
        full_name = response.get("name", "")
        project_id = ""
        if full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        instance = cls(
            id=full_name or full_type,
            name=metric_name,
            type="monitoring.metricDescriptor",
            project=project_id,
            labels=response.get("labels"),
            display_name=response.get("displayName", ""),
            description=response.get("description"),
            metric_kind=response.get("metricKind", "GAUGE"),
            value_type=response.get("valueType", "DOUBLE"),
            unit=response.get("unit"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance


class AlertPolicy(GCPResource):
    """Model for a Google Cloud Monitoring alert policy."""

    display_name: str = Field("", description="A short name for the policy")
    documentation: Optional[Dict[str, Any]] = Field(
        None, description="Documentation for the policy"
    )
    conditions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Conditions for the alert policy"
    )
    combiner: str = Field(
        "OR",
        description="How to combine the conditions (OR, AND)",
    )
    enabled: bool = Field(True, description="Whether the policy is enabled")
    notification_channels: Optional[List[str]] = Field(
        None, description="Notification channels to notify when the policy fires"
    )
    _tags: Optional[Dict[str, str]] = None

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
    def from_api_response(cls, response: Dict[str, Any]) -> "AlertPolicy":
        """Create an AlertPolicy from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new AlertPolicy instance
        """
        full_name = response.get("name", "")
        policy_name = full_name.split("/")[-1] if "/" in full_name else full_name

        # Extract project from name: projects/{project}/alertPolicies/{policy_id}
        project_id = ""
        if "/" in full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        # Parse enabled field (API returns a wrapper object or bool)
        enabled_val = response.get("enabled", True)
        if isinstance(enabled_val, dict):
            enabled_val = enabled_val.get("value", True)

        instance = cls(
            id=full_name,
            name=policy_name,
            type="monitoring.alertPolicy",
            project=project_id,
            labels=response.get("userLabels"),
            display_name=response.get("displayName", ""),
            documentation=response.get("documentation"),
            conditions=response.get("conditions", []),
            combiner=response.get("combiner", "OR"),
            enabled=enabled_val,
            notification_channels=response.get("notificationChannels"),
            created=response.get("creationRecord", {}).get("mutateTime"),
            updated=response.get("mutationRecord", {}).get("mutateTime"),
        )

        if response.get("userLabels"):
            instance._tags = response["userLabels"]

        return instance


class NotificationChannel(GCPResource):
    """Model for a Google Cloud Monitoring notification channel."""

    display_name: str = Field("", description="A human-readable name for the channel")
    channel_type: str = Field(
        "", description="The type of notification channel (e.g., email, sms, slack)"
    )
    description: Optional[str] = Field(
        None, description="A description of the channel"
    )
    enabled: bool = Field(True, description="Whether the channel is enabled")
    verification_status: Optional[str] = Field(
        None, description="The verification status of the channel"
    )
    _tags: Optional[Dict[str, str]] = None

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
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "NotificationChannel":
        """Create a NotificationChannel from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new NotificationChannel instance
        """
        full_name = response.get("name", "")
        channel_name = (
            full_name.split("/")[-1] if "/" in full_name else full_name
        )

        # Extract project from name:
        # projects/{project}/notificationChannels/{channel_id}
        project_id = ""
        if "/" in full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        # Parse enabled field
        enabled_val = response.get("enabled", True)
        if isinstance(enabled_val, dict):
            enabled_val = enabled_val.get("value", True)

        instance = cls(
            id=full_name,
            name=channel_name,
            type="monitoring.notificationChannel",
            project=project_id,
            labels=response.get("labels"),
            display_name=response.get("displayName", ""),
            channel_type=response.get("type", ""),
            description=response.get("description"),
            enabled=enabled_val,
            verification_status=response.get("verificationStatus"),
            created=response.get("creationRecord", {}).get("mutateTime"),
            updated=response.get("mutationRecord", {}).get("mutateTime"),
        )

        if response.get("userLabels"):
            instance._tags = response["userLabels"]

        return instance


class UptimeCheckConfig(GCPResource):
    """Model for a Google Cloud Monitoring uptime check configuration."""

    display_name: str = Field("", description="A human-friendly name for the check")
    monitored_resource: Optional[Dict[str, Any]] = Field(
        None, description="The monitored resource associated with the check"
    )
    http_check: Optional[Dict[str, Any]] = Field(
        None, description="HTTP check configuration"
    )
    tcp_check: Optional[Dict[str, Any]] = Field(
        None, description="TCP check configuration"
    )
    period: Optional[str] = Field(
        None, description="How often the uptime check is performed"
    )
    timeout: Optional[str] = Field(
        None, description="The maximum amount of time to wait for the request"
    )
    selected_regions: Optional[List[str]] = Field(
        None, description="The list of regions from which the check is run"
    )
    is_internal: bool = Field(
        False, description="Whether the check is internal"
    )

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any]
    ) -> "UptimeCheckConfig":
        """Create an UptimeCheckConfig from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new UptimeCheckConfig instance
        """
        full_name = response.get("name", "")
        check_name = (
            full_name.split("/")[-1] if "/" in full_name else full_name
        )

        # Extract project from name:
        # projects/{project}/uptimeCheckConfigs/{check_id}
        project_id = ""
        if "/" in full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        instance = cls(
            id=full_name,
            name=check_name,
            type="monitoring.uptimeCheckConfig",
            project=project_id,
            display_name=response.get("displayName", ""),
            monitored_resource=response.get("monitoredResource"),
            http_check=response.get("httpCheck"),
            tcp_check=response.get("tcpCheck"),
            period=response.get("period"),
            timeout=response.get("timeout"),
            selected_regions=response.get("selectedRegions"),
            is_internal=response.get("isInternal", False),
        )

        return instance
