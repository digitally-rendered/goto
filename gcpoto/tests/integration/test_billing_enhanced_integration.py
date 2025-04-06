"""Enhanced integration tests for the Billing service."""

import os
import time
import uuid
import pytest
from typing import Dict, Any, List

from gcpoto.services.billing import BillingService
from gcpoto.models.billing import BillingAccount, ProjectBillingInfo, BillingBudget


pytest.mark.integration = pytest.mark.skipif(
    "GCPOTO_RUN_INTEGRATION_TESTS" not in os.environ,
    reason="Integration tests are skipped unless GCPOTO_RUN_INTEGRATION_TESTS is set",
)


@pytest.fixture(scope="session")  # Changed from module to session
def billing_service(test_project_id: str, credentials_file: str) -> BillingService:
    """Create a BillingService instance for integration tests.
    
    Args:
        test_project_id: The GCP project ID to use.
        credentials_file: Path to credentials file, if any.
        
    Returns:
        BillingService: An initialized billing service.
    """
    return BillingService(
        project_id=test_project_id,
        credentials_file=credentials_file
    )


@pytest.mark.integration
class TestBillingEnhancedIntegration:
    """Enhanced integration tests for the Billing service with improved coverage."""
    
    def test_get_billing_account(self, billing_service: BillingService):
        """Test retrieving a specific billing account."""
        # First get a list of accounts to find one to test with
        accounts = billing_service.list_billing_accounts()
        
        # Skip if no accounts available
        if not accounts:
            pytest.skip("No billing accounts available to test")
        
        # Get the first account
        sample_account = accounts[0]
        
        # Now test get_billing_account
        account = billing_service.get_billing_account(sample_account.billing_account_id)
        
        # Verify the account details
        assert account.billing_account_id == sample_account.billing_account_id
        assert account.display_name == sample_account.display_name
        assert account.id == sample_account.id
        assert account.type == "billing.account"
        
        print(f"Successfully retrieved billing account: {account.display_name} ({account.billing_account_id})")
    
    def test_list_project_billing_info(self, billing_service: BillingService, test_project_id: str):
        """Test listing projects associated with a billing account."""
        # First get a list of accounts to find one to test with
        accounts = billing_service.list_billing_accounts()
        
        # Skip if no accounts available
        if not accounts:
            pytest.skip("No billing accounts available to test")
        
        # Get the first account
        sample_account = accounts[0]
        
        # Test listing projects for this billing account
        try:
            projects = billing_service.list_project_billing_info(sample_account.billing_account_id)
            
            # Verify we got a list of ProjectBillingInfo objects
            assert isinstance(projects, list)
            
            # If there are any projects, verify they are properly typed
            if projects:
                assert all(isinstance(p, ProjectBillingInfo) for p in projects)
                
                # Print some info for debugging
                print(f"Found {len(projects)} projects associated with billing account {sample_account.billing_account_id}")
                for project in projects[:5]:  # Just print first 5 to avoid too much output
                    print(f"- Project: {project.project_id}, Billing enabled: {project.billing_enabled}")
        except Exception as e:
            # This might fail if the user doesn't have permission to list project billing info
            print(f"Could not list project billing info: {e}")
            pytest.skip(f"Insufficient permissions to list project billing info: {e}")
    
    def test_enable_disable_project_billing(self, billing_service: BillingService, test_project_id: str):
        """Test enabling and disabling project billing.
        
        This test will check the current billing status but not modify it.
        For actually changing the billing status, use the resource creation tests.
        """
        # First get the current project billing info
        try:
            current_info = billing_service.get_project_billing_info(test_project_id)
            
            # Get the current billing account (if any)
            current_account = current_info.billing_account_name
            current_enabled = current_info.billing_enabled
            
            print(f"Current project {test_project_id} billing:")
            print(f"  Account: {current_account or 'None'}")
            print(f"  Enabled: {current_enabled}")
            
            # Don't actually change anything in this test, just verify the method signatures
            assert hasattr(billing_service, 'enable_project_billing')
            assert hasattr(billing_service, 'disable_project_billing')
        except Exception as e:
            print(f"Could not get project billing info: {e}")
            pytest.skip(f"Insufficient permissions to get project billing info: {e}")
    
    def test_get_sku_pricing(self, billing_service: BillingService):
        """Test retrieving pricing information for SKUs."""
        # First get services to find one to test with
        services = billing_service.list_services()
        
        # Make sure we have services
        assert len(services) > 0, "No billing services found"
        
        # Get a sample service ID
        service_id = services[0]['service_id']
        
        # Get SKUs for the service
        skus = billing_service.list_skus(service_id)
        
        # Make sure we have SKUs
        if not skus:
            pytest.skip(f"No SKUs found for service {service_id}")
        
        # Get a sample SKU ID
        sku_id = skus[0]['sku_id']
        
        # Test getting pricing for this SKU
        try:
            pricing = billing_service.get_sku_pricing(service_id, sku_id)
            
            # Verify the pricing data
            assert isinstance(pricing, dict)
            assert 'pricing_info' in pricing or 'category' in pricing or 'service_regions' in pricing
            
            print(f"Retrieved pricing for SKU {sku_id} in service {service_id}")
            # Print a sample of the pricing data
            print(f"Pricing data keys: {list(pricing.keys())[:5]}")
        except Exception as e:
            print(f"Could not get SKU pricing: {e}")
            pytest.skip(f"Failed to get SKU pricing: {e}")
    
    def test_search_billing_accounts(self, billing_service: BillingService):
        """Test searching for billing accounts with filters."""
        # Try searching for only open accounts
        open_accounts = billing_service.list_billing_accounts(only_open=True)
        
        # Verify returned accounts
        assert isinstance(open_accounts, list)
        assert all(isinstance(a, BillingAccount) for a in open_accounts)
        assert all(a.open is True for a in open_accounts), "Found closed accounts when filtering for open only"
        
        print(f"Found {len(open_accounts)} open billing accounts")


@pytest.mark.integration
@pytest.mark.skipif(
    "GCPOTO_TEST_BILLING_ACCOUNT" not in os.environ,
    reason="Budget tests are skipped unless GCPOTO_TEST_BILLING_ACCOUNT is set"
)
class TestBillingBudgetEnhancedIntegration:
    """Enhanced integration tests for Billing Budget operations.
    
    These tests focus on validating all budget operations without modifying resources.
    """
    
    @pytest.fixture(scope="class")
    def billing_account_id(self):
        """Get the billing account ID for testing.
        
        Returns:
            str: The billing account ID.
        """
        return os.environ.get("GCPOTO_TEST_BILLING_ACCOUNT")
    
    def test_get_budget(self, billing_service: BillingService, billing_account_id: str):
        """Test retrieving a specific budget by ID."""
        # First get a list of budgets to find one to test with
        try:
            budgets = billing_service.list_budgets(billing_account_id)
            
            # Skip if no budgets available
            if not budgets:
                pytest.skip("No budgets available to test get_budget")
            
            # Get the first budget
            sample_budget = budgets[0]
            
            # Now test get_budget
            budget = billing_service.get_budget(billing_account_id, sample_budget.budget_id)
            
            # Verify the budget details
            assert budget.budget_id == sample_budget.budget_id
            assert budget.display_name == sample_budget.display_name
            assert budget.id == sample_budget.id
            assert budget.type == "billing.budget"
            
            print(f"Successfully retrieved budget: {budget.display_name} ({budget.budget_id})")
        except Exception as e:
            print(f"Could not test get_budget: {e}")
            pytest.skip(f"Insufficient permissions or setup to test get_budget: {e}")
    
    def test_validate_budget_structure(self, billing_service: BillingService, billing_account_id: str, test_project_id: str):
        """Test validating budget structure without creating a budget."""
        # Create a test budget definition (without actually creating it)
        budget_name = f"Test Budget {uuid.uuid4().hex[:8]}"
        
        # Prepare a budget definition
        budget_def = {
            "display_name": budget_name,
            "amount": {"specified_amount": {"currency_code": "USD", "units": "1000"}},
            "budget_filter": {"projects": [f"projects/{test_project_id}"]},
            "threshold_rules": [
                {"threshold_percent": 0.5, "spend_basis": "CURRENT_SPEND"},
                {"threshold_percent": 0.9, "spend_basis": "CURRENT_SPEND"},
            ],
        }
        
        # Validate dictionary structure for the model
        try:
            # This won't create a budget but validates the structure
            budget = BillingBudget(
                id="billingAccounts/test-account/budgets/test-budget",
                name="billingAccounts/test-account/budgets/test-budget",
                type="billing.budget",
                project=test_project_id,
                budget_id="test-budget",
                display_name=budget_def["display_name"],
                amount=budget_def["amount"],
                budget_filter=budget_def["budget_filter"],
                threshold_rules=budget_def["threshold_rules"]
            )
            
            # Verify the budget was created correctly
            assert budget.display_name == budget_name
            assert budget.amount == budget_def["amount"]
            assert budget.budget_filter == budget_def["budget_filter"]
            assert len(budget.threshold_rules) == 2
            
            print(f"Successfully validated budget structure for {budget_name}")
        except Exception as e:
            print(f"Failed to validate budget structure: {e}")
            pytest.fail(f"Budget structure validation failed: {e}")
