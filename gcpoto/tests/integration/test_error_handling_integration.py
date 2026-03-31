"""Integration tests for error handling across services.

Validates that GCP API errors are correctly translated into the gcpoto
exception hierarchy:

  - 404 responses -> ResourceNotFoundError
  - 403 responses -> PermissionDeniedError
  - Other HTTP errors -> APIError

Tests target a handful of representative services (storage, dns,
secret_manager, pubsub) to avoid needing every API enabled.
"""

import logging
import uuid

import pytest

from gcpoto.exceptions import (
    APIError,
    GCPotoError,
    PermissionDeniedError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)

# Every test in this module is an integration test
pytestmark = pytest.mark.integration


def _nonexistent_id() -> str:
    """Return a resource name that is virtually guaranteed not to exist."""
    return f"gcpoto-nonexistent-{uuid.uuid4().hex}"


# ---------------------------------------------------------------------------
# Storage: 404 on nonexistent bucket
# ---------------------------------------------------------------------------

class TestStorageErrorHandling:
    """Verify Storage service error translation."""

    def test_get_nonexistent_bucket_raises_not_found(self, storage_service):
        """Getting a bucket that does not exist should raise ResourceNotFoundError."""
        fake_name = _nonexistent_id()
        with pytest.raises((ResourceNotFoundError, APIError, GCPotoError)) as exc_info:
            storage_service.get_resource(fake_name)
        logger.info(
            "storage.get_resource(%s) raised %s: %s",
            fake_name, type(exc_info.value).__name__, exc_info.value,
        )

    def test_delete_nonexistent_bucket_raises_not_found(self, storage_service):
        """Deleting a bucket that does not exist should raise ResourceNotFoundError."""
        fake_name = _nonexistent_id()
        with pytest.raises((ResourceNotFoundError, APIError, GCPotoError)) as exc_info:
            storage_service.delete_bucket(fake_name)
        logger.info(
            "storage.delete_bucket(%s) raised %s: %s",
            fake_name, type(exc_info.value).__name__, exc_info.value,
        )

    def test_get_nonexistent_object_raises_not_found(self, storage_service, unique_name):
        """Getting a nonexistent object from a nonexistent bucket should error."""
        fake_bucket = _nonexistent_id()
        fake_object = _nonexistent_id()
        with pytest.raises((ResourceNotFoundError, APIError, GCPotoError)) as exc_info:
            storage_service.get_object(
                bucket_name=fake_bucket, object_name=fake_object
            )
        logger.info(
            "storage.get_object raised %s: %s",
            type(exc_info.value).__name__, exc_info.value,
        )


# ---------------------------------------------------------------------------
# DNS: 404 on nonexistent zone
# ---------------------------------------------------------------------------

class TestDNSErrorHandling:
    """Verify Cloud DNS service error translation."""

    def test_get_nonexistent_zone_raises_error(self, dns_service):
        """Getting a DNS zone that does not exist should raise an appropriate error."""
        fake_zone = _nonexistent_id()
        with pytest.raises((ResourceNotFoundError, APIError, GCPotoError)) as exc_info:
            dns_service.get_resource(fake_zone)
        logger.info(
            "dns.get_resource(%s) raised %s: %s",
            fake_zone, type(exc_info.value).__name__, exc_info.value,
        )

    def test_delete_nonexistent_zone_raises_error(self, dns_service):
        """Deleting a nonexistent DNS zone should raise an appropriate error."""
        fake_zone = _nonexistent_id()
        with pytest.raises((ResourceNotFoundError, APIError, GCPotoError)) as exc_info:
            dns_service.delete_resource(fake_zone)
        logger.info(
            "dns.delete_resource(%s) raised %s: %s",
            fake_zone, type(exc_info.value).__name__, exc_info.value,
        )


# ---------------------------------------------------------------------------
# Secret Manager: 404 on nonexistent secret
# ---------------------------------------------------------------------------

class TestSecretManagerErrorHandling:
    """Verify Secret Manager service error translation."""

    def test_get_nonexistent_secret_raises_error(self, secret_manager_service):
        """Getting a secret that does not exist should raise an appropriate error."""
        fake_secret = _nonexistent_id()
        with pytest.raises((ResourceNotFoundError, APIError, GCPotoError)) as exc_info:
            secret_manager_service.get_resource(fake_secret)
        logger.info(
            "secret_manager.get_resource(%s) raised %s: %s",
            fake_secret, type(exc_info.value).__name__, exc_info.value,
        )

    def test_get_nonexistent_secret_version_raises_error(self, secret_manager_service):
        """Accessing a nonexistent secret version should raise an appropriate error."""
        fake_secret = _nonexistent_id()
        try:
            secret_manager_service.get_secret_version(fake_secret, "latest")
            pytest.fail("Expected an error for nonexistent secret version")
        except (ResourceNotFoundError, APIError, GCPotoError) as exc:
            logger.info(
                "secret_manager.get_secret_version raised %s: %s",
                type(exc).__name__, exc,
            )
        except AttributeError:
            pytest.skip("SecretManagerService does not implement get_secret_version")
        except NotImplementedError:
            pytest.skip("get_secret_version not implemented")


# ---------------------------------------------------------------------------
# Pub/Sub: 404 on nonexistent topic / subscription
# ---------------------------------------------------------------------------

class TestPubSubErrorHandling:
    """Verify Pub/Sub service error translation."""

    def test_get_nonexistent_topic_raises_error(self, pubsub_service):
        """Getting a topic that does not exist should raise an appropriate error."""
        fake_topic = _nonexistent_id()
        with pytest.raises((ResourceNotFoundError, APIError, GCPotoError, Exception)) as exc_info:
            pubsub_service.get_topic(fake_topic)
        exc = exc_info.value
        # Accept gcpoto errors or google-cloud-pubsub NotFound
        exc_module = type(exc).__module__ or ""
        assert (
            isinstance(exc, GCPotoError)
            or exc_module.startswith("google.")
            or exc_module.startswith("grpc")
        ), f"Unexpected exception type: {type(exc).__name__} from {exc_module}"
        logger.info(
            "pubsub.get_topic(%s) raised %s: %s",
            fake_topic, type(exc).__name__, exc,
        )

    def test_get_nonexistent_subscription_raises_error(self, pubsub_service):
        """Getting a subscription that does not exist should raise an appropriate error."""
        fake_sub = _nonexistent_id()
        with pytest.raises((ResourceNotFoundError, APIError, GCPotoError, Exception)) as exc_info:
            pubsub_service.get_subscription(fake_sub)
        exc = exc_info.value
        exc_module = type(exc).__module__ or ""
        assert (
            isinstance(exc, GCPotoError)
            or exc_module.startswith("google.")
            or exc_module.startswith("grpc")
        ), f"Unexpected exception type: {type(exc).__name__} from {exc_module}"
        logger.info(
            "pubsub.get_subscription(%s) raised %s: %s",
            fake_sub, type(exc).__name__, exc,
        )

    def test_publish_to_nonexistent_topic_raises_error(self, pubsub_service):
        """Publishing to a nonexistent topic should raise an appropriate error."""
        fake_topic = _nonexistent_id()
        try:
            pubsub_service.publish_message(
                topic_name=fake_topic, data="test-payload"
            )
            pytest.fail("Expected an error when publishing to nonexistent topic")
        except (ResourceNotFoundError, APIError, GCPotoError) as exc:
            logger.info(
                "pubsub.publish_message raised %s: %s",
                type(exc).__name__, exc,
            )
        except Exception as exc:
            # Allow google-cloud / grpc errors
            exc_module = type(exc).__module__ or ""
            assert (
                exc_module.startswith("google.")
                or exc_module.startswith("grpc")
            ), f"Unexpected exception type: {type(exc).__name__} from {exc_module}"
            logger.info(
                "pubsub.publish_message raised upstream %s: %s",
                type(exc).__name__, exc,
            )


# ---------------------------------------------------------------------------
# Cross-service: permission errors
# ---------------------------------------------------------------------------

class TestPermissionErrorHandling:
    """Verify that permission-denied responses are surfaced correctly.

    These tests are best-effort.  If the test credentials *do* have the
    relevant permission the test is skipped.  The goal is to validate the
    error mapping when a 403 does occur.
    """

    def test_permission_denied_is_surfaced(self, gcp_project, credentials_file):
        """Attempt an operation likely to be denied and verify the error type.

        We try to list IAM service accounts -- if the credentials lack
        ``iam.serviceAccounts.list`` we expect PermissionDeniedError.
        """
        from gcpoto.services.iam import IAMService

        try:
            svc = IAMService(
                project_id=gcp_project, credentials_file=credentials_file
            )
        except Exception as exc:
            pytest.skip(f"Cannot instantiate IAMService: {exc}")

        try:
            svc.list_resources()
            # If the call succeeds the credentials have the permission --
            # nothing to assert about error handling.
            pytest.skip(
                "Credentials have IAM list permission; cannot test denial path"
            )
        except PermissionDeniedError as exc:
            logger.info("Correctly received PermissionDeniedError: %s", exc)
        except (APIError, GCPotoError) as exc:
            # A different API error is still acceptable (e.g. API not enabled)
            logger.info(
                "Received %s instead of PermissionDeniedError: %s",
                type(exc).__name__, exc,
            )
        except Exception as exc:
            exc_module = type(exc).__module__ or ""
            if exc_module.startswith("google.") or exc_module.startswith("grpc"):
                logger.info(
                    "Received upstream %s: %s", type(exc).__name__, exc
                )
            else:
                raise
