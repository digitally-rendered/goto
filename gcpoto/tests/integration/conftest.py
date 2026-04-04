"""Configuration and fixtures for integration tests.

This module provides a robust framework for integration testing against real
GCP APIs. Tests are controlled by environment variables:

    GCP_PROJECT_ID or GCPOTO_TEST_PROJECT_ID  - Required project ID
    GCP_CREDENTIALS_FILE or GOOGLE_APPLICATION_CREDENTIALS - Optional creds path
    RUN_INTEGRATION_TESTS=1 - Must be set to run integration tests

Usage:
    RUN_INTEGRATION_TESTS=1 GCP_PROJECT_ID=my-project pytest -m integration
"""

import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import pytest

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Gate: skip the entire integration suite unless explicitly opted in
# ---------------------------------------------------------------------------

def _should_run_integration_tests() -> bool:
    """Check whether integration tests are enabled via environment."""
    return os.environ.get("RUN_INTEGRATION_TESTS", "0") == "1"


def pytest_collection_modifyitems(config, items):
    """Automatically skip integration-marked tests when not opted in."""
    if _should_run_integration_tests():
        return
    skip_integration = pytest.mark.skip(
        reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable."
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def gcp_project() -> str:
    """Read the GCP project ID from the environment or skip the test session.

    Checks GCP_PROJECT_ID first, then GCPOTO_TEST_PROJECT_ID, then
    GOOGLE_CLOUD_PROJECT.

    Returns:
        The GCP project ID string.
    """
    project_id = (
        os.environ.get("GCP_PROJECT_ID")
        or os.environ.get("GCPOTO_TEST_PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
    )
    if not project_id:
        pytest.skip(
            "Integration tests require a GCP project ID. "
            "Set GCP_PROJECT_ID, GCPOTO_TEST_PROJECT_ID, or GOOGLE_CLOUD_PROJECT."
        )
    return project_id


# Keep backward-compat alias used by existing tests
@pytest.fixture(scope="session")
def test_project_id(gcp_project: str) -> str:
    """Alias for gcp_project, kept for backward compatibility."""
    return gcp_project


@pytest.fixture(scope="session")
def credentials_file() -> Optional[str]:
    """Read the optional path to a GCP credentials file.

    Checks GCP_CREDENTIALS_FILE first, then GCPOTO_TEST_CREDENTIALS, then
    GOOGLE_APPLICATION_CREDENTIALS.

    Returns:
        Path string or None when not configured.
    """
    return (
        os.environ.get("GCP_CREDENTIALS_FILE")
        or os.environ.get("GCPOTO_TEST_CREDENTIALS")
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    )


@pytest.fixture(scope="session")
def mock_mode() -> bool:
    """Determine if tests should run in mock mode.

    Returns:
        True if GCPOTO_MOCK_MODE is set to '1', False otherwise.
    """
    return os.environ.get("GCPOTO_MOCK_MODE", "0") == "1"


# ---------------------------------------------------------------------------
# Unique naming
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_resource_prefix() -> str:
    """Generate a session-unique prefix for test resource names.

    The prefix contains a timestamp and short UUID fragment so resources can
    be identified and cleaned up even if teardown fails.

    Returns:
        A string like ``gcpoto-t1711843200-a1b2c3d4``.
    """
    ts = int(time.time())
    uid = uuid.uuid4().hex[:8]
    return f"gcpoto-t{ts}-{uid}"


@pytest.fixture
def unique_name(test_resource_prefix: str):
    """Factory fixture that generates unique resource names with a timestamp prefix.

    Each call returns a new unique name, suitable for creating isolated test
    resources that do not collide across parallel runs.

    Usage in tests::

        def test_create_bucket(unique_name):
            name = unique_name("bucket")
            # name => "gcpoto-t1711843200-a1b2c3d4-bucket-e5f6a7b8"

    Returns:
        A callable that accepts a resource label and returns a unique name.
    """

    def _generate(label: str = "res") -> str:
        uid = uuid.uuid4().hex[:8]
        return f"{test_resource_prefix}-{label}-{uid}"

    return _generate


# ---------------------------------------------------------------------------
# Common tags
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def common_tags() -> Dict[str, str]:
    """Tags applied to every resource created during integration tests.

    Returns:
        Dictionary of tag key-value pairs.
    """
    return {
        "created-by": "gcpoto-integration-tests",
        "purpose": "testing",
        "auto-delete": "true",
        "environment": "test",
    }


# ---------------------------------------------------------------------------
# Resource cleanup tracker
# ---------------------------------------------------------------------------

@dataclass
class ResourceTracker:
    """Track resources created during integration tests for teardown cleanup.

    Register resources immediately after creation.  During teardown the
    ``cleanup`` method will attempt to delete every registered resource,
    logging errors rather than raising so that as many resources as possible
    are cleaned up.
    """

    _entries: List[Tuple[str, Dict[str, Any], Optional[Callable]]] = field(
        default_factory=list
    )

    def register(
        self,
        resource_type: str,
        identifiers: Dict[str, Any],
        cleanup_fn: Optional[Callable] = None,
    ) -> None:
        """Register a resource for cleanup.

        Args:
            resource_type: Human-readable label (e.g. ``bucket``, ``topic``).
            identifiers: Dict of identifiers needed to delete the resource.
            cleanup_fn: Optional zero-arg callable that performs the deletion.
                        If not provided the caller is responsible for
                        implementing cleanup in a finalizer or via the
                        service-specific helpers below.
        """
        self._entries.append((resource_type, identifiers, cleanup_fn))
        logger.info(
            "Registered %s for cleanup: %s", resource_type, identifiers
        )

    # Convenience shortcuts for common resource types
    def register_bucket(self, bucket_name: str, cleanup_fn: Optional[Callable] = None) -> None:
        self.register("bucket", {"bucket_name": bucket_name}, cleanup_fn)

    def register_topic(self, topic_name: str, cleanup_fn: Optional[Callable] = None) -> None:
        self.register("topic", {"topic_name": topic_name}, cleanup_fn)

    def register_subscription(self, subscription_name: str, cleanup_fn: Optional[Callable] = None) -> None:
        self.register("subscription", {"subscription_name": subscription_name}, cleanup_fn)

    def register_secret(self, secret_id: str, cleanup_fn: Optional[Callable] = None) -> None:
        self.register("secret", {"secret_id": secret_id}, cleanup_fn)

    def register_dns_zone(self, zone_name: str, cleanup_fn: Optional[Callable] = None) -> None:
        self.register("dns_zone", {"zone_name": zone_name}, cleanup_fn)

    def cleanup(self) -> List[str]:
        """Delete all registered resources in reverse order (LIFO).

        Returns:
            A list of error messages for any resources that could not be cleaned up.
        """
        errors: List[str] = []
        # Reverse so that dependent resources (e.g. subscriptions) are deleted
        # before their parents (e.g. topics).
        for resource_type, identifiers, cleanup_fn in reversed(self._entries):
            if cleanup_fn is None:
                logger.warning(
                    "No cleanup function for %s %s; skipping",
                    resource_type, identifiers,
                )
                continue
            try:
                cleanup_fn()
                logger.info("Cleaned up %s: %s", resource_type, identifiers)
            except Exception as exc:
                msg = "Failed to clean up %s %s: %s" % (
                    resource_type, identifiers, exc,
                )
                logger.error(msg)
                errors.append(msg)
        self._entries.clear()
        return errors


@pytest.fixture(scope="session")
def resource_tracker() -> ResourceTracker:
    """Session-scoped resource tracker instance."""
    return ResourceTracker()


@pytest.fixture
def cleanup_resources(resource_tracker: ResourceTracker):
    """Function-scoped fixture that yields a ResourceTracker and runs cleanup on teardown.

    Resources registered via the tracker during the test are automatically
    deleted when the test finishes (pass or fail).

    Usage::

        def test_something(cleanup_resources, storage_service, unique_name):
            name = unique_name("bucket")
            storage_service.create_bucket(bucket_name=name)
            cleanup_resources.register_bucket(
                name, cleanup_fn=lambda: storage_service.delete_bucket(name, force=True)
            )
            # ... assertions ...
            # Bucket is deleted automatically in teardown
    """
    tracker = ResourceTracker()
    yield tracker
    errors = tracker.cleanup()
    if errors:
        logger.warning(
            "Cleanup encountered %d error(s) during teardown", len(errors)
        )


# ---------------------------------------------------------------------------
# Service fixtures (lazy, session-scoped)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def storage_service(gcp_project: str, credentials_file: Optional[str], mock_mode: bool):
    """Create a StorageService for integration tests."""
    from gcpoto.services.storage import StorageService

    service = StorageService(
        project_id=gcp_project, credentials_file=credentials_file
    )
    if mock_mode:
        from unittest.mock import MagicMock

        service.client = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.name = f"mock-bucket-{gcp_project}"
        service.client.list_buckets.return_value = [mock_bucket]
    return service


@pytest.fixture(scope="session")
def pubsub_service(gcp_project: str, credentials_file: Optional[str], mock_mode: bool):
    """Create a PubSubService for integration tests."""
    from gcpoto.services.pubsub import PubSubService

    service = PubSubService(
        project_id=gcp_project, credentials_file=credentials_file
    )
    if mock_mode:
        from unittest.mock import MagicMock

        service.publisher_client = MagicMock()
        service.subscriber_client = MagicMock()
        mock_topic = MagicMock()
        mock_topic.name = f"projects/{gcp_project}/topics/mock-topic"
        service.publisher_client.list_topics.return_value = [mock_topic]
    return service


@pytest.fixture(scope="session")
def billing_service(gcp_project: str, credentials_file: Optional[str], mock_mode: bool):
    """Create a BillingService for integration tests."""
    from gcpoto.services.billing import BillingService

    service = BillingService(
        project_id=gcp_project, credentials_file=credentials_file
    )
    if mock_mode:
        from unittest.mock import MagicMock

        service.cloud_billing_client = MagicMock()
        service.cloud_catalog_client = MagicMock()
    return service


@pytest.fixture(scope="session")
def resource_manager_service(gcp_project: str, credentials_file: Optional[str], mock_mode: bool):
    """Create a ResourceManagerService for integration tests."""
    from gcpoto.services.resource_manager import ResourceManagerService

    service = ResourceManagerService(
        project_id=gcp_project, credentials_file=credentials_file
    )
    if mock_mode:
        from unittest.mock import MagicMock

        service.projects_client = MagicMock()
        service.folders_client = MagicMock()
    return service


@pytest.fixture(scope="session")
def dns_service(gcp_project: str, credentials_file: Optional[str]):
    """Create a DNSService for integration tests."""
    from gcpoto.services.dns import DNSService

    return DNSService(project_id=gcp_project, credentials_file=credentials_file)


@pytest.fixture(scope="session")
def secret_manager_service(gcp_project: str, credentials_file: Optional[str]):
    """Create a SecretManagerService for integration tests."""
    from gcpoto.services.secret_manager import SecretManagerService

    return SecretManagerService(
        project_id=gcp_project, credentials_file=credentials_file
    )
