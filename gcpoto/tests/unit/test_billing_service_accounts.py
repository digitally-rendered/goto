"""Unit tests for GCP Billing service - account operations."""

import pytest
import uuid
from unittest.mock import patch, Mock, MagicMock

from google.cloud import billing_v1

from gcpoto.services.billing import BillingService
from gcpoto.models.billing import BillingAccount, ProjectBillingInfo


@pytest.fixture
def mock_cloud_billing_client():
    """Create a mock CloudBillingClient."""
    with patch('google.cloud.billing_v1.CloudBillingClient') as mock_client:
        yield mock_client.return_value


@pytest.fixture
def mock_cloud_catalog_client():
    """Create a mock CloudCatalogClient."""
    with patch('google.cloud.billing_v1.CloudCatalogClient') as mock_client:
        yield mock_client.return_value


@pytest.fixture
def mock_budget_client():
    """Create a mock BudgetServiceClient."""
    mock_client = MagicMock()
    with patch('google.cloud.billing_budgets_v1.BudgetServiceClient', return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_billing_service(mock_cloud_billing_client, mock_cloud_catalog_client):
    """Create a BillingService with mocked clients."""
    service = BillingService(project_id="test-project")
    service.cloud_billing_client = mock_cloud_billing_client
    service.cloud_catalog_client = mock_cloud_catalog_client
    service._budget_client = None  # Reset budget client to test lazy loading
    
    return service


@pytest.fixture
def sample_billing_account_proto():
    """Create a sample BillingAccount proto response."""
    account = billing_v1.BillingAccount()
    account.name = "billingAccounts/ABCDEF-123456"
    account.display_name = "Test Billing Account"
    account.open = True
    account.master_billing_account = "billingAccounts/MASTER-123456"
    
    return account


@pytest.fixture
def sample_project_billing_info_proto():
    """Create a sample ProjectBillingInfo proto response."""
    info = billing_v1.ProjectBillingInfo()
    info.name = "projects/test-project/billingInfo"
    info.billing_account_name = "billingAccounts/ABCDEF-123456"
    info.billing_enabled = True
    
    return info


class TestBillingServiceAccounts:
    """Tests for the BillingService account operations."""
    
    def test_list_billing_accounts(self, mock_billing_service, sample_billing_account_proto):
        """Test listing billing accounts."""
        # Setup
        billing_client = mock_billing_service.cloud_billing_client
        billing_client.list_billing_accounts.return_value = [sample_billing_account_proto]
        
        # Execute
        accounts = mock_billing_service.list_billing_accounts()
        
        # Verify
        assert len(accounts) == 1
        assert accounts[0].id == "billingAccounts/ABCDEF-123456"
        assert accounts[0].billing_account_id == "ABCDEF-123456"
        assert accounts[0].display_name == "Test Billing Account"
        assert accounts[0].open is True
        assert accounts[0].master_billing_account == "billingAccounts/MASTER-123456"
        
        # Verify client was called correctly
        billing_client.list_billing_accounts.assert_called_once()
        
        # Test with only_open=True
        mock_billing_service.list_billing_accounts(only_open=True)
        # 2nd call should include filter
        assert billing_client.list_billing_accounts.call_count == 2
        last_call_args = billing_client.list_billing_accounts.call_args[1]
        assert "filter" in last_call_args["request"].__dict__
    
    def test_get_billing_account(self, mock_billing_service, sample_billing_account_proto):
        """Test getting a billing account."""
        # Setup
        billing_client = mock_billing_service.cloud_billing_client
        billing_client.get_billing_account.return_value = sample_billing_account_proto
        
        # Execute
        account = mock_billing_service.get_billing_account("ABCDEF-123456")
        
        # Verify
        assert account.id == "billingAccounts/ABCDEF-123456"
        assert account.billing_account_id == "ABCDEF-123456"
        assert account.display_name == "Test Billing Account"
        
        # Verify client was called correctly
        billing_client.get_billing_account.assert_called_once_with(name="billingAccounts/ABCDEF-123456")
        
        # Test with already formatted name
        mock_billing_service.get_billing_account("billingAccounts/ABCDEF-789012")
        billing_client.get_billing_account.assert_called_with(name="billingAccounts/ABCDEF-789012")
        
        # Test error handling
        billing_client.get_billing_account.side_effect = Exception("Not found")
        with pytest.raises(Exception, match="Failed to get billing account"):
            mock_billing_service.get_billing_account("non-existent")
    
    def test_get_project_billing_info(self, mock_billing_service, sample_project_billing_info_proto):
        """Test getting project billing info."""
        # Setup
        billing_client = mock_billing_service.cloud_billing_client
        billing_client.get_project_billing_info.return_value = sample_project_billing_info_proto
        
        # Execute
        info = mock_billing_service.get_project_billing_info("test-project")
        
        # Verify
        assert info.id == "projects/test-project/billingInfo"
        assert info.project_id == "test-project"
        assert info.billing_account_name == "billingAccounts/ABCDEF-123456"
        assert info.billing_enabled is True
        
        # Verify client was called correctly
        billing_client.get_project_billing_info.assert_called_once_with(name="projects/test-project")
        
        # Test with already formatted name
        mock_billing_service.get_project_billing_info("projects/another-project")
        billing_client.get_project_billing_info.assert_called_with(name="projects/another-project")
        
        # Test error handling
        billing_client.get_project_billing_info.side_effect = Exception("Not found")
        with pytest.raises(Exception, match="Failed to get project billing info"):
            mock_billing_service.get_project_billing_info("non-existent")
    
    def test_update_project_billing_info(self, mock_billing_service, sample_project_billing_info_proto):
        """Test updating project billing info."""
        # Setup
        billing_client = mock_billing_service.cloud_billing_client
        billing_client.update_project_billing_info.return_value = sample_project_billing_info_proto
        
        # Execute - test adding billing account
        info = mock_billing_service.update_project_billing_info(
            project_id="test-project",
            billing_account_id="ABCDEF-123456"
        )
        
        # Verify
        assert info.id == "projects/test-project/billingInfo"
        assert info.billing_account_name == "billingAccounts/ABCDEF-123456"
        assert info.billing_enabled is True
        
        # Verify client was called correctly with billing account
        billing_client.update_project_billing_info.assert_called_once()
        call_args = billing_client.update_project_billing_info.call_args[1]
        assert call_args["name"] == "projects/test-project"
        assert call_args["project_billing_info"].billing_account_name == "billingAccounts/ABCDEF-123456"
        
        # Reset mock
        billing_client.update_project_billing_info.reset_mock()
        
        # Test disabling billing
        mock_billing_service.update_project_billing_info(
            project_id="test-project",
            billing_account_id=None
        )
        
        # Verify client was called correctly to disable billing
        call_args = billing_client.update_project_billing_info.call_args[1]
        assert call_args["project_billing_info"].billing_account_name == ""
        
        # Test error handling
        billing_client.update_project_billing_info.side_effect = Exception("Update failed")
        with pytest.raises(Exception, match="Failed to update project billing info"):
            mock_billing_service.update_project_billing_info(
                project_id="test-project",
                billing_account_id="ABCDEF-123456"
            )
    
    def test_list_project_billing_info(self, mock_billing_service, sample_project_billing_info_proto):
        """Test listing projects for a billing account."""
        # Setup
        billing_client = mock_billing_service.cloud_billing_client
        billing_client.list_project_billing_info.return_value = [sample_project_billing_info_proto]
        
        # Execute
        projects = mock_billing_service.list_project_billing_info("ABCDEF-123456")
        
        # Verify
        assert len(projects) == 1
        assert projects[0].id == "projects/test-project/billingInfo"
        assert projects[0].project_id == "test-project"
        assert projects[0].billing_account_name == "billingAccounts/ABCDEF-123456"
        
        # Verify client was called correctly
        billing_client.list_project_billing_info.assert_called_once_with(name="billingAccounts/ABCDEF-123456")
        
        # Test with already formatted name
        mock_billing_service.list_project_billing_info("billingAccounts/ABCDEF-789012")
        billing_client.list_project_billing_info.assert_called_with(name="billingAccounts/ABCDEF-789012")
    
    def test_list_services(self, mock_billing_service):
        """Test listing available services."""
        # Setup
        catalog_client = mock_billing_service.cloud_catalog_client
        service1 = MagicMock()
        service1.name = "services/6F81-5844-456A"
        service1.service_id = "6F81-5844-456A"
        service1.display_name = "Compute Engine"
        
        service2 = MagicMock()
        service2.name = "services/95FF-2EF5-5EA1"
        service2.service_id = "95FF-2EF5-5EA1"
        service2.display_name = "Cloud Storage"
        
        catalog_client.list_services.return_value = [service1, service2]
        
        # Execute
        services = mock_billing_service.list_services()
        
        # Verify
        assert len(services) == 2
        assert services[0]["service_id"] == "6F81-5844-456A"
        assert services[0]["display_name"] == "Compute Engine"
        assert services[1]["service_id"] == "95FF-2EF5-5EA1"
        assert services[1]["display_name"] == "Cloud Storage"
        
        # Verify client was called correctly
        catalog_client.list_services.assert_called_once()
    
    def test_list_skus(self, mock_billing_service):
        """Test listing SKUs for a service."""
        # Setup
        catalog_client = mock_billing_service.cloud_catalog_client
        
        sku1 = MagicMock()
        sku1.name = "services/6F81-5844-456A/skus/D062-BDF8-38B3"
        sku1.sku_id = "D062-BDF8-38B3"
        sku1.description = "N1 Predefined Instance Core running in Americas"
        sku1.category.resource_family = "Compute"
        sku1.service_regions = ["us-central1", "us-east1"]
        
        # Create mock pricing info
        pricing_info = MagicMock()
        tiered_rate = MagicMock()
        tiered_rate.start_usage_amount = 0
        tiered_rate.unit_price.currency_code = "USD"
        tiered_rate.unit_price.units = "0"
        tiered_rate.unit_price.nanos = 31611000
        pricing_info.pricing_expression.tiered_rates = [tiered_rate]
        sku1.pricing_info = [pricing_info]
        
        catalog_client.list_skus.return_value = [sku1]
        
        # Execute
        skus = mock_billing_service.list_skus("6F81-5844-456A")
        
        # Verify
        assert len(skus) == 1
        assert skus[0]["sku_id"] == "D062-BDF8-38B3"
        assert skus[0]["description"] == "N1 Predefined Instance Core running in Americas"
        assert skus[0]["category"] == "Compute"
        assert len(skus[0]["service_regions"]) == 2
        assert "pricing_info" in skus[0]
        
        # Verify client was called correctly
        catalog_client.list_skus.assert_called_once_with(parent="services/6F81-5844-456A")
        
        # Test with already formatted service name
        mock_billing_service.list_skus("services/95FF-2EF5-5EA1")
        catalog_client.list_skus.assert_called_with(parent="services/95FF-2EF5-5EA1")
    
    def test_base_methods(self, mock_billing_service, sample_billing_account_proto):
        """Test the base class methods implementation."""
        # Setup for get_resource
        billing_client = mock_billing_service.cloud_billing_client
        billing_client.get_billing_account.return_value = sample_billing_account_proto
        
        # Test get_resource
        account = mock_billing_service.get_resource("ABCDEF-123456")
        assert account.id == "billingAccounts/ABCDEF-123456"
        
        # Setup for list_resources
        billing_client.list_billing_accounts.return_value = [sample_billing_account_proto]
        
        # Test list_resources
        accounts = mock_billing_service.list_resources()
        assert len(accounts) == 1
        assert accounts[0].id == "billingAccounts/ABCDEF-123456"
