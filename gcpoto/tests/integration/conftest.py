"""Configuration for integration tests."""

import os
import pytest
import uuid
import logging
import time
from typing import Dict, Any, List, Set, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field

from gcpoto.services.storage import StorageService
from gcpoto.services.pubsub import PubSubService
from gcpoto.services.billing import BillingService
from gcpoto.services.resource_manager import ResourceManagerService
from google.auth import default as google_auth_default
from google.cloud.service_usage_v1 import ServiceUsageClient, EnableServiceRequest
from google.api_core import exceptions as google_exceptions
from google.api_core.operation import Operation

# Integration tests are meant to test with real GCP resources

@pytest.fixture(scope="session")
def test_project_id() -> str:
    """Get the GCP project ID to use for integration tests.
    
    This will use the GCPOTO_TEST_PROJECT_ID environment variable if set,
    otherwise it will fall back to the GOOGLE_CLOUD_PROJECT environment variable.
    
    Raises:
        ValueError: If no project ID can be determined.
    
    Returns:
        str: The GCP project ID to use for tests.
    """
    project_id = os.environ.get("GCPOTO_TEST_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError(
            "Integration tests require a GCP project ID. "
            "Set either GCPOTO_TEST_PROJECT_ID or GOOGLE_CLOUD_PROJECT environment variable."
        )
    return project_id


@pytest.fixture(scope="session")
def credentials_file() -> str:
    """Get the path to the GCP credentials file to use for integration tests.
    
    This will use the GCPOTO_TEST_CREDENTIALS environment variable if set,
    otherwise it will fall back to the GOOGLE_APPLICATION_CREDENTIALS environment variable.
    
    Returns:
        str: The path to the credentials file, or None if not set.
    """
    return os.environ.get("GCPOTO_TEST_CREDENTIALS") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")


# Integration tests are meant to test with real GCP resources

@pytest.fixture(scope="session")
def storage_service(test_project_id: str, credentials_file: str, mock_mode: bool) -> StorageService:
    """Create a StorageService instance for integration tests.
    
    Args:
        test_project_id: The GCP project ID to use.
        credentials_file: Path to credentials file, if any.
        mock_mode: Whether to use mocks or real GCP services.
        
    Returns:
        StorageService: An initialized storage service.
    """
    # Ensure we have a valid project ID for testing
    if not test_project_id:
        pytest.skip("Test requires a valid GCP project ID. Set GCPOTO_TEST_PROJECT_ID.")
        
    # Create service with application default credentials
    service = StorageService(
        project_id=test_project_id,
        credentials_file=credentials_file
    )
    
    # If mock mode is enabled, patch the client with MagicMock objects
    if mock_mode:
        from unittest.mock import MagicMock
        
        # Mock the storage client
        service.client = MagicMock()
        
        # Setup mock return values for common methods
        # Mock bucket list
        mock_bucket = MagicMock()
        mock_bucket.name = f"mock-bucket-{test_project_id}"
        service.client.list_buckets.return_value = [mock_bucket]
    
    return service



@pytest.fixture(scope="session")
def pubsub_service(test_project_id: str, credentials_file: str, mock_mode: bool) -> PubSubService:
    """Create a PubSubService instance for integration tests.
    
    Args:
        test_project_id: The GCP project ID to use.
        credentials_file: Path to credentials file, if any.
        mock_mode: Whether to use mocks or real GCP services.
        
    Returns:
        PubSubService: An initialized Pub/Sub service.
    """
    # Create service with application default credentials
    service = PubSubService(
        project_id=test_project_id,
        credentials_file=credentials_file
    )
    
    # If mock mode is enabled, patch the clients with MagicMock objects
    if mock_mode:
        from unittest.mock import MagicMock
        
        # Mock the pubsub clients
        service.publisher_client = MagicMock()
        service.subscriber_client = MagicMock()
        
        # Setup mock return values for common methods
        # Mock topic
        mock_topic = MagicMock()
        mock_topic.name = f"projects/{test_project_id}/topics/mock-topic"
        service.publisher_client.list_topics.return_value = [mock_topic]
    
    return service


@pytest.fixture(scope="session")
def test_resource_prefix() -> str:
    """Generate a unique prefix for test resources.
    
    This ensures that test resources can be easily identified and cleaned up,
    and that tests don't interfere with each other when run in parallel.
    
    Returns:
        str: A unique prefix for test resources.
    """
    return f"gcpoto-test-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def common_tags() -> Dict[str, str]:
    """Return a dictionary of tags to apply to all test resources.
    
    Returns:
        Dict[str, str]: Common tags for test resources.
    """
    return {
        "created-by": "gcpoto-integration-tests",
        "purpose": "testing",
        "auto-delete": "true",
        "environment": "test"
    }


# Resource tracking for cleanup
@dataclass
class ResourceTracker:
    """Track resources created during tests for cleanup."""
    # Sets to track different resource types
    storage_buckets: Set[str] = field(default_factory=set)
    pubsub_topics: Set[str] = field(default_factory=set)
    pubsub_subscriptions: Set[str] = field(default_factory=set)
    billing_budgets: List[Dict[str, str]] = field(default_factory=list)  # [{'account_id': 'id', 'budget_id': 'id'}]
    resource_manager_projects: Set[str] = field(default_factory=set)
    resource_manager_folders: Set[str] = field(default_factory=set)
    
    def register_bucket(self, bucket_name: str) -> None:
        """Register a storage bucket for cleanup."""
        self.storage_buckets.add(bucket_name)
        logging.info(f"Registered bucket for cleanup: {bucket_name}")
    
    def register_topic(self, topic_name: str) -> None:
        """Register a Pub/Sub topic for cleanup."""
        self.pubsub_topics.add(topic_name)
        logging.info(f"Registered topic for cleanup: {topic_name}")
    
    def register_subscription(self, subscription_name: str) -> None:
        """Register a Pub/Sub subscription for cleanup."""
        self.pubsub_subscriptions.add(subscription_name)
        logging.info(f"Registered subscription for cleanup: {subscription_name}")
    
    def register_budget(self, billing_account_id: str, budget_id: str) -> None:
        """Register a billing budget for cleanup."""
        self.billing_budgets.append({
            'account_id': billing_account_id,
            'budget_id': budget_id
        })
        logging.info(f"Registered budget for cleanup: {billing_account_id}/{budget_id}")
    
    def register_project(self, project_id: str) -> None:
        """Register a project for cleanup."""
        self.resource_manager_projects.add(project_id)
        logging.info(f"Registered project for cleanup: {project_id}")
    
    def register_folder(self, folder_id: str) -> None:
        """Register a folder for cleanup."""
        self.resource_manager_folders.add(folder_id)
        logging.info(f"Registered folder for cleanup: {folder_id}")
    
    def cleanup_all(self, storage_service: StorageService, pubsub_service: PubSubService, 
                  billing_service: BillingService, resource_manager_service: ResourceManagerService) -> None:
        """Clean up all registered resources."""
        cleanup_errors = []
        
        # Clean up buckets
        for bucket_name in self.storage_buckets:
            try:
                storage_service.delete_bucket(bucket_name, force=True)
                logging.info(f"Cleaned up bucket: {bucket_name}")
            except Exception as e:
                error_msg = f"Failed to clean up bucket {bucket_name}: {str(e)}"
                logging.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # Clean up subscriptions (before topics)
        for subscription_name in self.pubsub_subscriptions:
            try:
                pubsub_service.delete_subscription(subscription_name)
                logging.info(f"Cleaned up subscription: {subscription_name}")
            except Exception as e:
                error_msg = f"Failed to clean up subscription {subscription_name}: {str(e)}"
                logging.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # Clean up topics
        for topic_name in self.pubsub_topics:
            try:
                pubsub_service.delete_topic(topic_name)
                logging.info(f"Cleaned up topic: {topic_name}")
            except Exception as e:
                error_msg = f"Failed to clean up topic {topic_name}: {str(e)}"
                logging.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # Clean up budgets
        for budget in self.billing_budgets:
            try:
                billing_service.delete_budget(budget['account_id'], budget['budget_id'])
                logging.info(f"Cleaned up budget: {budget['account_id']}/{budget['budget_id']}")
            except Exception as e:
                error_msg = f"Failed to clean up budget {budget['account_id']}/{budget['budget_id']}: {str(e)}"
                logging.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # Clean up projects
        for project_id in self.resource_manager_projects:
            try:
                resource_manager_service.delete_project(project_id)
                logging.info(f"Cleaned up project: {project_id}")
            except Exception as e:
                error_msg = f"Failed to clean up project {project_id}: {str(e)}"
                logging.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # Clean up folders
        for folder_id in self.resource_manager_folders:
            try:
                resource_manager_service.delete_folder(folder_id)
                logging.info(f"Cleaned up folder: {folder_id}")
            except Exception as e:
                error_msg = f"Failed to clean up folder {folder_id}: {str(e)}"
                logging.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # Report any errors
        if cleanup_errors:
            logging.error(f"Encountered {len(cleanup_errors)} errors during cleanup:")
            for error in cleanup_errors:
                logging.error(f"  - {error}")
        else:
            logging.info("All resources cleaned up successfully")


@pytest.fixture(scope="session")
def resource_tracker() -> ResourceTracker:
    """Create a resource tracker for the test session.
    
    Returns:
        ResourceTracker: A tracker for test resources.
    """
    return ResourceTracker()


@pytest.fixture(scope="session")
def mock_mode() -> bool:
    """Determine if tests should run in mock mode.
    
    Returns:
        bool: True if tests should use mocks, False to use real GCP services.
    """
    return os.environ.get("GCPOTO_MOCK_MODE", "1") == "1"

@pytest.fixture(scope="session")
def billing_service(test_project_id: str, credentials_file: str, mock_mode: bool) -> BillingService:
    """Create a BillingService instance for integration tests.
    
    Args:
        test_project_id: The GCP project ID to use.
        credentials_file: Path to credentials file, if any.
        mock_mode: Whether to use mocks or real GCP services.
        
    Returns:
        BillingService: An initialized billing service.
    """
    # Ensure we have a valid project ID for testing
    if not test_project_id:
        pytest.skip("Test requires a valid GCP project ID. Set GCPOTO_TEST_PROJECT_ID.")
    
    # Create service with application default credentials
    service = BillingService(
        project_id=test_project_id,
        credentials_file=credentials_file
    )
    
    # If mock mode is enabled, patch the clients with MagicMock objects
    if mock_mode:
        from unittest.mock import MagicMock
        
        # Mock the billing clients
        service.cloud_billing_client = MagicMock()
        service.cloud_catalog_client = MagicMock()
        
        # Setup mock return values for common methods
        # Mock billing accounts with proper structure using objects with attributes
        class MockBillingAccount:
            def __init__(self):
                self.name = "billingAccounts/ABCDEF-123456-789012"
                self.display_name = "Mock Billing Account"
                self.open = True
                self.master_billing_account = None
        
        # Mock services in the catalog
        class MockService:
            def __init__(self, service_id, display_name):
                self.name = f"services/{service_id}"
                self.service_id = service_id
                self.display_name = display_name
        
        # Mock project billing info
        class MockProjectBillingInfo:
            def __init__(self, project_id, billing_enabled=True):
                self.name = f"projects/{project_id}/billingInfo"
                self.project_id = project_id
                self.billing_account_name = "billingAccounts/ABCDEF-123456-789012" if billing_enabled else ""
                self.billing_enabled = billing_enabled
        
        # Set up mock return values
        mock_account = MockBillingAccount()
        service.cloud_billing_client.list_billing_accounts.return_value = [mock_account]
        
        # Setup mock services
        mock_services = [
            MockService("6F81-5844-456A", "Compute Engine"),
            MockService("E505-1A4E-FCD9", "Cloud Storage"),
            MockService("24E6-581D-38E5", "BigQuery")
        ]
        service.cloud_catalog_client.list_services.return_value = mock_services
        
        # Setup mock project billing info
        mock_project_info = MockProjectBillingInfo(test_project_id)
        service.cloud_billing_client.get_project_billing_info.return_value = mock_project_info
        
        # Setup mock listings for projects in a billing account
        service.cloud_billing_client.list_project_billing_info.return_value = [mock_project_info]
    
    return service



@pytest.fixture(scope="session")  # Changed from module to session
def resource_manager_service(test_project_id: str, credentials_file: str, mock_mode: bool) -> ResourceManagerService:
    """Create a ResourceManagerService instance for integration tests.
    
    Args:
        test_project_id: The GCP project ID to use.
        credentials_file: Path to credentials file, if any.
        mock_mode: Whether to use mocks or real GCP services.
        
    Returns:
        ResourceManagerService: An initialized resource manager service.
    """
    # Ensure we have a valid project ID for testing
    if not test_project_id:
        pytest.skip("Test requires a valid GCP project ID. Set GCPOTO_TEST_PROJECT_ID.")
        
    # Create service with application default credentials
    service = ResourceManagerService(
        project_id=test_project_id,
        credentials_file=credentials_file
    )
    
    # If mock mode is enabled, patch the clients with MagicMock objects
    if mock_mode:
        from unittest.mock import MagicMock
        
        # Mock the resource manager clients
        service.projects_client = MagicMock()
        service.folders_client = MagicMock()
        
        # Setup mock return values for common methods
        # Mock project
        mock_project = MagicMock()
        mock_project.name = f"projects/{test_project_id}"
        mock_project.project_id = test_project_id
        mock_project.display_name = "Mock Project"
        mock_project.state = "ACTIVE"
        service.projects_client.get_project.return_value = mock_project
        service.projects_client.list_projects.return_value = [mock_project]
    
    return service



@pytest.fixture(scope="session", autouse=True)
def ensure_services_enabled(test_project_id: str):
    """Fixture to ensure required GCP services are enabled for the test project.
    
    This runs automatically for the session before tests execute.
    It only runs if mock mode is NOT enabled.
    Requires serviceusage.services.enable permission.
    """
    if os.getenv("GCPOTO_MOCK_MODE") == "1":
        print("Mock mode enabled, skipping service enablement check.")
        return

    print(f"Checking and enabling required services for project: {test_project_id}...")
    try:
        credentials, _ = google_auth_default()
        service_usage_client = ServiceUsageClient(credentials=credentials)
    except Exception as e:
        pytest.fail(f"Failed to initialize ServiceUsageClient: {e}", pytrace=False)

    required_services = [
        "serviceusage.googleapis.com",
        "cloudbilling.googleapis.com",
        "cloudresourcemanager.googleapis.com",
        "iam.googleapis.com",
        "pubsub.googleapis.com",
        "storage.googleapis.com",
        # Add other services your tests might need
    ]

    parent = f"projects/{test_project_id}"
    enabled_services = set()

    try:
        # Check existing enabled services
        for service in service_usage_client.list_services(parent=parent, filter="state:ENABLED"):
            # Service name format: projects/{project_number}/services/{service_name}
            service_name = service.name.split("/")[-1]
            enabled_services.add(service_name)
        print(f"Currently enabled services: {enabled_services}")

    except google_exceptions.PermissionDenied:
        pytest.skip(
            f"Permission denied checking enabled services for {test_project_id}. "
            f"Ensure the identity has 'serviceusage.services.list' permission or run in mock mode."
        )
    except Exception as e:
        # Handle other potential errors during listing without failing the whole suite
        print(f"Warning: Failed to list enabled services for {test_project_id}: {e}. Proceeding may lead to enable errors.")
        # Initialize as empty if listing failed, forcing enable attempts for all required services
        enabled_services = set()

    services_to_enable = [
        s for s in required_services if s not in enabled_services
    ]

    if not services_to_enable:
        print("All required services are already enabled.")
        return

    print(f"Attempting to enable the following services: {services_to_enable}")
    # Use Operation type hint from google.api_core
    enable_operations: Dict[str, Operation] = {}

    for service_name in services_to_enable:
        try:
            print(f"Enabling {service_name}...")
            request = EnableServiceRequest(
                name=f"{parent}/services/{service_name}"
            )
            operation = service_usage_client.enable_service(request=request)
            enable_operations[service_name] = operation
            print(f"Enable operation started for {service_name}: {operation.operation.name}")
            # Short initial sleep to allow API propagation
            time.sleep(2)
        except google_exceptions.FailedPrecondition as e:
            # This can happen if the service is already being enabled/disabled
            print(f"Warning: Failed precondition enabling {service_name}: {e}. Might already be in process.")
        except google_exceptions.NotFound as e:
            print(f"Warning: Service {service_name} not found for project {test_project_id}: {e}. Skipping.")
        except Exception as e:
            pytest.fail(f"Failed to start enable operation for {service_name}: {e}", pytrace=False)

    # Wait for operations to complete
    print("Waiting for service enablement operations to complete...")
    max_wait_time = 300  # 5 minutes total wait time
    start_time = time.time()
    operations_complete = False

    while time.time() - start_time < max_wait_time:
        all_done = True
        # Iterate over a copy of the keys since we modify the dict in the loop
        for service_name in list(enable_operations.keys()):
            operation = enable_operations[service_name]
            # Initialize current_op_state to None at the beginning of each loop iteration
            current_op_state = None
            
            # Use the Operation object directly if possible, otherwise check via get_operation
            op_done = operation.done()
            
            if not op_done:
                all_done = False
                # Check status without blocking excessively
                try:
                    # Periodically reload the operation status using the client
                    current_op_state = service_usage_client.get_operation(name=operation.operation.name)
                    op_done = current_op_state.done
                except Exception as e:
                    # Handle potential transient errors during status check
                    print(f"Warning: Error checking operation status for {service_name}: {type(e).__name__} - {e}")
                    # Assume not done if status check fails to be safe, keep polling
                    all_done = False
                    op_done = False

            if op_done:
                # Case 1: We have an updated operation status from the API
                if current_op_state:
                    op_error = getattr(current_op_state, 'error', None)
                    if op_error:
                        # Use pytest.fail to stop tests if a service enablement fails
                        pytest.fail(
                            f"Error enabling service {service_name}: {op_error.message}",
                            pytrace=False,
                        )
                    else:
                        # Operation succeeded based on updated status
                        print(f"Successfully enabled {service_name}")
                        del enable_operations[service_name]  # Remove completed operation
                # Case 2: The operation was already completed (from initial done() check)
                else:
                    # Check the initial operation object for error
                    op_error = getattr(operation, 'error', None) # Direct check on initial op object
                    if op_error:
                        pytest.fail(
                            f"Error enabling service {service_name} (initial check): {op_error.message}",
                            pytrace=False,
                        )
                    else:  # Already done and successful
                        if service_name in enable_operations:  # Ensure it wasn't already deleted
                            print(f"Service {service_name} enablement already completed.")
                            del enable_operations[service_name]

        if all_done and not enable_operations:  # Check dict is empty too
            operations_complete = True
            break
        # Wait before checking statuses again
        if enable_operations: # Only print if still waiting
            print(f"Waiting for {len(enable_operations)} service(s) to enable...")
        else:
            print("All initiated enable operations seem complete, final check...")
        time.sleep(10)

    if not operations_complete:
        remaining = list(enable_operations.keys())
        pytest.fail(f"Timeout waiting for services to enable: {remaining}", pytrace=False)

    print("All required services are enabled.")


@pytest.fixture(scope="session", autouse=True)
def cleanup_all_resources(resource_tracker: ResourceTracker, storage_service: StorageService, 
                         pubsub_service: PubSubService, billing_service: BillingService,
                         resource_manager_service: ResourceManagerService):
    """Automatically clean up all registered resources at the end of the test session.
    
    This fixture runs automatically due to autouse=True.
    
    Args:
        resource_tracker: The resource tracker.
        storage_service: The storage service for bucket operations.
        pubsub_service: The pubsub service for topic/subscription operations.
        billing_service: The billing service for budget operations.
        resource_manager_service: The resource manager service for project/folder operations.
    """
    # This code runs before all tests
    yield
    # This code runs after all tests
    logging.info("Beginning resource cleanup after test session")
    resource_tracker.cleanup_all(
        storage_service=storage_service,
        pubsub_service=pubsub_service,
        billing_service=billing_service,
        resource_manager_service=resource_manager_service
    )


@contextmanager
def register_resource_for_cleanup(resource_tracker: ResourceTracker, resource_type: str, **resource_data):
    """Context manager to register and ensure cleanup of a resource.
    
    Args:
        resource_tracker: The resource tracker.
        resource_type: Type of resource ('bucket', 'topic', 'subscription', 'budget', 'project', 'folder').
        **resource_data: Resource identifiers like bucket_name, topic_name, etc.
    """
    resource_id = None
    try:
        # Register based on resource type
        if resource_type == 'bucket':
            resource_id = resource_data.get('bucket_name')
            resource_tracker.register_bucket(resource_id)
        elif resource_type == 'topic':
            resource_id = resource_data.get('topic_name')
            resource_tracker.register_topic(resource_id)
        elif resource_type == 'subscription':
            resource_id = resource_data.get('subscription_name')
            resource_tracker.register_subscription(resource_id)
        elif resource_type == 'budget':
            account_id = resource_data.get('billing_account_id')
            budget_id = resource_data.get('budget_id')
            resource_tracker.register_budget(account_id, budget_id)
            resource_id = f"{account_id}/{budget_id}"
        elif resource_type == 'project':
            resource_id = resource_data.get('project_id')
            resource_tracker.register_project(resource_id)
        elif resource_type == 'folder':
            resource_id = resource_data.get('folder_id')
            resource_tracker.register_folder(resource_id)
        
        # Let the test run
        yield
        
    except Exception as e:
        logging.error(f"Exception while testing with {resource_type} {resource_id}: {str(e)}")
        raise
