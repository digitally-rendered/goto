"""Tests for the base service class retry, error handling, and LRO support."""

import time
import unittest.mock as mock

import httplib2
import pytest
from googleapiclient.errors import HttpError

from gcpoto.exceptions import (
    APIError,
    AuthenticationError,
    PermissionDeniedError,
    QuotaExceededError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    ValidationError,
)
from gcpoto.models.base import GCPResource
from gcpoto.services.base import GCPService


def _make_http_error(status: int, message: str = "error") -> HttpError:
    """Create an HttpError with the given status code."""
    resp = httplib2.Response({"status": status})
    return HttpError(resp, message.encode("utf-8"))


@pytest.fixture
def service():
    """Create a GCPService instance with mocked discovery."""
    with mock.patch("gcpoto.services.base.discovery.build") as mock_build:
        mock_api = mock.MagicMock()
        mock_build.return_value = mock_api
        svc = GCPService(
            project_id="test-project",
            service_name="compute",
            version="v1",
            num_retries=3,
            retry_delay=0.01,  # fast retries for tests
        )
        svc.service = mock_api
        yield svc


# ---------- __init__ parameters ----------


class TestInitParameters:
    def test_default_retry_params(self):
        with mock.patch("gcpoto.services.base.discovery.build"):
            svc = GCPService(
                project_id="p", service_name="compute", version="v1"
            )
        assert svc.num_retries == 3
        assert svc.retry_delay == 1.0

    def test_custom_retry_params(self):
        with mock.patch("gcpoto.services.base.discovery.build"):
            svc = GCPService(
                project_id="p",
                service_name="compute",
                version="v1",
                num_retries=5,
                retry_delay=2.0,
            )
        assert svc.num_retries == 5
        assert svc.retry_delay == 2.0


# ---------- _execute_with_retry ----------


class TestExecuteWithRetry:
    def test_success_on_first_attempt(self, service):
        request = mock.MagicMock()
        request.execute.return_value = {"id": "1"}
        result = service._execute_with_retry(request)
        assert result == {"id": "1"}
        assert request.execute.call_count == 1

    def test_retry_then_succeed(self, service):
        """Fail with a retryable error twice, then succeed."""
        request = mock.MagicMock()
        request.execute.side_effect = [
            _make_http_error(503),
            _make_http_error(503),
            {"id": "1"},
        ]
        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._execute_with_retry(request)
        assert result == {"id": "1"}
        assert request.execute.call_count == 3

    def test_all_retries_exhausted(self, service):
        """When all retries are exhausted, raise the mapped exception."""
        request = mock.MagicMock()
        request.execute.side_effect = _make_http_error(503)
        with mock.patch("gcpoto.services.base.time.sleep"):
            with pytest.raises(ServiceUnavailableError):
                service._execute_with_retry(request)
        # 1 initial + 3 retries = 4 attempts
        assert request.execute.call_count == 4

    @pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
    def test_retryable_status_codes(self, service, status):
        """All retryable status codes should be retried."""
        request = mock.MagicMock()
        request.execute.side_effect = [
            _make_http_error(status),
            {"ok": True},
        ]
        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._execute_with_retry(request)
        assert result == {"ok": True}
        assert request.execute.call_count == 2

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 409])
    def test_non_retryable_status_codes_fail_immediately(self, service, status):
        """Client errors should not be retried."""
        request = mock.MagicMock()
        request.execute.side_effect = _make_http_error(status)
        with mock.patch("gcpoto.services.base.time.sleep"):
            with pytest.raises(Exception):
                service._execute_with_retry(request)
        assert request.execute.call_count == 1

    def test_backoff_timing_increases(self, service):
        """Verify that sleep delays increase with each attempt."""
        request = mock.MagicMock()
        request.execute.side_effect = [
            _make_http_error(503),
            _make_http_error(503),
            _make_http_error(503),
            _make_http_error(503),  # exhausted
        ]
        with mock.patch("gcpoto.services.base.time.sleep") as mock_sleep:
            with mock.patch("gcpoto.services.base.random.uniform", return_value=0):
                with pytest.raises(ServiceUnavailableError):
                    service._execute_with_retry(request)

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        # With base 0.01 and no jitter: 0.01*2^0, 0.01*2^1, 0.01*2^2
        assert len(delays) == 3
        assert delays[0] < delays[1] < delays[2]

    def test_connection_error_retried(self, service):
        """ConnectionError should be retried."""
        request = mock.MagicMock()
        request.execute.side_effect = [
            ConnectionError("reset"),
            {"ok": True},
        ]
        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._execute_with_retry(request)
        assert result == {"ok": True}

    def test_connection_error_exhausted(self, service):
        """ConnectionError should raise APIError when retries are exhausted."""
        request = mock.MagicMock()
        request.execute.side_effect = ConnectionError("reset")
        with mock.patch("gcpoto.services.base.time.sleep"):
            with pytest.raises(APIError, match="reset"):
                service._execute_with_retry(request)

    def test_os_error_retried(self, service):
        """OSError (e.g. broken pipe) should be retried."""
        request = mock.MagicMock()
        request.execute.side_effect = [
            OSError("Broken pipe"),
            {"ok": True},
        ]
        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._execute_with_retry(request)
        assert result == {"ok": True}


# ---------- _handle_http_error ----------


class TestHandleHttpError:
    def test_400_raises_validation_error(self, service):
        with pytest.raises(ValidationError):
            service._handle_http_error(_make_http_error(400))

    def test_401_raises_authentication_error(self, service):
        with pytest.raises(AuthenticationError):
            service._handle_http_error(_make_http_error(401))

    def test_403_raises_permission_denied_error(self, service):
        with pytest.raises(PermissionDeniedError):
            service._handle_http_error(_make_http_error(403))

    def test_404_raises_resource_not_found_error(self, service):
        with pytest.raises(ResourceNotFoundError) as exc_info:
            service._handle_http_error(
                _make_http_error(404), resource_type="bucket", resource_id="my-bucket"
            )
        assert exc_info.value.resource_type == "bucket"
        assert exc_info.value.resource_id == "my-bucket"

    def test_404_default_resource_params(self, service):
        with pytest.raises(ResourceNotFoundError) as exc_info:
            service._handle_http_error(_make_http_error(404))
        assert exc_info.value.resource_type == "resource"
        assert exc_info.value.resource_id == "unknown"

    def test_409_raises_resource_already_exists_error(self, service):
        with pytest.raises(ResourceAlreadyExistsError):
            service._handle_http_error(_make_http_error(409))

    def test_429_raises_quota_exceeded_error(self, service):
        with pytest.raises(QuotaExceededError):
            service._handle_http_error(_make_http_error(429))

    def test_503_raises_service_unavailable_error(self, service):
        with pytest.raises(ServiceUnavailableError):
            service._handle_http_error(_make_http_error(503))

    def test_unknown_status_raises_api_error(self, service):
        with pytest.raises(APIError) as exc_info:
            service._handle_http_error(_make_http_error(418))
        assert exc_info.value.status_code == 418

    def test_preserves_original_error_as_cause(self, service):
        original = _make_http_error(400)
        with pytest.raises(ValidationError) as exc_info:
            service._handle_http_error(original)
        assert exc_info.value.__cause__ is original


# ---------- _wait_for_operation ----------


class TestWaitForOperation:
    def test_already_done(self, service):
        """Operation that is already DONE should return immediately."""
        op = {"name": "op-1", "status": "DONE"}
        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._wait_for_operation(op, poll_interval=0.01)
        assert result == op

    def test_done_via_done_field(self, service):
        """Supports the 'done' boolean field used by some APIs."""
        op = {"name": "op-1", "done": True}
        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._wait_for_operation(op, poll_interval=0.01)
        assert result == op

    def test_polls_until_done_global(self, service):
        """Should poll globalOperations until status is DONE."""
        initial_op = {"name": "op-1", "status": "RUNNING"}
        pending_op = {"name": "op-1", "status": "RUNNING"}
        done_op = {"name": "op-1", "status": "DONE"}

        mock_request = mock.MagicMock()
        mock_request.execute.side_effect = [pending_op, done_op]
        service.service.globalOperations().get.return_value = mock_request

        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._wait_for_operation(
                initial_op, poll_interval=0.01, timeout=10
            )
        assert result["status"] == "DONE"
        service.service.globalOperations().get.assert_called_with(
            project="test-project", operation="op-1"
        )

    def test_polls_zone_operations(self, service):
        """Should use zoneOperations when zone is specified."""
        initial_op = {"name": "op-1", "status": "RUNNING"}
        done_op = {"name": "op-1", "status": "DONE"}

        mock_request = mock.MagicMock()
        mock_request.execute.return_value = done_op
        service.service.zoneOperations().get.return_value = mock_request

        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._wait_for_operation(
                initial_op, zone="us-central1-a", poll_interval=0.01, timeout=10
            )
        assert result["status"] == "DONE"
        service.service.zoneOperations().get.assert_called_with(
            project="test-project", zone="us-central1-a", operation="op-1"
        )

    def test_polls_region_operations(self, service):
        """Should use regionOperations when location is specified."""
        initial_op = {"name": "op-1", "status": "RUNNING"}
        done_op = {"name": "op-1", "status": "DONE"}

        mock_request = mock.MagicMock()
        mock_request.execute.return_value = done_op
        service.service.regionOperations().get.return_value = mock_request

        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._wait_for_operation(
                initial_op, location="us-central1", poll_interval=0.01, timeout=10
            )
        assert result["status"] == "DONE"
        service.service.regionOperations().get.assert_called_with(
            project="test-project", region="us-central1", operation="op-1"
        )

    def test_operation_error(self, service):
        """Should raise APIError when operation has an error field."""
        op = {
            "name": "op-1",
            "status": "DONE",
            "error": {"errors": [{"code": "QUOTA_EXCEEDED"}]},
        }
        with mock.patch("gcpoto.services.base.time.sleep"):
            with pytest.raises(APIError, match="op-1 failed"):
                service._wait_for_operation(op, poll_interval=0.01)

    def test_operation_timeout(self, service):
        """Should raise APIError when timeout is exceeded."""
        op = {"name": "op-1", "status": "RUNNING"}

        mock_request = mock.MagicMock()
        mock_request.execute.return_value = {"name": "op-1", "status": "RUNNING"}
        service.service.globalOperations().get.return_value = mock_request

        with mock.patch("gcpoto.services.base.time.sleep"):
            with mock.patch(
                "gcpoto.services.base.time.monotonic",
                side_effect=[0, 0, 0.01, 999],
            ):
                with pytest.raises(APIError, match="timed out"):
                    service._wait_for_operation(
                        op, timeout=0.5, poll_interval=0.01
                    )

    def test_uses_custom_project_id(self, service):
        """Should use provided project_id over self.project_id."""
        initial_op = {"name": "op-1", "status": "RUNNING"}
        done_op = {"name": "op-1", "status": "DONE"}

        mock_request = mock.MagicMock()
        mock_request.execute.return_value = done_op
        service.service.globalOperations().get.return_value = mock_request

        with mock.patch("gcpoto.services.base.time.sleep"):
            service._wait_for_operation(
                initial_op,
                project_id="other-project",
                poll_interval=0.01,
                timeout=10,
            )
        service.service.globalOperations().get.assert_called_with(
            project="other-project", operation="op-1"
        )


# ---------- Additional retry / error scenarios ----------


class TestAdditionalRetryScenarios:
    """Extended tests for retry logic edge cases and specific error paths."""

    def test_execute_retry_on_503_individually(self, service):
        """503 Service Unavailable triggers retry, then succeeds (non-parametrized)."""
        request = mock.MagicMock()
        request.execute.side_effect = [
            _make_http_error(503, "Service Unavailable"),
            {"id": "1", "name": "ok"},
        ]
        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._execute_with_retry(request)
        assert result == {"id": "1", "name": "ok"}
        assert request.execute.call_count == 2

    def test_execute_retry_on_429_individually(self, service):
        """429 Too Many Requests triggers retry, then succeeds."""
        request = mock.MagicMock()
        request.execute.side_effect = [
            _make_http_error(429, "Rate limit exceeded"),
            {"id": "1", "name": "ok"},
        ]
        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._execute_with_retry(request)
        assert result == {"id": "1", "name": "ok"}
        assert request.execute.call_count == 2

    def test_execute_retry_on_500_individually(self, service):
        """500 Internal Server Error triggers retry, then succeeds."""
        request = mock.MagicMock()
        request.execute.side_effect = [
            _make_http_error(500, "Internal Server Error"),
            {"id": "1", "name": "ok"},
        ]
        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._execute_with_retry(request)
        assert result == {"id": "1", "name": "ok"}
        assert request.execute.call_count == 2

    def test_execute_no_retry_on_400_individually(self, service):
        """400 raises ValidationError immediately, no retry."""
        request = mock.MagicMock()
        request.execute.side_effect = _make_http_error(400, "Bad Request")
        with pytest.raises(ValidationError):
            service._execute_with_retry(request)
        request.execute.assert_called_once()

    def test_execute_no_retry_on_401_individually(self, service):
        """401 raises AuthenticationError immediately, no retry."""
        request = mock.MagicMock()
        request.execute.side_effect = _make_http_error(401, "Unauthorized")
        with pytest.raises(AuthenticationError):
            service._execute_with_retry(request)
        request.execute.assert_called_once()

    def test_execute_no_retry_on_403_individually(self, service):
        """403 raises PermissionDeniedError immediately, no retry."""
        request = mock.MagicMock()
        request.execute.side_effect = _make_http_error(403, "Forbidden")
        with pytest.raises(PermissionDeniedError):
            service._execute_with_retry(request)
        request.execute.assert_called_once()

    def test_execute_no_retry_on_404_individually(self, service):
        """404 raises ResourceNotFoundError immediately, no retry."""
        request = mock.MagicMock()
        request.execute.side_effect = _make_http_error(404, "Not Found")
        with pytest.raises(ResourceNotFoundError):
            service._execute_with_retry(request)
        request.execute.assert_called_once()

    def test_execute_no_retry_on_409_individually(self, service):
        """409 raises ResourceAlreadyExistsError immediately, no retry."""
        request = mock.MagicMock()
        request.execute.side_effect = _make_http_error(409, "Conflict")
        with pytest.raises(ResourceAlreadyExistsError):
            service._execute_with_retry(request)
        request.execute.assert_called_once()

    def test_execute_retry_on_timeout_error(self, service):
        """TimeoutError (subclass of OSError) triggers retry, then succeeds."""
        request = mock.MagicMock()
        request.execute.side_effect = [
            TimeoutError("Connection timed out"),
            {"id": "1", "name": "ok"},
        ]
        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._execute_with_retry(request)
        assert result == {"id": "1", "name": "ok"}
        assert request.execute.call_count == 2

    def test_execute_max_retries_zero_means_no_retry(self):
        """num_retries=0 means no retry, immediate failure on retryable error."""
        with mock.patch("gcpoto.services.base.discovery.build"):
            svc = GCPService(
                project_id="test-project",
                service_name="compute",
                version="v1",
                num_retries=0,
                retry_delay=0.01,
            )
        request = mock.MagicMock()
        request.execute.side_effect = _make_http_error(503, "Unavailable")
        with pytest.raises(ServiceUnavailableError):
            svc._execute_with_retry(request)
        request.execute.assert_called_once()

    def test_execute_retry_exhausted_429_raises_quota_error(self, service):
        """All retries exhausted on 429 raises QuotaExceededError."""
        request = mock.MagicMock()
        request.execute.side_effect = _make_http_error(429, "Rate limit")
        with mock.patch("gcpoto.services.base.time.sleep"):
            with pytest.raises(QuotaExceededError):
                service._execute_with_retry(request)
        assert request.execute.call_count == 4  # 1 initial + 3 retries

    def test_retryable_then_non_retryable_stops(self, service):
        """Transient error followed by client error stops retrying immediately."""
        request = mock.MagicMock()
        request.execute.side_effect = [
            _make_http_error(503, "Unavailable"),
            _make_http_error(404, "Not Found"),
        ]
        with mock.patch("gcpoto.services.base.time.sleep"):
            with pytest.raises(ResourceNotFoundError):
                service._execute_with_retry(request)
        assert request.execute.call_count == 2

    def test_connection_then_http_error_then_success(self, service):
        """Mix of connection and HTTP transient errors, then success."""
        request = mock.MagicMock()
        request.execute.side_effect = [
            ConnectionError("Reset"),
            _make_http_error(503, "Unavailable"),
            {"id": "1", "name": "ok"},
        ]
        with mock.patch("gcpoto.services.base.time.sleep"):
            result = service._execute_with_retry(request)
        assert result == {"id": "1", "name": "ok"}
        assert request.execute.call_count == 3

    def test_retryable_status_codes_class_attribute(self, service):
        """Verify the RETRYABLE_STATUS_CODES class attribute contains expected codes."""
        assert service.RETRYABLE_STATUS_CODES == {429, 500, 502, 503, 504}

    def test_handle_http_error_preserves_cause_chain(self, service):
        """All mapped exceptions preserve the original HttpError as __cause__."""
        for status, exc_type in [
            (400, ValidationError),
            (401, AuthenticationError),
            (403, PermissionDeniedError),
            (404, ResourceNotFoundError),
            (409, ResourceAlreadyExistsError),
            (429, QuotaExceededError),
            (503, ServiceUnavailableError),
            (418, APIError),
        ]:
            original = _make_http_error(status)
            with pytest.raises(exc_type) as exc_info:
                service._handle_http_error(original)
            assert exc_info.value.__cause__ is original, (
                "Exception for status %d should chain the original HttpError" % status
            )

    @mock.patch("gcpoto.services.base.random.uniform", return_value=0)
    @mock.patch("gcpoto.services.base.time.sleep")
    def test_backoff_delay_cap_at_60(self, mock_sleep, mock_random):
        """Verify backoff delay is capped at 60 seconds (max_delay)."""
        with mock.patch("gcpoto.services.base.discovery.build"):
            svc = GCPService(
                project_id="test-project",
                service_name="compute",
                version="v1",
                num_retries=10,
                retry_delay=100.0,  # Large base to exceed cap
            )
        request = mock.MagicMock()
        request.execute.side_effect = _make_http_error(503, "Unavailable")
        with pytest.raises(ServiceUnavailableError):
            svc._execute_with_retry(request)

        # All delays should be capped at 60.0 (with zero jitter)
        for c in mock_sleep.call_args_list:
            assert c.args[0] <= 60.0, (
                "Backoff delay %s exceeds 60s cap" % c.args[0]
            )
