"""Unit tests for the billing models."""

import pytest
from datetime import datetime
from typing import Dict, Any

from gcpoto.models.billing import BillingAccount, ProjectBillingInfo, BillingBudget


def test_billing_account_model():
    """Test the BillingAccount model."""
    # Test model creation
    account = BillingAccount(
        id="billingAccounts/ABCDEF-123456-789012",
        name="billingAccounts/ABCDEF-123456-789012",
        type="billing.account",
        project="test-project",
        billing_account_id="ABCDEF-123456-789012",
        display_name="Test Billing Account",
        open=True,
        labels={"env": "test"},
        tags={"purpose": "testing"}
    )
    
    # Verify attributes
    assert account.id == "billingAccounts/ABCDEF-123456-789012"
    assert account.billing_account_id == "ABCDEF-123456-789012"
    assert account.display_name == "Test Billing Account"
    assert account.open is True
    assert account.labels == {"env": "test"}
    assert account.tags == {"purpose": "testing"}


def test_billing_account_validators():
    """Test the BillingAccount validators."""
    # Test name validator
    account = BillingAccount(
        billing_account_id="ABCDEF-123456-789012",
        name="ABCDEF-123456-789012",  # Missing prefix
        display_name="Test Account",
        type="billing.account",
        project="test-project"
    )
    assert account.name == "billingAccounts/ABCDEF-123456-789012"
    
    # Test id validator
    account = BillingAccount(
        billing_account_id="ABCDEF-123456-789012",
        display_name="Test Account",
        type="billing.account",
        project="test-project"
    )
    assert account.id == "billingAccounts/ABCDEF-123456-789012"


def test_billing_account_from_api_response():
    """Test creating BillingAccount from API response."""
    # Typical API response
    response = {
        "name": "billingAccounts/ABCDEF-123456-789012",
        "displayName": "Test Billing Account",
        "open": True,
        "masterBillingAccount": "billingAccounts/PARENT-123456-789012",
        "labels": {"department": "engineering"}
    }
    
    account = BillingAccount.from_api_response(response)
    
    assert account.billing_account_id == "ABCDEF-123456-789012"
    assert account.display_name == "Test Billing Account"
    assert account.open is True
    assert account.master_billing_account == "billingAccounts/PARENT-123456-789012"
    assert account.labels == {"department": "engineering"}
    assert account.tags == {"department": "engineering"}
    
    # Test with minimal response
    minimal_response = {
        "name": "billingAccounts/MINIMAL-123456",
        "displayName": "Minimal Account"
    }
    
    minimal_account = BillingAccount.from_api_response(minimal_response)
    assert minimal_account.billing_account_id == "MINIMAL-123456"
    assert minimal_account.display_name == "Minimal Account"
    assert minimal_account.open is True  # Default value
    assert minimal_account.master_billing_account is None


def test_project_billing_info_model():
    """Test the ProjectBillingInfo model."""
    # Test model creation
    billing_info = ProjectBillingInfo(
        id="projects/test-project/billingInfo",
        name="projects/test-project/billingInfo",
        type="billing.projectBillingInfo",
        project="test-project",
        project_id="test-project",
        billing_account_name="billingAccounts/ABCDEF-123456-789012",
        billing_enabled=True
    )
    
    # Verify attributes
    assert billing_info.id == "projects/test-project/billingInfo"
    assert billing_info.project_id == "test-project"
    assert billing_info.billing_account_name == "billingAccounts/ABCDEF-123456-789012"
    assert billing_info.billing_enabled is True


def test_project_billing_info_validators():
    """Test the ProjectBillingInfo validators."""
    # Test name and id validators
    billing_info = ProjectBillingInfo(
        project_id="test-project",
        type="billing.projectBillingInfo",
        project="test-project",
        billing_enabled=True
    )
    
    assert billing_info.name == "projects/test-project/billingInfo"
    assert billing_info.id == "projects/test-project/billingInfo"
    
    # Test with projects/ prefix
    billing_info = ProjectBillingInfo(
        project_id="projects/another-project",
        type="billing.projectBillingInfo",
        project="another-project",
        billing_enabled=False
    )
    
    assert billing_info.name == "projects/another-project/billingInfo"
    assert billing_info.id == "projects/another-project/billingInfo"


def test_project_billing_info_from_api_response():
    """Test creating ProjectBillingInfo from API response."""
    # Typical API response
    response = {
        "name": "projects/test-project/billingInfo",
        "billingAccountName": "billingAccounts/ABCDEF-123456-789012",
        "billingEnabled": True
    }
    
    billing_info = ProjectBillingInfo.from_api_response(response)
    
    assert billing_info.project_id == "test-project"
    assert billing_info.billing_account_name == "billingAccounts/ABCDEF-123456-789012"
    assert billing_info.billing_enabled is True
    
    # Test with minimal response
    minimal_response = {
        "name": "projects/minimal-project/billingInfo"
    }
    
    minimal_info = ProjectBillingInfo.from_api_response(minimal_response)
    assert minimal_info.project_id == "minimal-project"
    assert minimal_info.billing_account_name is None
    assert minimal_info.billing_enabled is False  # Default value


def test_billing_budget_model():
    """Test the BillingBudget model."""
    # Test model creation
    budget = BillingBudget(
        id="billingAccounts/ABCDEF-123456-789012/budgets/budget-123",
        name="billingAccounts/ABCDEF-123456-789012/budgets/budget-123",
        type="billing.budget",
        project="test-project",
        budget_id="budget-123",
        display_name="Test Budget",
        budget_filter={"projects": ["projects/test-project"]},
        amount={"specified_amount": {"units": "1000", "currency_code": "USD"}},
        threshold_rules=[{"threshold_percent": 0.8, "spend_basis": "CURRENT_SPEND"}],
        notify_emails=["alert@example.com"]
    )
    
    # Verify attributes
    assert budget.id == "billingAccounts/ABCDEF-123456-789012/budgets/budget-123"
    assert budget.budget_id == "budget-123"
    assert budget.display_name == "Test Budget"
    assert budget.budget_filter == {"projects": ["projects/test-project"]}
    assert budget.amount == {"specified_amount": {"units": "1000", "currency_code": "USD"}}
    assert len(budget.threshold_rules) == 1
    assert budget.threshold_rules[0]["threshold_percent"] == 0.8
    assert budget.notify_emails == ["alert@example.com"]


def test_billing_budget_validators():
    """Test the BillingBudget validators."""
    # Test with minimal required fields
    budget = BillingBudget(
        budget_id="budget-xyz",
        type="billing.budget",
        project="test-project",
        display_name="Minimal Budget",
        amount={"specified_amount": {"units": "500", "currency_code": "USD"}}
    )
    
    # Default values are applied
    assert budget.budget_filter == {}
    assert budget.threshold_rules == []
    assert budget.notify_emails is None


def test_billing_budget_from_api_response():
    """Test creating BillingBudget from API response."""
    # Typical API response
    response = {
        "name": "billingAccounts/ABCDEF-123456-789012/budgets/budget-123",
        "displayName": "API Test Budget",
        "budgetFilter": {
            "projects": ["projects/test-project"],
            "services": ["services/compute.googleapis.com"]
        },
        "amount": {
            "specified_amount": {
                "currency_code": "USD",
                "units": "2000"
            }
        },
        "thresholdRules": [
            {"threshold_percent": 0.5, "spend_basis": "CURRENT_SPEND"},
            {"threshold_percent": 0.9, "spend_basis": "CURRENT_SPEND"}
        ],
        "notificationsRule": {
            "monitoringNotificationChannels": [
                "projects/test-project/notificationChannels/email-alert1",
                "projects/test-project/notificationChannels/email-alert2"
            ]
        },
        "labels": {"purpose": "testing"}
    }
    
    budget = BillingBudget.from_api_response(response, "ABCDEF-123456-789012")
    
    assert budget.budget_id == "budget-123"
    assert budget.display_name == "API Test Budget"
    assert "projects" in budget.budget_filter
    assert "services" in budget.budget_filter
    assert budget.amount["specified_amount"]["units"] == "2000"
    assert len(budget.threshold_rules) == 2
    assert budget.notify_emails is not None
    assert len(budget.notify_emails) == 2
    assert budget.labels == {"purpose": "testing"}
    assert budget.tags == {"purpose": "testing"}
