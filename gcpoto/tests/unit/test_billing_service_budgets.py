"""Unit tests for GCP Billing service - budget operations."""

import pytest
import uuid
import json
from unittest.mock import patch, Mock, MagicMock

from gcpoto.services.billing import BillingService
from gcpoto.models.billing import BillingBudget


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
def mock_billing_service(mock_cloud_billing_client, mock_cloud_catalog_client, mock_budget_client):
    """Create a BillingService with mocked clients."""
    with patch('gcpoto.services.billing.BillingService._proto_to_dict') as mock_proto_to_dict:
        # Configure the mock proto_to_dict to return a simple dict
        mock_proto_to_dict.side_effect = lambda proto: json.loads(json.dumps({
            "name": getattr(proto, "name", ""),
            "display_name": getattr(proto, "display_name", ""),
            "amount": {"specified_amount": {"currency_code": "USD", "units": "1000"}},
            "threshold_rules": [{"threshold_percent": 0.9}, {"threshold_percent": 1.0}]
        }))
        
        # Create the service
        service = BillingService(project_id="test-project")
        service.cloud_billing_client = mock_cloud_billing_client
        service.cloud_catalog_client = mock_cloud_catalog_client
        service._budget_client = mock_budget_client
        
        yield service


@pytest.fixture
def sample_budget_proto():
    """Create a sample Budget proto response."""
    budget = MagicMock()
    budget.name = "billingAccounts/ABCDEF-123456/budgets/budget-12345678"
    budget.display_name = "Test Budget"
    
    # These fields will be converted to dict by _proto_to_dict
    budget.__dict__["amount"] = {"specified_amount": {"currency_code": "USD", "units": "1000"}}
    budget.__dict__["threshold_rules"] = [{"threshold_percent": 0.9}, {"threshold_percent": 1.0}]
    budget.__dict__["budget_filter"] = {"projects": ["projects/test-project"]}
    
    return budget


class TestBillingServiceBudgets:
    """Tests for the BillingService budget operations."""
    
    def test_budget_client_lazy_loading(self, mock_billing_service):
        """Test that the budget client is lazy-loaded."""
        # Reset the budget client to None
        mock_billing_service._budget_client = None
        
        # Verify it's None
        assert mock_billing_service._budget_client is None
        
        # Access the budget_client property to trigger lazy loading
        client = mock_billing_service.budget_client
        
        # Verify it's not None anymore
        assert client is not None
        assert mock_billing_service._budget_client is not None
    
    def test_list_budgets(self, mock_billing_service, sample_budget_proto, mock_budget_client):
        """Test listing budgets for a billing account."""
        # Setup
        mock_budget_client.list_budgets.return_value = [sample_budget_proto]
        
        # Execute
        budgets = mock_billing_service.list_budgets("ABCDEF-123456")
        
        # Verify
        assert len(budgets) == 1
        assert budgets[0].id == "billingAccounts/ABCDEF-123456/budgets/budget-12345678"
        assert budgets[0].budget_id == "budget-12345678"
        assert budgets[0].display_name == "Test Budget"
        
        # Verify client was called correctly
        mock_budget_client.list_budgets.assert_called_once_with(parent="billingAccounts/ABCDEF-123456")
        
        # Test with already formatted name
        mock_billing_service.list_budgets("billingAccounts/ABCDEF-789012")
        mock_budget_client.list_budgets.assert_called_with(parent="billingAccounts/ABCDEF-789012")
        
        # Test error handling
        mock_budget_client.list_budgets.side_effect = Exception("List failed")
        with pytest.raises(Exception, match="Failed to list budgets"):
            mock_billing_service.list_budgets("ABCDEF-123456")
    
    def test_get_budget(self, mock_billing_service, sample_budget_proto, mock_budget_client):
        """Test getting a budget by ID."""
        # Setup
        mock_budget_client.get_budget.return_value = sample_budget_proto
        
        # Execute
        budget = mock_billing_service.get_budget("ABCDEF-123456", "budget-12345678")
        
        # Verify
        assert budget.id == "billingAccounts/ABCDEF-123456/budgets/budget-12345678"
        assert budget.budget_id == "budget-12345678"
        assert budget.display_name == "Test Budget"
        
        # Verify client was called correctly
        mock_budget_client.get_budget.assert_called_once_with(name="billingAccounts/ABCDEF-123456/budgets/budget-12345678")
        
        # Test with already formatted billing account name
        mock_billing_service.get_budget("billingAccounts/ABCDEF-789012", "budget-12345678")
        mock_budget_client.get_budget.assert_called_with(name="billingAccounts/ABCDEF-789012/budgets/budget-12345678")
        
        # Test error handling
        mock_budget_client.get_budget.side_effect = Exception("Not found")
        with pytest.raises(Exception, match="Failed to get budget"):
            mock_billing_service.get_budget("ABCDEF-123456", "budget-12345678")
    
    def test_create_budget(self, mock_billing_service, sample_budget_proto, mock_budget_client):
        """Test creating a budget."""
        # Setup
        mock_budget_client.create_budget.return_value = sample_budget_proto
        
        # Execute
        budget = mock_billing_service.create_budget(
            billing_account_id="ABCDEF-123456",
            display_name="Test Budget",
            amount={"specified_amount": {"currency_code": "USD", "units": "1000"}},
            budget_filter={"projects": ["projects/test-project"]},
            threshold_rules=[{"threshold_percent": 0.9}, {"threshold_percent": 1.0}],
            notify_emails=["user@example.com"]
        )
        
        # Verify
        assert budget.display_name == "Test Budget"
        assert "specified_amount" in budget.amount
        assert len(budget.threshold_rules) == 2
        
        # Verify client was called correctly
        mock_budget_client.create_budget.assert_called_once()
        assert "budget" in mock_budget_client.create_budget.call_args[1]
        assert "parent" in mock_budget_client.create_budget.call_args[1]
        assert mock_budget_client.create_budget.call_args[1]["parent"] == "billingAccounts/ABCDEF-123456"
        
        # Test with already formatted billing account name
        mock_billing_service.create_budget(
            billing_account_id="billingAccounts/ABCDEF-789012",
            display_name="Another Budget",
            amount={"specified_amount": {"currency_code": "USD", "units": "2000"}}
        )
        assert mock_budget_client.create_budget.call_args[1]["parent"] == "billingAccounts/ABCDEF-789012"
        
        # Test error handling
        mock_budget_client.create_budget.side_effect = Exception("Creation failed")
        with pytest.raises(Exception, match="Failed to create budget"):
            mock_billing_service.create_budget(
                billing_account_id="ABCDEF-123456",
                display_name="Error Budget",
                amount={"specified_amount": {"currency_code": "USD", "units": "1000"}}
            )
    
    def test_update_budget(self, mock_billing_service, sample_budget_proto, mock_budget_client):
        """Test updating a budget."""
        # Setup
        mock_budget_client.get_budget.return_value = sample_budget_proto
        mock_budget_client.update_budget.return_value = sample_budget_proto
        
        # Execute - test updating display name
        budget = mock_billing_service.update_budget(
            billing_account_id="ABCDEF-123456",
            budget_id="budget-12345678",
            display_name="Updated Budget"
        )
        
        # Verify
        assert budget.display_name == "Test Budget"  # It's mocked to return the original proto
        
        # Verify client was called correctly
        assert mock_budget_client.update_budget.call_count == 1
        
        # Test updating other fields
        mock_billing_service.update_budget(
            billing_account_id="ABCDEF-123456",
            budget_id="budget-12345678",
            amount={"specified_amount": {"currency_code": "USD", "units": "2000"}},
            budget_filter={"projects": ["projects/another-project"]},
            threshold_rules=[{"threshold_percent": 0.8}]
        )
        
        # Now client should have been called twice
        assert mock_budget_client.update_budget.call_count == 2
        
        # Test with no changes (should still return current budget)
        budget = mock_billing_service.update_budget(
            billing_account_id="ABCDEF-123456",
            budget_id="budget-12345678"
        )
        
        assert budget.id == "billingAccounts/ABCDEF-123456/budgets/budget-12345678"
        
        # Client call count should be unchanged since no update happened
        assert mock_budget_client.update_budget.call_count == 2
        
        # Test error handling
        mock_budget_client.update_budget.side_effect = Exception("Update failed")
        with pytest.raises(Exception, match="Failed to update budget"):
            mock_billing_service.update_budget(
                billing_account_id="ABCDEF-123456",
                budget_id="budget-12345678",
                display_name="Error Budget"
            )
    
    def test_delete_budget(self, mock_billing_service, mock_budget_client):
        """Test deleting a budget."""
        # Setup
        mock_budget_client.delete_budget.return_value = None  # Delete returns nothing
        
        # Execute
        result = mock_billing_service.delete_budget("ABCDEF-123456", "budget-12345678")
        
        # Verify
        assert result is True
        
        # Verify client was called correctly
        mock_budget_client.delete_budget.assert_called_once_with(
            name="billingAccounts/ABCDEF-123456/budgets/budget-12345678"
        )
        
        # Test with already formatted billing account name
        mock_billing_service.delete_budget("billingAccounts/ABCDEF-789012", "budget-87654321")
        mock_budget_client.delete_budget.assert_called_with(
            name="billingAccounts/ABCDEF-789012/budgets/budget-87654321"
        )
        
        # Test error handling
        mock_budget_client.delete_budget.side_effect = Exception("Deletion failed")
        with pytest.raises(Exception, match="Failed to delete budget"):
            mock_billing_service.delete_budget("ABCDEF-123456", "budget-12345678")
    
    def test_proto_to_dict(self, mock_billing_service):
        """Test the _proto_to_dict method."""
        # Create a real method to test
        mock_billing_service._proto_to_dict = BillingService._proto_to_dict.__get__(mock_billing_service)
        
        # Create a simple mock proto with to_json method
        mock_proto = MagicMock()
        mock_proto.to_json.return_value = '{"name": "test", "value": 123}'
        
        # Create a simple mock proto with MessageToJson
        with patch('google.protobuf.json_format.MessageToJson', return_value='{"name": "test", "value": 123}'):
            result = mock_billing_service._proto_to_dict(mock_proto)
            
            assert isinstance(result, dict)
            assert result["name"] == "test"
            assert result["value"] == 123
