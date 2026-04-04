"""Tests for Cloud Monitoring service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.monitoring import MonitoringService
from gcpoto.models.monitoring import (
    MetricDescriptor,
    AlertPolicy,
    NotificationChannel,
    UptimeCheckConfig,
)
from gcpoto.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().metricDescriptors() chain
        mock_metric_descriptors = mock.MagicMock()
        mock_service.projects.return_value.metricDescriptors.return_value = (
            mock_metric_descriptors
        )

        # Set up projects().timeSeries() chain
        mock_time_series = mock.MagicMock()
        mock_service.projects.return_value.timeSeries.return_value = (
            mock_time_series
        )

        # Set up projects().alertPolicies() chain
        mock_alert_policies = mock.MagicMock()
        mock_service.projects.return_value.alertPolicies.return_value = (
            mock_alert_policies
        )

        # Set up projects().notificationChannels() chain
        mock_notification_channels = mock.MagicMock()
        mock_service.projects.return_value.notificationChannels.return_value = (
            mock_notification_channels
        )

        # Set up projects().uptimeCheckConfigs() chain
        mock_uptime_checks = mock.MagicMock()
        mock_service.projects.return_value.uptimeCheckConfigs.return_value = (
            mock_uptime_checks
        )

        yield mock_service


@pytest.fixture
def sample_metric_descriptor_response():
    """Sample Cloud Monitoring metric descriptor API response."""
    return {
        "name": "projects/test-project/metricDescriptors/custom.googleapis.com/my_metric",
        "type": "custom.googleapis.com/my_metric",
        "displayName": "My Custom Metric",
        "description": "A custom metric for testing",
        "metricKind": "GAUGE",
        "valueType": "DOUBLE",
        "unit": "1",
        "labels": {
            "env": "production",
        },
    }


@pytest.fixture
def sample_alert_policy_response():
    """Sample Cloud Monitoring alert policy API response."""
    return {
        "name": "projects/test-project/alertPolicies/policy-123",
        "displayName": "High CPU Alert",
        "documentation": {
            "content": "CPU usage is above threshold.",
            "mimeType": "text/markdown",
        },
        "conditions": [
            {
                "displayName": "CPU > 90%",
                "conditionThreshold": {
                    "filter": 'metric.type="compute.googleapis.com/instance/cpu/utilization"',
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 0.9,
                    "duration": "60s",
                },
            }
        ],
        "combiner": "OR",
        "enabled": True,
        "notificationChannels": [
            "projects/test-project/notificationChannels/channel-456"
        ],
        "userLabels": {"team": "sre", "severity": "critical"},
        "creationRecord": {"mutateTime": "2025-01-10T08:00:00Z"},
        "mutationRecord": {"mutateTime": "2025-01-12T12:00:00Z"},
    }


@pytest.fixture
def sample_notification_channel_response():
    """Sample Cloud Monitoring notification channel API response."""
    return {
        "name": "projects/test-project/notificationChannels/channel-456",
        "displayName": "SRE Team Email",
        "type": "email",
        "description": "Email channel for SRE team",
        "labels": {"email_address": "sre@example.com"},
        "enabled": True,
        "verificationStatus": "VERIFIED",
        "userLabels": {"team": "sre"},
        "creationRecord": {"mutateTime": "2025-01-10T08:00:00Z"},
        "mutationRecord": {"mutateTime": "2025-01-12T12:00:00Z"},
    }


@pytest.fixture
def sample_uptime_check_response():
    """Sample Cloud Monitoring uptime check config API response."""
    return {
        "name": "projects/test-project/uptimeCheckConfigs/check-789",
        "displayName": "Homepage Check",
        "monitoredResource": {
            "type": "uptime_url",
            "labels": {"host": "example.com"},
        },
        "httpCheck": {
            "requestMethod": "GET",
            "useSsl": True,
            "path": "/",
            "port": 443,
        },
        "period": "60s",
        "timeout": "10s",
        "selectedRegions": ["USA", "EUROPE", "ASIA_PACIFIC"],
        "isInternal": False,
    }


# ---- Service Init ----


class TestMonitoringServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the MonitoringService."""
        from googleapiclient.discovery import build

        service = MonitoringService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "monitoring"
        assert service.version == "v3"
        build.assert_called_once_with("monitoring", "v3", credentials=None)


# ---- MetricDescriptor Model ----


class TestMetricDescriptorModel:
    def test_from_api_response(self, sample_metric_descriptor_response):
        """Test creating a MetricDescriptor from an API response."""
        descriptor = MetricDescriptor.from_api_response(
            sample_metric_descriptor_response
        )

        assert descriptor.name == "my_metric"
        assert descriptor.project == "test-project"
        assert descriptor.display_name == "My Custom Metric"
        assert descriptor.description == "A custom metric for testing"
        assert descriptor.metric_kind == "GAUGE"
        assert descriptor.value_type == "DOUBLE"
        assert descriptor.unit == "1"
        assert descriptor.type == "monitoring.metricDescriptor"

    def test_from_api_response_minimal(self):
        """Test creating a MetricDescriptor from a minimal API response."""
        descriptor = MetricDescriptor.from_api_response({})

        assert descriptor.name == ""
        assert descriptor.display_name == ""
        assert descriptor.description is None
        assert descriptor.metric_kind == "GAUGE"
        assert descriptor.value_type == "DOUBLE"
        assert descriptor.unit is None

    def test_get_tag(self, sample_metric_descriptor_response):
        """Test get_tag on MetricDescriptor."""
        descriptor = MetricDescriptor.from_api_response(
            sample_metric_descriptor_response
        )

        assert descriptor.get_tag("env") == "production"
        assert descriptor.get_tag("missing", "default") == "default"


# ---- AlertPolicy Model ----


class TestAlertPolicyModel:
    def test_from_api_response(self, sample_alert_policy_response):
        """Test creating an AlertPolicy from an API response."""
        policy = AlertPolicy.from_api_response(sample_alert_policy_response)

        assert policy.name == "policy-123"
        assert policy.project == "test-project"
        assert policy.display_name == "High CPU Alert"
        assert policy.documentation == {
            "content": "CPU usage is above threshold.",
            "mimeType": "text/markdown",
        }
        assert len(policy.conditions) == 1
        assert policy.conditions[0]["displayName"] == "CPU > 90%"
        assert policy.combiner == "OR"
        assert policy.enabled is True
        assert len(policy.notification_channels) == 1
        assert policy.type == "monitoring.alertPolicy"

    def test_from_api_response_minimal(self):
        """Test creating an AlertPolicy from a minimal API response."""
        policy = AlertPolicy.from_api_response({"name": "simple-policy"})

        assert policy.name == "simple-policy"
        assert policy.display_name == ""
        assert policy.documentation is None
        assert policy.conditions == []
        assert policy.combiner == "OR"
        assert policy.enabled is True
        assert policy.notification_channels is None

    def test_from_api_response_enabled_wrapper(self):
        """Test AlertPolicy with enabled as a wrapper object."""
        policy = AlertPolicy.from_api_response(
            {"name": "policy-1", "enabled": {"value": False}}
        )
        assert policy.enabled is False

    def test_get_tag(self, sample_alert_policy_response):
        """Test get_tag on AlertPolicy."""
        policy = AlertPolicy.from_api_response(sample_alert_policy_response)

        assert policy.get_tag("team") == "sre"
        assert policy.get_tag("severity") == "critical"
        assert policy.get_tag("missing", "default") == "default"


# ---- NotificationChannel Model ----


class TestNotificationChannelModel:
    def test_from_api_response(self, sample_notification_channel_response):
        """Test creating a NotificationChannel from an API response."""
        channel = NotificationChannel.from_api_response(
            sample_notification_channel_response
        )

        assert channel.name == "channel-456"
        assert channel.project == "test-project"
        assert channel.display_name == "SRE Team Email"
        assert channel.channel_type == "email"
        assert channel.description == "Email channel for SRE team"
        assert channel.enabled is True
        assert channel.verification_status == "VERIFIED"
        assert channel.type == "monitoring.notificationChannel"

    def test_from_api_response_minimal(self):
        """Test creating a NotificationChannel from a minimal API response."""
        channel = NotificationChannel.from_api_response(
            {"name": "simple-channel"}
        )

        assert channel.name == "simple-channel"
        assert channel.display_name == ""
        assert channel.channel_type == ""
        assert channel.description is None
        assert channel.enabled is True
        assert channel.verification_status is None

    def test_get_tag(self, sample_notification_channel_response):
        """Test get_tag on NotificationChannel."""
        channel = NotificationChannel.from_api_response(
            sample_notification_channel_response
        )

        assert channel.get_tag("team") == "sre"
        assert channel.get_tag("missing", "default") == "default"


# ---- UptimeCheckConfig Model ----


class TestUptimeCheckConfigModel:
    def test_from_api_response(self, sample_uptime_check_response):
        """Test creating an UptimeCheckConfig from an API response."""
        check = UptimeCheckConfig.from_api_response(
            sample_uptime_check_response
        )

        assert check.name == "check-789"
        assert check.project == "test-project"
        assert check.display_name == "Homepage Check"
        assert check.monitored_resource == {
            "type": "uptime_url",
            "labels": {"host": "example.com"},
        }
        assert check.http_check == {
            "requestMethod": "GET",
            "useSsl": True,
            "path": "/",
            "port": 443,
        }
        assert check.period == "60s"
        assert check.timeout == "10s"
        assert check.selected_regions == ["USA", "EUROPE", "ASIA_PACIFIC"]
        assert check.is_internal is False
        assert check.type == "monitoring.uptimeCheckConfig"

    def test_from_api_response_minimal(self):
        """Test creating an UptimeCheckConfig from a minimal API response."""
        check = UptimeCheckConfig.from_api_response({"name": "simple-check"})

        assert check.name == "simple-check"
        assert check.display_name == ""
        assert check.monitored_resource is None
        assert check.http_check is None
        assert check.tcp_check is None
        assert check.period is None
        assert check.timeout is None
        assert check.selected_regions is None
        assert check.is_internal is False

    def test_get_tag(self):
        """Test get_tag on UptimeCheckConfig."""
        check = UptimeCheckConfig.from_api_response({"name": "check-1"})

        assert check.get_tag("missing", "default") == "default"


# ---- Metric Descriptors Service Methods ----


class TestListMetricDescriptors:
    def test_list_metric_descriptors(
        self, mock_google_client, sample_metric_descriptor_response
    ):
        """Test listing metric descriptors."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "metricDescriptors": [sample_metric_descriptor_response]
        }

        # list_next returns None to stop pagination
        mock_list_next = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        descriptors = service.list_metric_descriptors()

        mock_list.assert_called_once_with(name="projects/test-project")

        assert len(descriptors) == 1
        assert isinstance(descriptors[0], MetricDescriptor)
        assert descriptors[0].display_name == "My Custom Metric"

    def test_list_metric_descriptors_with_filter(
        self, mock_google_client
    ):
        """Test listing metric descriptors with a filter."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"metricDescriptors": []}

        mock_list_next = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        descriptors = service.list_metric_descriptors(
            filter_str='metric.type = starts_with("custom.googleapis.com")'
        )

        mock_list.assert_called_once_with(
            name="projects/test-project",
            filter='metric.type = starts_with("custom.googleapis.com")',
        )

        assert descriptors == []

    def test_list_metric_descriptors_empty(self, mock_google_client):
        """Test listing metric descriptors when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        descriptors = service.list_metric_descriptors()

        assert descriptors == []

    def test_list_metric_descriptors_pagination(
        self, mock_google_client, sample_metric_descriptor_response
    ):
        """Test listing metric descriptors with pagination."""
        mock_list = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.list
        )
        mock_list_next = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.list_next
        )

        # First page
        mock_request_1 = mock.MagicMock()
        mock_list.return_value = mock_request_1
        response_1 = {
            "metricDescriptors": [sample_metric_descriptor_response]
        }
        mock_request_1.execute.return_value = response_1

        # Second page
        mock_request_2 = mock.MagicMock()
        second_descriptor = dict(sample_metric_descriptor_response)
        second_descriptor["displayName"] = "Second Metric"
        response_2 = {"metricDescriptors": [second_descriptor]}
        mock_request_2.execute.return_value = response_2

        # list_next returns second request on first call, None on second
        mock_list_next.side_effect = [mock_request_2, None]

        service = MonitoringService(project_id="test-project")
        descriptors = service.list_metric_descriptors()

        assert len(descriptors) == 2
        assert descriptors[0].display_name == "My Custom Metric"
        assert descriptors[1].display_name == "Second Metric"


class TestGetMetricDescriptor:
    def test_get_metric_descriptor(
        self, mock_google_client, sample_metric_descriptor_response
    ):
        """Test getting a specific metric descriptor."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = (
            sample_metric_descriptor_response
        )

        service = MonitoringService(project_id="test-project")
        descriptor = service.get_metric_descriptor(
            "custom.googleapis.com/my_metric"
        )

        mock_get.assert_called_once_with(
            name="projects/test-project/metricDescriptors/custom.googleapis.com/my_metric"
        )

        assert isinstance(descriptor, MetricDescriptor)
        assert descriptor.display_name == "My Custom Metric"

    def test_get_metric_descriptor_full_path(
        self, mock_google_client, sample_metric_descriptor_response
    ):
        """Test getting a metric descriptor with a full path."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = (
            sample_metric_descriptor_response
        )

        service = MonitoringService(project_id="test-project")
        service.get_metric_descriptor(
            "projects/test-project/metricDescriptors/custom.googleapis.com/my_metric"
        )

        mock_get.assert_called_with(
            name="projects/test-project/metricDescriptors/custom.googleapis.com/my_metric"
        )

    def test_get_metric_descriptor_not_found(self, mock_google_client):
        """Test getting a metric descriptor that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404),
            content=b"Metric descriptor not found",
        )

        service = MonitoringService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_metric_descriptor("custom.googleapis.com/nonexistent")


class TestCreateMetricDescriptor:
    def test_create_metric_descriptor(
        self, mock_google_client, sample_metric_descriptor_response
    ):
        """Test creating a metric descriptor."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = (
            sample_metric_descriptor_response
        )

        service = MonitoringService(project_id="test-project")
        descriptor = service.create_metric_descriptor(
            metric_type="custom.googleapis.com/my_metric",
            display_name="My Custom Metric",
            metric_kind="GAUGE",
            value_type="DOUBLE",
            unit="1",
            description="A custom metric for testing",
            labels=[{"key": "env", "valueType": "STRING"}],
        )

        mock_create.assert_called_once_with(
            name="projects/test-project",
            body={
                "type": "custom.googleapis.com/my_metric",
                "displayName": "My Custom Metric",
                "metricKind": "GAUGE",
                "valueType": "DOUBLE",
                "unit": "1",
                "description": "A custom metric for testing",
                "labels": [{"key": "env", "valueType": "STRING"}],
            },
        )

        assert isinstance(descriptor, MetricDescriptor)
        assert descriptor.display_name == "My Custom Metric"

    def test_create_metric_descriptor_minimal(
        self, mock_google_client, sample_metric_descriptor_response
    ):
        """Test creating a metric descriptor with minimal arguments."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = (
            sample_metric_descriptor_response
        )

        service = MonitoringService(project_id="test-project")
        service.create_metric_descriptor(
            metric_type="custom.googleapis.com/my_metric",
            display_name="My Metric",
            metric_kind="GAUGE",
            value_type="DOUBLE",
        )

        mock_create.assert_called_once_with(
            name="projects/test-project",
            body={
                "type": "custom.googleapis.com/my_metric",
                "displayName": "My Metric",
                "metricKind": "GAUGE",
                "valueType": "DOUBLE",
            },
        )


class TestDeleteMetricDescriptor:
    def test_delete_metric_descriptor(self, mock_google_client):
        """Test deleting a metric descriptor."""
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = MonitoringService(project_id="test-project")
        result = service.delete_metric_descriptor(
            "custom.googleapis.com/my_metric"
        )

        mock_delete.assert_called_once_with(
            name="projects/test-project/metricDescriptors/custom.googleapis.com/my_metric"
        )
        assert result is True

    def test_delete_metric_descriptor_full_path(self, mock_google_client):
        """Test deleting a metric descriptor with a full path."""
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value
            .metricDescriptors.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = MonitoringService(project_id="test-project")
        service.delete_metric_descriptor(
            "projects/test-project/metricDescriptors/custom.googleapis.com/my_metric"
        )

        mock_delete.assert_called_with(
            name="projects/test-project/metricDescriptors/custom.googleapis.com/my_metric"
        )


# ---- Time Series Service Methods ----


class TestListTimeSeries:
    def test_list_time_series(self, mock_google_client):
        """Test listing time series data."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .timeSeries.return_value.list
        )
        mock_list.return_value = mock_request

        ts_data = {
            "metric": {
                "type": "compute.googleapis.com/instance/cpu/utilization"
            },
            "points": [
                {
                    "interval": {
                        "startTime": "2025-01-15T10:00:00Z",
                        "endTime": "2025-01-15T10:05:00Z",
                    },
                    "value": {"doubleValue": 0.75},
                }
            ],
        }
        mock_request.execute.return_value = {"timeSeries": [ts_data]}

        mock_list_next = (
            mock_google_client.projects.return_value
            .timeSeries.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        results = service.list_time_series(
            filter_str='metric.type="compute.googleapis.com/instance/cpu/utilization"',
            interval_start="2025-01-15T10:00:00Z",
            interval_end="2025-01-15T10:05:00Z",
        )

        mock_list.assert_called_once_with(
            name="projects/test-project",
            filter='metric.type="compute.googleapis.com/instance/cpu/utilization"',
            interval_startTime="2025-01-15T10:00:00Z",
            interval_endTime="2025-01-15T10:05:00Z",
        )

        assert len(results) == 1
        assert results[0]["metric"]["type"] == (
            "compute.googleapis.com/instance/cpu/utilization"
        )

    def test_list_time_series_with_aggregation(self, mock_google_client):
        """Test listing time series with aggregation."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .timeSeries.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"timeSeries": []}

        mock_list_next = (
            mock_google_client.projects.return_value
            .timeSeries.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        service.list_time_series(
            filter_str='metric.type="compute.googleapis.com/instance/cpu/utilization"',
            interval_start="2025-01-15T10:00:00Z",
            interval_end="2025-01-15T10:05:00Z",
            aggregation={
                "alignmentPeriod": "300s",
                "perSeriesAligner": "ALIGN_MEAN",
                "crossSeriesReducer": "REDUCE_MEAN",
                "groupByFields": ["resource.label.zone"],
            },
        )

        mock_list.assert_called_once_with(
            name="projects/test-project",
            filter='metric.type="compute.googleapis.com/instance/cpu/utilization"',
            interval_startTime="2025-01-15T10:00:00Z",
            interval_endTime="2025-01-15T10:05:00Z",
            aggregation_alignmentPeriod="300s",
            aggregation_perSeriesAligner="ALIGN_MEAN",
            aggregation_crossSeriesReducer="REDUCE_MEAN",
            aggregation_groupByFields=["resource.label.zone"],
        )

    def test_list_time_series_empty(self, mock_google_client):
        """Test listing time series when none match."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .timeSeries.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value
            .timeSeries.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        results = service.list_time_series(
            filter_str='metric.type="custom.googleapis.com/nonexistent"',
            interval_start="2025-01-15T10:00:00Z",
            interval_end="2025-01-15T10:05:00Z",
        )

        assert results == []


# ---- Alert Policies Service Methods ----


class TestListAlertPolicies:
    def test_list_alert_policies(
        self, mock_google_client, sample_alert_policy_response
    ):
        """Test listing alert policies."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "alertPolicies": [sample_alert_policy_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        policies = service.list_alert_policies()

        mock_list.assert_called_once_with(name="projects/test-project")

        assert len(policies) == 1
        assert isinstance(policies[0], AlertPolicy)
        assert policies[0].display_name == "High CPU Alert"

    def test_list_alert_policies_empty(self, mock_google_client):
        """Test listing alert policies when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        policies = service.list_alert_policies()

        assert policies == []


class TestGetAlertPolicy:
    def test_get_alert_policy(
        self, mock_google_client, sample_alert_policy_response
    ):
        """Test getting a specific alert policy."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_alert_policy_response

        service = MonitoringService(project_id="test-project")
        policy = service.get_alert_policy("policy-123")

        mock_get.assert_called_once_with(
            name="projects/test-project/alertPolicies/policy-123"
        )

        assert isinstance(policy, AlertPolicy)
        assert policy.display_name == "High CPU Alert"

    def test_get_alert_policy_full_path(
        self, mock_google_client, sample_alert_policy_response
    ):
        """Test getting an alert policy with a full path."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_alert_policy_response

        service = MonitoringService(project_id="test-project")
        service.get_alert_policy(
            "projects/test-project/alertPolicies/policy-123"
        )

        mock_get.assert_called_with(
            name="projects/test-project/alertPolicies/policy-123"
        )

    def test_get_alert_policy_not_found(self, mock_google_client):
        """Test getting an alert policy that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404),
            content=b"Alert policy not found",
        )

        service = MonitoringService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_alert_policy("nonexistent-policy")


class TestCreateAlertPolicy:
    def test_create_alert_policy(
        self, mock_google_client, sample_alert_policy_response
    ):
        """Test creating an alert policy."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_alert_policy_response

        conditions = [
            {
                "displayName": "CPU > 90%",
                "conditionThreshold": {
                    "filter": 'metric.type="compute.googleapis.com/instance/cpu/utilization"',
                    "comparison": "COMPARISON_GT",
                    "thresholdValue": 0.9,
                    "duration": "60s",
                },
            }
        ]

        service = MonitoringService(project_id="test-project")
        policy = service.create_alert_policy(
            display_name="High CPU Alert",
            conditions=conditions,
            combiner="OR",
            enabled=True,
            notification_channels=[
                "projects/test-project/notificationChannels/channel-456"
            ],
            documentation={
                "content": "CPU usage is above threshold.",
                "mimeType": "text/markdown",
            },
        )

        mock_create.assert_called_once_with(
            name="projects/test-project",
            body={
                "displayName": "High CPU Alert",
                "conditions": conditions,
                "combiner": "OR",
                "enabled": True,
                "notificationChannels": [
                    "projects/test-project/notificationChannels/channel-456"
                ],
                "documentation": {
                    "content": "CPU usage is above threshold.",
                    "mimeType": "text/markdown",
                },
            },
        )

        assert isinstance(policy, AlertPolicy)
        assert policy.display_name == "High CPU Alert"

    def test_create_alert_policy_minimal(
        self, mock_google_client, sample_alert_policy_response
    ):
        """Test creating an alert policy with minimal arguments."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_alert_policy_response

        conditions = [{"displayName": "Simple Condition"}]

        service = MonitoringService(project_id="test-project")
        service.create_alert_policy(
            display_name="Simple Alert",
            conditions=conditions,
        )

        mock_create.assert_called_once_with(
            name="projects/test-project",
            body={
                "displayName": "Simple Alert",
                "conditions": conditions,
                "combiner": "OR",
                "enabled": True,
            },
        )


class TestUpdateAlertPolicy:
    def test_update_alert_policy(
        self, mock_google_client, sample_alert_policy_response
    ):
        """Test updating an alert policy."""
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_alert_policy_response

        service = MonitoringService(project_id="test-project")
        policy = service.update_alert_policy(
            policy_id="policy-123",
            update_fields={
                "displayName": "Updated Alert",
                "enabled": False,
            },
        )

        mock_patch.assert_called_once_with(
            name="projects/test-project/alertPolicies/policy-123",
            body={
                "name": "projects/test-project/alertPolicies/policy-123",
                "displayName": "Updated Alert",
                "enabled": False,
            },
        )

        assert isinstance(policy, AlertPolicy)


class TestDeleteAlertPolicy:
    def test_delete_alert_policy(self, mock_google_client):
        """Test deleting an alert policy."""
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = MonitoringService(project_id="test-project")
        result = service.delete_alert_policy("policy-123")

        mock_delete.assert_called_once_with(
            name="projects/test-project/alertPolicies/policy-123"
        )
        assert result is True

    def test_delete_alert_policy_full_path(self, mock_google_client):
        """Test deleting an alert policy with a full path."""
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value
            .alertPolicies.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = MonitoringService(project_id="test-project")
        service.delete_alert_policy(
            "projects/test-project/alertPolicies/policy-123"
        )

        mock_delete.assert_called_with(
            name="projects/test-project/alertPolicies/policy-123"
        )


# ---- Notification Channels Service Methods ----


class TestListNotificationChannels:
    def test_list_notification_channels(
        self, mock_google_client, sample_notification_channel_response
    ):
        """Test listing notification channels."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .notificationChannels.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "notificationChannels": [
                sample_notification_channel_response
            ]
        }

        mock_list_next = (
            mock_google_client.projects.return_value
            .notificationChannels.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        channels = service.list_notification_channels()

        mock_list.assert_called_once_with(name="projects/test-project")

        assert len(channels) == 1
        assert isinstance(channels[0], NotificationChannel)
        assert channels[0].display_name == "SRE Team Email"

    def test_list_notification_channels_empty(self, mock_google_client):
        """Test listing notification channels when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .notificationChannels.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value
            .notificationChannels.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        channels = service.list_notification_channels()

        assert channels == []


class TestGetNotificationChannel:
    def test_get_notification_channel(
        self, mock_google_client, sample_notification_channel_response
    ):
        """Test getting a specific notification channel."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value
            .notificationChannels.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = (
            sample_notification_channel_response
        )

        service = MonitoringService(project_id="test-project")
        channel = service.get_notification_channel("channel-456")

        mock_get.assert_called_once_with(
            name="projects/test-project/notificationChannels/channel-456"
        )

        assert isinstance(channel, NotificationChannel)
        assert channel.display_name == "SRE Team Email"

    def test_get_notification_channel_not_found(self, mock_google_client):
        """Test getting a notification channel that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value
            .notificationChannels.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404),
            content=b"Notification channel not found",
        )

        service = MonitoringService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_notification_channel("nonexistent-channel")


class TestCreateNotificationChannel:
    def test_create_notification_channel(
        self, mock_google_client, sample_notification_channel_response
    ):
        """Test creating a notification channel."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value
            .notificationChannels.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = (
            sample_notification_channel_response
        )

        service = MonitoringService(project_id="test-project")
        channel = service.create_notification_channel(
            display_name="SRE Team Email",
            channel_type="email",
            labels={"email_address": "sre@example.com"},
            enabled=True,
        )

        mock_create.assert_called_once_with(
            name="projects/test-project",
            body={
                "displayName": "SRE Team Email",
                "type": "email",
                "enabled": True,
                "labels": {"email_address": "sre@example.com"},
            },
        )

        assert isinstance(channel, NotificationChannel)
        assert channel.display_name == "SRE Team Email"

    def test_create_notification_channel_minimal(
        self, mock_google_client, sample_notification_channel_response
    ):
        """Test creating a notification channel with minimal arguments."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value
            .notificationChannels.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = (
            sample_notification_channel_response
        )

        service = MonitoringService(project_id="test-project")
        service.create_notification_channel(
            display_name="Simple Channel",
            channel_type="email",
        )

        mock_create.assert_called_once_with(
            name="projects/test-project",
            body={
                "displayName": "Simple Channel",
                "type": "email",
                "enabled": True,
            },
        )


class TestDeleteNotificationChannel:
    def test_delete_notification_channel(self, mock_google_client):
        """Test deleting a notification channel."""
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value
            .notificationChannels.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = MonitoringService(project_id="test-project")
        result = service.delete_notification_channel("channel-456")

        mock_delete.assert_called_once_with(
            name="projects/test-project/notificationChannels/channel-456",
            force=False,
        )
        assert result is True

    def test_delete_notification_channel_full_path(
        self, mock_google_client
    ):
        """Test deleting a notification channel with a full path."""
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value
            .notificationChannels.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = MonitoringService(project_id="test-project")
        service.delete_notification_channel(
            "projects/test-project/notificationChannels/channel-456"
        )

        mock_delete.assert_called_with(
            name="projects/test-project/notificationChannels/channel-456",
            force=False,
        )


# ---- Uptime Check Configs Service Methods ----


class TestListUptimeCheckConfigs:
    def test_list_uptime_check_configs(
        self, mock_google_client, sample_uptime_check_response
    ):
        """Test listing uptime check configs."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .uptimeCheckConfigs.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "uptimeCheckConfigs": [sample_uptime_check_response]
        }

        mock_list_next = (
            mock_google_client.projects.return_value
            .uptimeCheckConfigs.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        configs = service.list_uptime_check_configs()

        mock_list.assert_called_once_with(parent="projects/test-project")

        assert len(configs) == 1
        assert isinstance(configs[0], UptimeCheckConfig)
        assert configs[0].display_name == "Homepage Check"

    def test_list_uptime_check_configs_empty(self, mock_google_client):
        """Test listing uptime check configs when none exist."""
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value
            .uptimeCheckConfigs.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        mock_list_next = (
            mock_google_client.projects.return_value
            .uptimeCheckConfigs.return_value.list_next
        )
        mock_list_next.return_value = None

        service = MonitoringService(project_id="test-project")
        configs = service.list_uptime_check_configs()

        assert configs == []


class TestGetUptimeCheckConfig:
    def test_get_uptime_check_config(
        self, mock_google_client, sample_uptime_check_response
    ):
        """Test getting a specific uptime check config."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value
            .uptimeCheckConfigs.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_uptime_check_response

        service = MonitoringService(project_id="test-project")
        config = service.get_uptime_check_config("check-789")

        mock_get.assert_called_once_with(
            name="projects/test-project/uptimeCheckConfigs/check-789"
        )

        assert isinstance(config, UptimeCheckConfig)
        assert config.display_name == "Homepage Check"

    def test_get_uptime_check_config_full_path(
        self, mock_google_client, sample_uptime_check_response
    ):
        """Test getting an uptime check config with a full path."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value
            .uptimeCheckConfigs.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_uptime_check_response

        service = MonitoringService(project_id="test-project")
        service.get_uptime_check_config(
            "projects/test-project/uptimeCheckConfigs/check-789"
        )

        mock_get.assert_called_with(
            name="projects/test-project/uptimeCheckConfigs/check-789"
        )

    def test_get_uptime_check_config_not_found(self, mock_google_client):
        """Test getting an uptime check config that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value
            .uptimeCheckConfigs.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404),
            content=b"Uptime check config not found",
        )

        service = MonitoringService(project_id="test-project")

        with pytest.raises(ResourceNotFoundError):
            service.get_uptime_check_config("nonexistent-check")


class TestCreateUptimeCheckConfig:
    def test_create_uptime_check_config(
        self, mock_google_client, sample_uptime_check_response
    ):
        """Test creating an uptime check config."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value
            .uptimeCheckConfigs.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_uptime_check_response

        monitored_resource = {
            "type": "uptime_url",
            "labels": {"host": "example.com"},
        }
        http_check = {
            "requestMethod": "GET",
            "useSsl": True,
            "path": "/",
            "port": 443,
        }

        service = MonitoringService(project_id="test-project")
        config = service.create_uptime_check_config(
            display_name="Homepage Check",
            monitored_resource=monitored_resource,
            http_check=http_check,
            period="60s",
            timeout="10s",
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "displayName": "Homepage Check",
                "monitoredResource": monitored_resource,
                "httpCheck": http_check,
                "period": "60s",
                "timeout": "10s",
            },
        )

        assert isinstance(config, UptimeCheckConfig)
        assert config.display_name == "Homepage Check"

    def test_create_uptime_check_config_minimal(
        self, mock_google_client, sample_uptime_check_response
    ):
        """Test creating an uptime check config with minimal arguments."""
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value
            .uptimeCheckConfigs.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_uptime_check_response

        monitored_resource = {
            "type": "uptime_url",
            "labels": {"host": "example.com"},
        }

        service = MonitoringService(project_id="test-project")
        service.create_uptime_check_config(
            display_name="Simple Check",
            monitored_resource=monitored_resource,
        )

        mock_create.assert_called_once_with(
            parent="projects/test-project",
            body={
                "displayName": "Simple Check",
                "monitoredResource": monitored_resource,
            },
        )


class TestDeleteUptimeCheckConfig:
    def test_delete_uptime_check_config(self, mock_google_client):
        """Test deleting an uptime check config."""
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value
            .uptimeCheckConfigs.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = MonitoringService(project_id="test-project")
        result = service.delete_uptime_check_config("check-789")

        mock_delete.assert_called_once_with(
            name="projects/test-project/uptimeCheckConfigs/check-789"
        )
        assert result is True

    def test_delete_uptime_check_config_full_path(
        self, mock_google_client
    ):
        """Test deleting an uptime check config with a full path."""
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value
            .uptimeCheckConfigs.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = MonitoringService(project_id="test-project")
        service.delete_uptime_check_config(
            "projects/test-project/uptimeCheckConfigs/check-789"
        )

        mock_delete.assert_called_with(
            name="projects/test-project/uptimeCheckConfigs/check-789"
        )
