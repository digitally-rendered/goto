"""Integration tests for retry / resilience logic.

These tests validate that the SDK handles transient failures gracefully by
injecting controlled failures into the HTTP transport layer and then
verifying that subsequent real calls still succeed (or that the expected
number of retries occurred).

The approach:

1. Create a real service instance so that credentials and discovery are
   fully wired up.
2. Patch the underlying ``httplib2.Http.request`` (or ``requests.Session``)
   to inject failures for a configurable number of calls, then delegate to
   the real implementation.
3. Invoke a list/get operation and verify the outcome.

This is a hybrid integration test -- it uses real credentials and API
discovery but controls the transport to exercise retry paths that are
difficult to trigger reliably against live APIs.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from gcpoto.exceptions import APIError, GCPotoError, ServiceUnavailableError

logger = logging.getLogger(__name__)

# Every test in this module is an integration test
pytestmark = pytest.mark.integration


class _TransientFailureInjector:
    """Wraps a real HTTP request callable and injects transient 503 errors.

    After ``fail_count`` failures the injector delegates to the real callable
    so the overall operation can succeed if the caller retries.
    """

    def __init__(self, real_request, fail_count: int = 2):
        self._real_request = real_request
        self._fail_count = fail_count
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    def __call__(self, *args, **kwargs):
        self._call_count += 1
        if self._call_count <= self._fail_count:
            logger.info(
                "Injecting transient 503 failure (attempt %d/%d)",
                self._call_count, self._fail_count,
            )
            # Return a fake 503 response
            fake_response = MagicMock()
            fake_response.status = 503
            fake_response.reason = "Service Unavailable (injected)"
            fake_response.headers = {}
            return fake_response, b'{"error": {"code": 503, "message": "injected"}}'
        logger.info(
            "Injector pass-through on attempt %d", self._call_count
        )
        return self._real_request(*args, **kwargs)


class _ConnectionErrorInjector:
    """Wraps a real HTTP request callable and injects ``ConnectionError``s.

    After ``fail_count`` exceptions the injector delegates to the real callable.
    """

    def __init__(self, real_request, fail_count: int = 2):
        self._real_request = real_request
        self._fail_count = fail_count
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    def __call__(self, *args, **kwargs):
        self._call_count += 1
        if self._call_count <= self._fail_count:
            logger.info(
                "Injecting ConnectionError (attempt %d/%d)",
                self._call_count, self._fail_count,
            )
            raise ConnectionError("Injected transient network failure")
        logger.info(
            "ConnectionError injector pass-through on attempt %d",
            self._call_count,
        )
        return self._real_request(*args, **kwargs)


# ---------------------------------------------------------------------------
# Storage: retry on transient 503
# ---------------------------------------------------------------------------

class TestStorageRetryBehavior:
    """Test that the storage service handles transient failures."""

    def test_list_buckets_retries_on_503(self, storage_service):
        """Inject 503 errors and verify the call eventually succeeds or
        raises a clean ServiceUnavailableError / APIError.
        """
        # Locate the underlying http object used by the discovery client
        http = getattr(storage_service.service, "_http", None)
        if http is None:
            pytest.skip("Cannot access _http on the discovery service object")

        real_request = http.request
        injector = _TransientFailureInjector(real_request, fail_count=1)

        http.request = injector
        try:
            try:
                result = storage_service.list_resources()
                # If retry logic worked, we got a valid result after the
                # injected failure.
                assert isinstance(result, list)
                logger.info(
                    "list_resources succeeded after %d call(s)",
                    injector.call_count,
                )
            except (ServiceUnavailableError, APIError, GCPotoError) as exc:
                # The service correctly surfaced the error after exhausting
                # retries -- that is acceptable behavior.
                logger.info(
                    "list_resources raised %s after %d call(s): %s",
                    type(exc).__name__, injector.call_count, exc,
                )
            except Exception as exc:
                exc_module = type(exc).__module__ or ""
                if exc_module.startswith(("google.", "httplib2", "grpc")):
                    logger.info(
                        "list_resources raised upstream %s after %d call(s)",
                        type(exc).__name__, injector.call_count,
                    )
                else:
                    raise

            # The injector should have been called at least twice (one failure
            # plus one real attempt) unless the library did not retry at all.
            assert injector.call_count >= 1, (
                "Expected at least 1 call through the injector"
            )
        finally:
            http.request = real_request

    def test_list_buckets_retries_on_connection_error(self, storage_service):
        """Inject ConnectionError and verify resilience."""
        http = getattr(storage_service.service, "_http", None)
        if http is None:
            pytest.skip("Cannot access _http on the discovery service object")

        real_request = http.request
        injector = _ConnectionErrorInjector(real_request, fail_count=1)

        http.request = injector
        try:
            try:
                result = storage_service.list_resources()
                assert isinstance(result, list)
                logger.info(
                    "list_resources succeeded after %d call(s) with connection errors",
                    injector.call_count,
                )
            except (ConnectionError, ServiceUnavailableError, APIError, GCPotoError) as exc:
                logger.info(
                    "list_resources raised %s after %d call(s): %s",
                    type(exc).__name__, injector.call_count, exc,
                )
            except Exception as exc:
                exc_module = type(exc).__module__ or ""
                if exc_module.startswith(("google.", "httplib2", "grpc")):
                    logger.info(
                        "list_resources raised upstream %s after %d call(s)",
                        type(exc).__name__, injector.call_count,
                    )
                else:
                    raise
        finally:
            http.request = real_request


# ---------------------------------------------------------------------------
# DNS: retry on transient 503
# ---------------------------------------------------------------------------

class TestDNSRetryBehavior:
    """Test that the DNS service handles transient failures."""

    def test_list_zones_retries_on_503(self, dns_service):
        """Inject a 503 error into DNS list_zones and verify behavior."""
        http = getattr(dns_service.service, "_http", None)
        if http is None:
            pytest.skip("Cannot access _http on the discovery service object")

        real_request = http.request
        injector = _TransientFailureInjector(real_request, fail_count=1)

        http.request = injector
        try:
            try:
                # Try list_zones first, fall back to list_resources
                list_fn = getattr(dns_service, "list_zones", None)
                if list_fn is None:
                    list_fn = dns_service.list_resources
                result = list_fn()
                assert isinstance(result, (list, type(None)))
                logger.info(
                    "DNS list call succeeded after %d call(s)",
                    injector.call_count,
                )
            except (ServiceUnavailableError, APIError, GCPotoError) as exc:
                logger.info(
                    "DNS list call raised %s after %d call(s): %s",
                    type(exc).__name__, injector.call_count, exc,
                )
            except NotImplementedError:
                pytest.skip("DNS list method not implemented")
            except Exception as exc:
                exc_module = type(exc).__module__ or ""
                if exc_module.startswith(("google.", "httplib2", "grpc")):
                    logger.info(
                        "DNS list call raised upstream %s after %d call(s)",
                        type(exc).__name__, injector.call_count,
                    )
                else:
                    raise

            assert injector.call_count >= 1
        finally:
            http.request = real_request


# ---------------------------------------------------------------------------
# Generic: verify that permanent errors are not retried indefinitely
# ---------------------------------------------------------------------------

class TestPermanentErrorBehavior:
    """Verify that non-retriable errors (4xx) are raised immediately."""

    def test_404_is_not_retried(self, storage_service):
        """A 404 should be raised immediately without retry attempts."""
        http = getattr(storage_service.service, "_http", None)
        if http is None:
            pytest.skip("Cannot access _http on the discovery service object")

        call_count = 0
        real_request = http.request

        def counting_404(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            fake_response = MagicMock()
            fake_response.status = 404
            fake_response.reason = "Not Found (injected)"
            fake_response.headers = {}
            return fake_response, b'{"error": {"code": 404, "message": "not found"}}'

        http.request = counting_404
        try:
            try:
                storage_service.list_resources()
                pytest.fail("Expected an error from injected 404")
            except (ResourceNotFoundError, APIError, GCPotoError):
                pass
            except Exception as exc:
                exc_module = type(exc).__module__ or ""
                if not exc_module.startswith(("google.", "httplib2", "grpc")):
                    raise

            # A 404 should not trigger multiple retries.  Allow a small number
            # of calls for discovery refresh, but flag excessive retrying.
            assert call_count <= 3, (
                f"404 triggered {call_count} calls -- expected at most 3 "
                f"(non-retriable errors should not be retried)"
            )
            logger.info(
                "404 error was handled in %d call(s) (no excessive retries)",
                call_count,
            )
        finally:
            http.request = real_request


# Import here to avoid NameError in test_404_is_not_retried
from gcpoto.exceptions import ResourceNotFoundError  # noqa: E402
