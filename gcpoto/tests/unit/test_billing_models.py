"""Unit tests for GCP Billing models."""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any

from gcpoto.models.billing import BillingAccount, ProjectBillingInfo, BillingBudget


class TestBillingAccountModel:
    """Tests for the BillingAccount model."""

    def test_billing_account_creation(self):
        """Test creating a BillingAccount model."""
        billing_id = f"ABCDEF-{uuid.uuid4().hex[:6]}"
        account = BillingAccount(
            id=f"billingAccounts/{billing_id}",
            name=f"billingAccounts/{billing_id}",
            type="billing.account",
            project="test-project",
            billing_account_id=billing_id,
            display_name="Test Billing Account",
            open=True,
            master_billing_account=None,
            labels={"department": "engineering"},
            tags={"team": "platform", "purpose": "testing"},
        )

        assert account.id == f"billingAccounts/{billing_id}"
        assert account.name == f"billingAccounts/{billing_id}"
        assert account.type == "billing.account"
        assert account.project == "test-project"
        assert account.billing_account_id == billing_id
        assert account.display_name == "Test Billing Account"
        assert account.open is True
        assert account.master_billing_account is None
        assert account.labels == {"department": "engineering"}
        assert account.tags == {"team": "platform", "purpose": "testing"}

    def test_billing_account_validators(self):
        """Test the BillingAccount model validators."""
        # Test name validator
        billing_id = f"ABCDEF-{uuid.uuid4().hex[:6]}"
        account = BillingAccount(
            id=f"billingAccounts/{billing_id}",
            name=billing_id,  # Missing billingAccounts/ prefix
            type="billing.account",
            project="test-project",
            billing_account_id=billing_id,
            display_name="Test Billing Account",
            open=True,
        )

        # Validator should have added the prefix
        assert account.name == f"billingAccounts/{billing_id}"

        # Test ID validator with missing ID
        account2 = BillingAccount(
            id="",  # Empty ID
            name=f"billingAccounts/{billing_id}",
            type="billing.account",
            project="test-project",
            billing_account_id=billing_id,
            display_name="Test Billing Account",
            open=True,
        )

        # ID should be set from billing_account_id
        assert account2.id == f"billingAccounts/{billing_id}"

    def test_billing_account_from_api_response(self):
        """Test creating a BillingAccount from an API response."""
        billing_id = f"ABCDEF-{uuid.uuid4().hex[:6]}"
        response = {
            "name": f"billingAccounts/{billing_id}",
            "displayName": "Test API Billing Account",
            "open": True,
            "masterBillingAccount": "billingAccounts/MASTER123",
            "labels": {"department": "finance", "managed-by": "gcpoto"},
        }

        account = BillingAccount.from_api_response(response)

        assert account.id == f"billingAccounts/{billing_id}"
        assert account.name == f"billingAccounts/{billing_id}"
        assert account.billing_account_id == billing_id
        assert account.display_name == "Test API Billing Account"
        assert account.open is True
        assert account.master_billing_account == "billingAccounts/MASTER123"
        assert account.labels == {"department": "finance", "managed-by": "gcpoto"}
        assert account.tags == {"department": "finance", "managed-by": "gcpoto"}

        # Test with minimal response
        minimal_response = {
            "name": f"billingAccounts/{billing_id}",
            "displayName": "Minimal Billing Account",
        }

        minimal_account = BillingAccount.from_api_response(minimal_response)
        assert minimal_account.id == f"billingAccounts/{billing_id}"
        assert minimal_account.billing_account_id == billing_id
        assert minimal_account.display_name == "Minimal Billing Account"
        assert minimal_account.open is True  # Default value


class TestProjectBillingInfoModel:
    """Tests for the ProjectBillingInfo model."""

    def test_project_billing_info_creation(self):
        """Test creating a ProjectBillingInfo model."""
        project_id = f"test-project-{uuid.uuid4().hex[:8]}"
        billing_id = f"ABCDEF-{uuid.uuid4().hex[:6]}"
        billing_info = ProjectBillingInfo(
            id=f"projects/{project_id}/billingInfo",
            name=f"projects/{project_id}/billingInfo",
            type="billing.projectBillingInfo",
            project=project_id,
            project_id=project_id,
            billing_account_name=f"billingAccounts/{billing_id}",
            billing_enabled=True,
        )

        assert billing_info.id == f"projects/{project_id}/billingInfo"
        assert billing_info.name == f"projects/{project_id}/billingInfo"
        assert billing_info.type == "billing.projectBillingInfo"
        assert billing_info.project == project_id
        assert billing_info.project_id == project_id
        assert billing_info.billing_account_name == f"billingAccounts/{billing_id}"
        assert billing_info.billing_enabled is True

    def test_project_billing_info_validators(self):
        """Test the ProjectBillingInfo model validators."""
        # Test name validator
        project_id = f"test-project-{uuid.uuid4().hex[:8]}"
        billing_info = ProjectBillingInfo(
            id=f"projects/{project_id}/billingInfo",
            name="",  # Empty name
            type="billing.projectBillingInfo",
            project=project_id,
            project_id=project_id,
            billing_enabled=True,
        )

        # Validator should have set the name
        assert billing_info.name == f"projects/{project_id}/billingInfo"

        # Test ID validator with missing ID
        billing_info2 = ProjectBillingInfo(
            id="",  # Empty ID
            name=f"projects/{project_id}/billingInfo",
            type="billing.projectBillingInfo",
            project=project_id,
            project_id=project_id,
            billing_enabled=True,
        )

        # ID should be set from project_id
        assert billing_info2.id == f"projects/{project_id}/billingInfo"

        # Test with project_id that already has prefix
        billing_info3 = ProjectBillingInfo(
            id="",
            name="",
            type="billing.projectBillingInfo",
            project=f"projects/{project_id}",
            project_id=f"projects/{project_id}",
            billing_enabled=True,
        )

        # Should handle the prefix correctly
        assert billing_info3.id == f"projects/{project_id}/billingInfo"
        assert billing_info3.name == f"projects/{project_id}/billingInfo"

    def test_project_billing_info_from_api_response(self):
        """Test creating a ProjectBillingInfo from an API response."""
        project_id = f"test-project-{uuid.uuid4().hex[:8]}"
        billing_id = f"ABCDEF-{uuid.uuid4().hex[:6]}"
        response = {
            "name": f"projects/{project_id}/billingInfo",
            "billingAccountName": f"billingAccounts/{billing_id}",
            "billingEnabled": True,
        }

        billing_info = ProjectBillingInfo.from_api_response(response)

        assert billing_info.id == f"projects/{project_id}/billingInfo"
        assert billing_info.name == f"projects/{project_id}/billingInfo"
        assert billing_info.project_id == project_id
        assert billing_info.billing_account_name == f"billingAccounts/{billing_id}"
        assert billing_info.billing_enabled is True

        # Test with minimal response
        minimal_response = {"name": f"projects/{project_id}/billingInfo"}

        minimal_info = ProjectBillingInfo.from_api_response(minimal_response)
        assert minimal_info.id == f"projects/{project_id}/billingInfo"
        assert minimal_info.project_id == project_id
        assert minimal_info.billing_enabled is False  # Default value


class TestBillingBudgetModel:
    """Tests for the BillingBudget model."""

    def test_billing_budget_creation(self):
        """Test creating a BillingBudget model."""
        billing_id = f"ABCDEF-{uuid.uuid4().hex[:6]}"
        budget_id = f"budget-{uuid.uuid4().hex[:8]}"
        budget = BillingBudget(
            id=f"billingAccounts/{billing_id}/budgets/{budget_id}",
            name=f"billingAccounts/{billing_id}/budgets/{budget_id}",
            type="billing.budget",
            project="test-project",
            budget_id=budget_id,
            display_name="Test Budget",
            budget_filter={
                "projects": ["projects/test-project"],
                "creditTypesTreatment": "INCLUDE_ALL_CREDITS",
            },
            amount={"specifiedAmount": {"currencyCode": "USD", "units": "1000"}},
            threshold_rules=[{"thresholdPercent": 0.9}, {"thresholdPercent": 1.0}],
            notify_emails=["user@example.com"],
            labels={"purpose": "cost-control"},
            tags={"team": "platform", "managed-by": "gcpoto"},
        )

        assert budget.id == f"billingAccounts/{billing_id}/budgets/{budget_id}"
        assert budget.name == f"billingAccounts/{billing_id}/budgets/{budget_id}"
        assert budget.type == "billing.budget"
        assert budget.project == "test-project"
        assert budget.budget_id == budget_id
        assert budget.display_name == "Test Budget"
        assert "projects" in budget.budget_filter
        assert "specifiedAmount" in budget.amount
        assert len(budget.threshold_rules) == 2
        assert budget.notify_emails == ["user@example.com"]
        assert budget.labels == {"purpose": "cost-control"}
        assert budget.tags == {"team": "platform", "managed-by": "gcpoto"}

    def test_billing_budget_validators(self):
        """Test the BillingBudget model validators."""
        billing_id = f"ABCDEF-{uuid.uuid4().hex[:6]}"
        budget_id = f"budget-{uuid.uuid4().hex[:8]}"

        # Test name validator
        budget = BillingBudget(
            id=f"billingAccounts/{billing_id}/budgets/{budget_id}",
            name="",  # Empty name
            type="billing.budget",
            project="test-project",
            budget_id=budget_id,
            billing_account_id=billing_id,
            display_name="Test Budget",
            amount={"specifiedAmount": {"currencyCode": "USD", "units": "1000"}},
        )

        # Validator should have set the name
        assert budget.name == f"billingAccounts/{billing_id}/budgets/{budget_id}"

        # Test ID validator with missing ID
        budget2 = BillingBudget(
            id="",  # Empty ID
            name=f"billingAccounts/{billing_id}/budgets/{budget_id}",
            type="billing.budget",
            project="test-project",
            budget_id=budget_id,
            billing_account_id=billing_id,
            display_name="Test Budget",
            amount={"specifiedAmount": {"currencyCode": "USD", "units": "1000"}},
        )

        # ID should be set from budget_id and billing_account_id
        assert budget2.id == f"billingAccounts/{billing_id}/budgets/{budget_id}"

    def test_billing_budget_from_api_response(self):
        """Test creating a BillingBudget from an API response."""
        billing_id = f"ABCDEF-{uuid.uuid4().hex[:6]}"
        budget_id = f"budget-{uuid.uuid4().hex[:8]}"
        response = {
            "name": f"billingAccounts/{billing_id}/budgets/{budget_id}",
            "displayName": "API Test Budget",
            "budgetFilter": {
                "projects": ["projects/test-project"],
                "creditTypesTreatment": "INCLUDE_ALL_CREDITS",
            },
            "amount": {"specifiedAmount": {"currencyCode": "USD", "units": "2000"}},
            "thresholdRules": [{"thresholdPercent": 0.8}, {"thresholdPercent": 1.0}],
            "notificationsRule": {
                "monitoringNotificationChannels": [
                    "projects/test-project/notificationChannels/email_123"
                ]
            },
            "labels": {"department": "engineering", "environment": "production"},
        }

        budget = BillingBudget.from_api_response(response, billing_id)

        assert budget.id == f"billingAccounts/{billing_id}/budgets/{budget_id}"
        assert budget.name == f"billingAccounts/{billing_id}/budgets/{budget_id}"
        assert budget.budget_id == budget_id
        assert budget.display_name == "API Test Budget"
        assert budget.budget_filter["projects"] == ["projects/test-project"]
        assert budget.amount["specifiedAmount"]["units"] == "2000"
        assert len(budget.threshold_rules) == 2
        assert budget.threshold_rules[0]["thresholdPercent"] == 0.8
        assert budget.labels == {
            "department": "engineering",
            "environment": "production",
        }
        assert budget.tags == {"department": "engineering", "environment": "production"}
        assert budget.notify_emails is not None

        # Test with budget ID extraction from name
        response_without_id = {
            "name": f"billingAccounts/{billing_id}/budgets/{budget_id}",
            "displayName": "Budget without explicit ID",
            "amount": {"specifiedAmount": {"currencyCode": "USD", "units": "1000"}},
        }

        budget_without_id = BillingBudget.from_api_response(response_without_id)
        assert budget_without_id.budget_id == budget_id
        assert (
            budget_without_id.id == f"billingAccounts/{billing_id}/budgets/{budget_id}"
        )

        # Test with project extraction from filter
        project_id = "extracted-project"
        response_with_project = {
            "name": f"billingAccounts/{billing_id}/budgets/{budget_id}",
            "displayName": "Budget with project in filter",
            "budgetFilter": {"projects": [f"projects/{project_id}"]},
            "amount": {"specifiedAmount": {"currencyCode": "USD", "units": "1000"}},
        }

        budget_with_project = BillingBudget.from_api_response(response_with_project)
        assert budget_with_project.project == project_id
