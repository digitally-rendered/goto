"""Service implementation for Google Cloud Monitoring."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.monitoring import (
    MetricDescriptor,
    AlertPolicy,
    NotificationChannel,
    UptimeCheckConfig,
)
from gcpoto.exceptions import (
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class MonitoringService(GCPService[MetricDescriptor]):
    """Service for interacting with Google Cloud Monitoring."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Monitoring service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="monitoring",
            version="v3",
            credentials_file=credentials_file,
            resource_model=MetricDescriptor,
            **kwargs,
        )

    # ---- Metric Descriptors ----

    def list_metric_descriptors(
        self, filter_str: Optional[str] = None, **kwargs
    ) -> List[MetricDescriptor]:
        """List metric descriptors for the project.

        Args:
            filter_str: Optional filter expression for metric descriptors.
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of MetricDescriptor instances.
        """
        logger.debug(
            "Listing metric descriptors for project %s", self.project_id
        )

        parent = f"projects/{self.project_id}"
        params: Dict[str, Any] = {"name": parent}
        if filter_str:
            params["filter"] = filter_str
        params.update(kwargs)

        descriptors = []
        request = self.service.projects().metricDescriptors().list(**params)
        while request is not None:
            response = request.execute()
            for item in response.get("metricDescriptors", []):
                descriptors.append(MetricDescriptor.from_api_response(item))
            request = (
                self.service.projects()
                .metricDescriptors()
                .list_next(request, response)
            )

        return descriptors

    def get_metric_descriptor(self, metric_type: str) -> MetricDescriptor:
        """Get a specific metric descriptor by its type.

        Args:
            metric_type: The metric type string
                (e.g., "custom.googleapis.com/my_metric").

        Returns:
            A MetricDescriptor instance.
        """
        if "/" not in metric_type or not metric_type.startswith("projects/"):
            name = f"projects/{self.project_id}/metricDescriptors/{metric_type}"
        else:
            name = metric_type

        logger.debug("Getting metric descriptor %s", name)

        try:
            request = self.service.projects().metricDescriptors().get(name=name)
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("metricDescriptor", metric_type)
            raise

        return MetricDescriptor.from_api_response(response)

    def create_metric_descriptor(
        self,
        metric_type: str,
        display_name: str,
        metric_kind: str,
        value_type: str,
        unit: Optional[str] = None,
        description: Optional[str] = None,
        labels: Optional[List[Dict[str, str]]] = None,
    ) -> MetricDescriptor:
        """Create a custom metric descriptor.

        Args:
            metric_type: The metric type
                (e.g., "custom.googleapis.com/my_metric").
            display_name: A concise name for the metric.
            metric_kind: The kind of measurement (GAUGE, DELTA, CUMULATIVE).
            value_type: The value type (BOOL, INT64, DOUBLE, STRING, DISTRIBUTION).
            unit: Optional units for the metric value.
            description: Optional description for the metric.
            labels: Optional list of label descriptors
                (each with "key", "valueType", "description").

        Returns:
            The newly created MetricDescriptor instance.
        """
        parent = f"projects/{self.project_id}"

        body: Dict[str, Any] = {
            "type": metric_type,
            "displayName": display_name,
            "metricKind": metric_kind,
            "valueType": value_type,
        }
        if unit is not None:
            body["unit"] = unit
        if description is not None:
            body["description"] = description
        if labels is not None:
            body["labels"] = labels

        logger.debug(
            "Creating metric descriptor %s in project %s",
            metric_type,
            self.project_id,
        )

        request = self.service.projects().metricDescriptors().create(
            name=parent, body=body
        )
        response = request.execute()

        return MetricDescriptor.from_api_response(response)

    def delete_metric_descriptor(self, metric_type: str) -> bool:
        """Delete a custom metric descriptor.

        Args:
            metric_type: The metric type to delete.

        Returns:
            True if the deletion was successful.
        """
        if "/" not in metric_type or not metric_type.startswith("projects/"):
            name = f"projects/{self.project_id}/metricDescriptors/{metric_type}"
        else:
            name = metric_type

        logger.debug("Deleting metric descriptor %s", name)

        request = self.service.projects().metricDescriptors().delete(name=name)
        request.execute()

        return True

    # ---- Time Series ----

    def list_time_series(
        self,
        filter_str: str,
        interval_start: str,
        interval_end: str,
        aggregation: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """List time series data matching a filter.

        Args:
            filter_str: A monitoring filter that specifies which time series
                should be returned.
            interval_start: The start of the time interval (RFC3339 string).
            interval_end: The end of the time interval (RFC3339 string).
            aggregation: Optional aggregation parameters.
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of time series data dictionaries.
        """
        logger.debug(
            "Listing time series for project %s with filter: %s",
            self.project_id,
            filter_str,
        )

        parent = f"projects/{self.project_id}"
        params: Dict[str, Any] = {
            "name": parent,
            "filter": filter_str,
            "interval_startTime": interval_start,
            "interval_endTime": interval_end,
        }

        if aggregation:
            if "alignmentPeriod" in aggregation:
                params["aggregation_alignmentPeriod"] = aggregation[
                    "alignmentPeriod"
                ]
            if "perSeriesAligner" in aggregation:
                params["aggregation_perSeriesAligner"] = aggregation[
                    "perSeriesAligner"
                ]
            if "crossSeriesReducer" in aggregation:
                params["aggregation_crossSeriesReducer"] = aggregation[
                    "crossSeriesReducer"
                ]
            if "groupByFields" in aggregation:
                params["aggregation_groupByFields"] = aggregation[
                    "groupByFields"
                ]

        params.update(kwargs)

        time_series = []
        request = self.service.projects().timeSeries().list(**params)
        while request is not None:
            response = request.execute()
            for ts in response.get("timeSeries", []):
                time_series.append(ts)
            request = (
                self.service.projects()
                .timeSeries()
                .list_next(request, response)
            )

        return time_series

    # ---- Alert Policies ----

    def list_alert_policies(self, **kwargs) -> List[AlertPolicy]:
        """List alert policies for the project.

        Args:
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of AlertPolicy instances.
        """
        logger.debug(
            "Listing alert policies for project %s", self.project_id
        )

        parent = f"projects/{self.project_id}"
        policies = []
        request = self.service.projects().alertPolicies().list(
            name=parent, **kwargs
        )
        while request is not None:
            response = request.execute()
            for item in response.get("alertPolicies", []):
                policies.append(AlertPolicy.from_api_response(item))
            request = (
                self.service.projects()
                .alertPolicies()
                .list_next(request, response)
            )

        return policies

    def get_alert_policy(self, policy_id: str) -> AlertPolicy:
        """Get a specific alert policy by ID.

        Args:
            policy_id: The alert policy ID or full resource name.

        Returns:
            An AlertPolicy instance.
        """
        if "/" not in policy_id:
            name = f"projects/{self.project_id}/alertPolicies/{policy_id}"
        else:
            name = policy_id

        logger.debug("Getting alert policy %s", name)

        try:
            request = self.service.projects().alertPolicies().get(name=name)
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("alertPolicy", policy_id)
            raise

        return AlertPolicy.from_api_response(response)

    def create_alert_policy(
        self,
        display_name: str,
        conditions: List[Dict[str, Any]],
        combiner: str = "OR",
        enabled: bool = True,
        notification_channels: Optional[List[str]] = None,
        documentation: Optional[Dict[str, Any]] = None,
    ) -> AlertPolicy:
        """Create a new alert policy.

        Args:
            display_name: A short name for the policy.
            conditions: A list of conditions for the policy.
            combiner: How to combine conditions (OR, AND).
            enabled: Whether the policy is enabled.
            notification_channels: Optional list of notification channel names.
            documentation: Optional documentation for the policy.

        Returns:
            The newly created AlertPolicy instance.
        """
        parent = f"projects/{self.project_id}"

        body: Dict[str, Any] = {
            "displayName": display_name,
            "conditions": conditions,
            "combiner": combiner,
            "enabled": enabled,
        }
        if notification_channels is not None:
            body["notificationChannels"] = notification_channels
        if documentation is not None:
            body["documentation"] = documentation

        logger.debug(
            "Creating alert policy '%s' in project %s",
            display_name,
            self.project_id,
        )

        request = self.service.projects().alertPolicies().create(
            name=parent, body=body
        )
        response = request.execute()

        return AlertPolicy.from_api_response(response)

    def update_alert_policy(
        self,
        policy_id: str,
        update_fields: Dict[str, Any],
    ) -> AlertPolicy:
        """Update an existing alert policy.

        Args:
            policy_id: The alert policy ID or full resource name.
            update_fields: A dictionary of fields to update.

        Returns:
            The updated AlertPolicy instance.
        """
        if "/" not in policy_id:
            name = f"projects/{self.project_id}/alertPolicies/{policy_id}"
        else:
            name = policy_id

        logger.debug("Updating alert policy %s", name)

        body: Dict[str, Any] = {"name": name}
        body.update(update_fields)

        request = self.service.projects().alertPolicies().patch(
            name=name, body=body
        )
        response = request.execute()

        return AlertPolicy.from_api_response(response)

    def delete_alert_policy(self, policy_id: str) -> bool:
        """Delete an alert policy.

        Args:
            policy_id: The alert policy ID or full resource name.

        Returns:
            True if the deletion was successful.
        """
        if "/" not in policy_id:
            name = f"projects/{self.project_id}/alertPolicies/{policy_id}"
        else:
            name = policy_id

        logger.debug("Deleting alert policy %s", name)

        request = self.service.projects().alertPolicies().delete(name=name)
        request.execute()

        return True

    # ---- Notification Channels ----

    def list_notification_channels(
        self, **kwargs
    ) -> List[NotificationChannel]:
        """List notification channels for the project.

        Args:
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of NotificationChannel instances.
        """
        logger.debug(
            "Listing notification channels for project %s", self.project_id
        )

        parent = f"projects/{self.project_id}"
        channels = []
        request = self.service.projects().notificationChannels().list(
            name=parent, **kwargs
        )
        while request is not None:
            response = request.execute()
            for item in response.get("notificationChannels", []):
                channels.append(
                    NotificationChannel.from_api_response(item)
                )
            request = (
                self.service.projects()
                .notificationChannels()
                .list_next(request, response)
            )

        return channels

    def get_notification_channel(
        self, channel_id: str
    ) -> NotificationChannel:
        """Get a specific notification channel by ID.

        Args:
            channel_id: The notification channel ID or full resource name.

        Returns:
            A NotificationChannel instance.
        """
        if "/" not in channel_id:
            name = (
                f"projects/{self.project_id}"
                f"/notificationChannels/{channel_id}"
            )
        else:
            name = channel_id

        logger.debug("Getting notification channel %s", name)

        try:
            request = (
                self.service.projects()
                .notificationChannels()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "notificationChannel", channel_id
                )
            raise

        return NotificationChannel.from_api_response(response)

    def create_notification_channel(
        self,
        display_name: str,
        channel_type: str,
        labels: Optional[Dict[str, str]] = None,
        enabled: bool = True,
    ) -> NotificationChannel:
        """Create a new notification channel.

        Args:
            display_name: A human-readable name for the channel.
            channel_type: The channel type (e.g., "email", "sms", "slack").
            labels: Optional configuration labels for the channel type.
            enabled: Whether the channel is enabled.

        Returns:
            The newly created NotificationChannel instance.
        """
        parent = f"projects/{self.project_id}"

        body: Dict[str, Any] = {
            "displayName": display_name,
            "type": channel_type,
            "enabled": enabled,
        }
        if labels is not None:
            body["labels"] = labels

        logger.debug(
            "Creating notification channel '%s' in project %s",
            display_name,
            self.project_id,
        )

        request = (
            self.service.projects()
            .notificationChannels()
            .create(name=parent, body=body)
        )
        response = request.execute()

        return NotificationChannel.from_api_response(response)

    def delete_notification_channel(
        self, channel_id: str, force: bool = False
    ) -> bool:
        """Delete a notification channel.

        Args:
            channel_id: The notification channel ID or full resource name.
            force: Whether to force deletion even if referenced by policies.

        Returns:
            True if the deletion was successful.
        """
        if "/" not in channel_id:
            name = (
                f"projects/{self.project_id}"
                f"/notificationChannels/{channel_id}"
            )
        else:
            name = channel_id

        logger.debug("Deleting notification channel %s", name)

        request = (
            self.service.projects()
            .notificationChannels()
            .delete(name=name, force=force)
        )
        request.execute()

        return True

    # ---- Uptime Check Configs ----

    def list_uptime_check_configs(
        self, **kwargs
    ) -> List[UptimeCheckConfig]:
        """List uptime check configurations for the project.

        Args:
            **kwargs: Additional parameters for the API request.

        Returns:
            A list of UptimeCheckConfig instances.
        """
        logger.debug(
            "Listing uptime check configs for project %s", self.project_id
        )

        parent = f"projects/{self.project_id}"
        configs = []
        request = self.service.projects().uptimeCheckConfigs().list(
            parent=parent, **kwargs
        )
        while request is not None:
            response = request.execute()
            for item in response.get("uptimeCheckConfigs", []):
                configs.append(UptimeCheckConfig.from_api_response(item))
            request = (
                self.service.projects()
                .uptimeCheckConfigs()
                .list_next(request, response)
            )

        return configs

    def get_uptime_check_config(
        self, check_id: str
    ) -> UptimeCheckConfig:
        """Get a specific uptime check configuration by ID.

        Args:
            check_id: The uptime check config ID or full resource name.

        Returns:
            An UptimeCheckConfig instance.
        """
        if "/" not in check_id:
            name = (
                f"projects/{self.project_id}"
                f"/uptimeCheckConfigs/{check_id}"
            )
        else:
            name = check_id

        logger.debug("Getting uptime check config %s", name)

        try:
            request = (
                self.service.projects()
                .uptimeCheckConfigs()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "uptimeCheckConfig", check_id
                )
            raise

        return UptimeCheckConfig.from_api_response(response)

    def create_uptime_check_config(
        self,
        display_name: str,
        monitored_resource: Dict[str, Any],
        http_check: Optional[Dict[str, Any]] = None,
        period: Optional[str] = None,
        timeout: Optional[str] = None,
    ) -> UptimeCheckConfig:
        """Create a new uptime check configuration.

        Args:
            display_name: A human-friendly name for the check.
            monitored_resource: The monitored resource to check.
            http_check: Optional HTTP check configuration.
            period: Optional check period (e.g., "60s").
            timeout: Optional check timeout (e.g., "10s").

        Returns:
            The newly created UptimeCheckConfig instance.
        """
        parent = f"projects/{self.project_id}"

        body: Dict[str, Any] = {
            "displayName": display_name,
            "monitoredResource": monitored_resource,
        }
        if http_check is not None:
            body["httpCheck"] = http_check
        if period is not None:
            body["period"] = period
        if timeout is not None:
            body["timeout"] = timeout

        logger.debug(
            "Creating uptime check config '%s' in project %s",
            display_name,
            self.project_id,
        )

        request = (
            self.service.projects()
            .uptimeCheckConfigs()
            .create(parent=parent, body=body)
        )
        response = request.execute()

        return UptimeCheckConfig.from_api_response(response)

    def delete_uptime_check_config(self, check_id: str) -> bool:
        """Delete an uptime check configuration.

        Args:
            check_id: The uptime check config ID or full resource name.

        Returns:
            True if the deletion was successful.
        """
        if "/" not in check_id:
            name = (
                f"projects/{self.project_id}"
                f"/uptimeCheckConfigs/{check_id}"
            )
        else:
            name = check_id

        logger.debug("Deleting uptime check config %s", name)

        request = (
            self.service.projects()
            .uptimeCheckConfigs()
            .delete(name=name)
        )
        request.execute()

        return True
