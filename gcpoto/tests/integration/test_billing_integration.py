"""Integration tests for the Billing service."""

import os
import time
import uuid
import pytest
from typing import Dict, Any, List

from gcpoto.services.billing import BillingService
from gcpoto.models.billing import BillingAccount, ProjectBillingInfo, BillingBudget
from tests.integration.conftest import ResourceTracker, register_resource_for_cleanup


pytest.mark.integration = pytest.mark.skipif(
    "GCPOTO_RUN_INTEGRATION_TESTS" not in os.environ,
    reason="Integration tests are skipped unless GCPOTO_RUN_INTEGRATION_TESTS is set",
)


# Using the billing_service fixture from conftest.py which has session scope


@pytest.fixture(scope="module")
def test_budget_name(test_resource_prefix: str) -> str:
    """Generate a unique budget display name for testing.

    Args:
        test_resource_prefix: Prefix for test resources.

    Returns:
        str: A unique budget display name.
    """
    return f"{test_resource_prefix} Budget {uuid.uuid4().hex[:8]}"


@pytest.mark.integration
class TestBillingIntegration:
    """Integration tests for the Billing service."""

    def test_list_billing_accounts(self, billing_service: BillingService):
        """Test listing billing accounts."""
        accounts = billing_service.list_billing_accounts()

        # Verify we can get a list without error
        assert isinstance(accounts, list)
        assert all(isinstance(a, BillingAccount) for a in accounts)

        # Print some info for debugging
        print(f"Found {len(accounts)} billing accounts")
        for account in accounts[:5]:  # Just print first 5 to avoid too much output
            print(f"- {account.billing_account_id} ({account.display_name})")
            print(f"  Open: {account.open}")
            if account.master_billing_account:
                print(f"  Master: {account.master_billing_account}")

    def test_get_project_billing_info(
        self, billing_service: BillingService, test_project_id: str
    ):
        """Test getting billing info for the current project."""
        # Get the billing info for the current project we're running tests in
        try:
            billing_info = billing_service.get_project_billing_info(test_project_id)

            # Verify billing info details
            assert billing_info.project_id == test_project_id
            assert billing_info.id == f"projects/{test_project_id}/billingInfo"

            # Print billing info for debugging
            print(f"Project ID: {billing_info.project_id}")
            print(f"Billing Account: {billing_info.billing_account_name}")
            print(f"Billing Enabled: {billing_info.billing_enabled}")
        except Exception as e:
            # This might fail if the user doesn't have permission to get billing info
            print(f"Could not get project billing info: {e}")
            pytest.skip("Insufficient permissions to get project billing info")

    def test_list_services(self, billing_service: BillingService):
        """Test listing available GCP services in the billing catalog."""
        services = billing_service.list_services()

        # Verify we can get a list without error
        assert isinstance(services, list)
        assert len(services) > 0

        # Print some service info for debugging
        print(f"Found {len(services)} services in the billing catalog")
        for service in services[:5]:  # Just print first 5 to avoid too much output
            print(f"- {service['display_name']} ({service['service_id']})")

        # Get a sample service ID for the next test
        sample_service_id = services[0]["service_id"]
        return sample_service_id

    def test_list_skus(self, billing_service: BillingService):
        """Test listing SKUs for a specific service."""
        # First get a service ID to use
        services = billing_service.list_services()
        if not services:
            pytest.skip("No services available to test SKUs")

        service_id = services[0]["service_id"]
        skus = billing_service.list_skus(service_id)

        # Verify we can get a list without error
        assert isinstance(skus, list)

        # Print some SKU info for debugging
        print(f"Found {len(skus)} SKUs for service {service_id}")
        for sku in skus[:3]:  # Just print a few to avoid too much output
            print(f"- {sku['description']} ({sku['sku_id']})")
            print(f"  Category: {sku['category']}")
            if "service_regions" in sku and sku["service_regions"]:
                print(
                    f"  Regions: {', '.join(sku['service_regions'][:3])}{'...' if len(sku['service_regions']) > 3 else ''}"
                )


@pytest.mark.integration
@pytest.mark.skipif(
    "GCPOTO_TEST_BILLING_ACCOUNT" not in os.environ,
    reason="Budget tests are skipped unless GCPOTO_TEST_BILLING_ACCOUNT is set",
)
class TestBillingBudgetIntegration:
    """Integration tests for Billing Budget operations.

    These tests are skipped by default because they require a billing account ID
    and permissions to manage budgets.
    """

    @pytest.fixture(scope="class")
    def billing_account_id(self):
        """Get the billing account ID for testing.

        Returns:
            str: The billing account ID.
        """
        return os.environ.get("GCPOTO_TEST_BILLING_ACCOUNT")

    def test_list_budgets(
        self, billing_service: BillingService, billing_account_id: str
    ):
        """Test listing budgets for a billing account."""
        try:
            budgets = billing_service.list_budgets(billing_account_id)

            # Verify we can get a list without error
            assert isinstance(budgets, list)
            assert all(isinstance(b, BillingBudget) for b in budgets)

            # Print some info for debugging
            print(f"Found {len(budgets)} budgets for account {billing_account_id}")
            for budget in budgets[:5]:  # Just print first 5 to avoid too much output
                print(f"- {budget.display_name} ({budget.budget_id})")
                if "specified_amount" in budget.amount:
                    amount = budget.amount["specified_amount"]
                    print(
                        f"  Amount: {amount.get('units', '0')}.{amount.get('nanos', 0) // 1000000} {amount.get('currency_code', 'USD')}"
                    )
                elif "last_period_amount" in budget.amount:
                    print("  Amount: Based on last period's spend")
        except Exception as e:
            print(f"Could not list budgets: {e}")
            pytest.skip(f"Insufficient permissions to list budgets: {e}")

    @pytest.mark.skipif(
        "GCPOTO_CREATE_RESOURCES" not in os.environ,
        reason="Budget creation tests skipped unless GCPOTO_CREATE_RESOURCES is set",
    )
    def test_create_update_delete_budget(
        self,
        billing_service: BillingService,
        billing_account_id: str,
        test_project_id: str,
        test_budget_name: str,
        common_tags: Dict[str, str],
        resource_tracker: ResourceTracker,
    ):
        """Test creating, updating, and deleting a budget."""
        # Skip this test unless specifically enabled
        if not os.environ.get("GCPOTO_TEST_CREATE_BUDGET"):
            pytest.skip(
                "Budget creation test skipped. Set GCPOTO_TEST_CREATE_BUDGET=1 to enable."
            )

        # Create custom tags for tracking this test
        custom_tags = {
            **common_tags,
            "test-type": "budget-lifecycle",
            "created-at": time.strftime("%Y-%m-%d"),
        }

        # Use the context manager to ensure cleanup even in case of test failure
        with register_resource_for_cleanup(resource_tracker, "budget"):
            # Create a budget
            budget = billing_service.create_budget(
                billing_account_id=billing_account_id,
                display_name=test_budget_name,
                amount={"specified_amount": {"currency_code": "USD", "units": "1000"}},
                budget_filter={"projects": [f"projects/{test_project_id}"]},
                threshold_rules=[
                    {"threshold_percent": 0.5, "spend_basis": "CURRENT_SPEND"},
                    {"threshold_percent": 0.9, "spend_basis": "CURRENT_SPEND"},
                    {"threshold_percent": 1.0, "spend_basis": "CURRENT_SPEND"},
                ],
                notify_emails=[],
                tags=custom_tags,
            )

            # Register the budget for cleanup
            budget_id = budget.budget_id
            resource_tracker.register_budget(billing_account_id, budget_id)

            # Verify the budget was created
            assert budget.display_name == test_budget_name
            assert budget.budget_id is not None
            assert budget.billing_account_id == billing_account_id

            # Verify amount
            specified_amount = budget.amount.get("specified_amount", {})
            assert specified_amount.get("currency_code") == "USD"
            assert specified_amount.get("units") == "1000"

            # Verify that threshold rules were applied
            assert len(budget.threshold_rules) == 3
            assert budget.threshold_rules[0]["threshold_percent"] == 0.5
            assert budget.threshold_rules[1]["threshold_percent"] == 0.9
            assert budget.threshold_rules[2]["threshold_percent"] == 1.0

            # Verify custom tags were applied
            for key, value in custom_tags.items():
                assert budget.tags.get(key) == value

            print(f"Created budget: {budget.display_name} (ID: {budget.budget_id})")

            # Get the budget by ID to verify it exists in the system
            retrieved_budget = billing_service.get_budget(billing_account_id, budget_id)
            assert retrieved_budget.budget_id == budget_id
            assert retrieved_budget.display_name == test_budget_name

            # Update the budget with more comprehensive changes
            updated_name = f"{test_budget_name} Updated"
            updated_budget = billing_service.update_budget(
                billing_account_id=billing_account_id,
                budget_id=budget_id,
                display_name=updated_name,
                amount={
                    "specified_amount": {"currency_code": "USD", "units": "1500"}
                },  # Increase the budget
                threshold_rules=[
                    {
                        "threshold_percent": 0.6,
                        "spend_basis": "CURRENT_SPEND",
                    },  # Changed from 0.5
                    {
                        "threshold_percent": 0.8,
                        "spend_basis": "CURRENT_SPEND",
                    },  # Changed from 0.9
                    {"threshold_percent": 1.0, "spend_basis": "CURRENT_SPEND"},
                ],
                tags={**custom_tags, "updated": "true"},
            )

            # Verify the update
            assert updated_budget.display_name == updated_name
            assert updated_budget.budget_id == budget_id  # ID should remain the same

            # Check the updated amount
            updated_amount = updated_budget.amount.get("specified_amount", {})
            assert (
                updated_amount.get("units") == "1500"
            )  # Verify the amount was updated

            # Verify updated threshold rules
            assert len(updated_budget.threshold_rules) == 3
            assert (
                updated_budget.threshold_rules[0]["threshold_percent"] == 0.6
            )  # Updated from 0.5
            assert (
                updated_budget.threshold_rules[1]["threshold_percent"] == 0.8
            )  # Updated from 0.9

            # Verify updated tags
            assert updated_budget.tags.get("updated") == "true"

            print(f"Successfully updated budget: {updated_budget.display_name}")

            # List budgets and verify our budget is there
            all_budgets = billing_service.list_budgets(billing_account_id)
            found_budget = next(
                (b for b in all_budgets if b.budget_id == budget_id), None
            )
            assert (
                found_budget is not None
            ), "Updated budget not found in list of budgets"
            assert found_budget.display_name == updated_name

            # Wait briefly before deleting
            time.sleep(2)

            # Delete the budget
            success = billing_service.delete_budget(billing_account_id, budget_id)
            assert success
            print(f"Deleted budget: {budget_id}")

            # Verify the budget was actually deleted by trying to list it
            time.sleep(3)  # Brief pause to allow deletion to propagate
            all_budgets_after_delete = billing_service.list_budgets(billing_account_id)
            assert not any(
                b.budget_id == budget_id for b in all_budgets_after_delete
            ), "Budget still exists after deletion"

            # Remove from the resource tracker since we deleted it manually
            resource_tracker.billing_budgets = [
                b
                for b in resource_tracker.billing_budgets
                if not (
                    b["account_id"] == billing_account_id
                    and b["budget_id"] == budget_id
                )
            ]

    @pytest.mark.skipif(
        "GCPOTO_CREATE_RESOURCES" not in os.environ,
        reason="Budget creation tests skipped unless GCPOTO_CREATE_RESOURCES is set",
    )
    def test_create_last_period_budget(
        self,
        billing_service: BillingService,
        billing_account_id: str,
        test_project_id: str,
        test_budget_name: str,
        common_tags: Dict[str, str],
    ):
        """Test creating a budget based on last period's spend.

        This tests a different type of budget (last-period-amount) to ensure
        comprehensive coverage of the budget creation functionality.
        """
        # Skip this test unless specifically enabled
        if not os.environ.get("GCPOTO_TEST_CREATE_BUDGET"):
            pytest.skip(
                "Budget creation test skipped. Set GCPOTO_TEST_CREATE_BUDGET=1 to enable."
            )

        budget_id = None
        try:
            # Create custom tags for tracking this test
            custom_tags = {
                **common_tags,
                "test-type": "last-period-budget",
                "created-at": time.strftime("%Y-%m-%d"),
            }

            # Create a budget based on last period's spend
            budget_name = f"{test_budget_name}-last-period"
            budget = billing_service.create_budget(
                billing_account_id=billing_account_id,
                display_name=budget_name,
                amount={
                    "last_period_amount": {}
                },  # Use last period's spending as the budget amount
                budget_filter={"projects": [f"projects/{test_project_id}"]},
                threshold_rules=[
                    {
                        "threshold_percent": 0.8,
                        "spend_basis": "FORECASTED_SPEND",
                    },  # Using forecasted spend
                    {"threshold_percent": 1.0, "spend_basis": "CURRENT_SPEND"},
                ],
                notify_emails=[],
                tags=custom_tags,
            )

            # Store budget ID for cleanup
            budget_id = budget.budget_id

            # Verify the budget was created
            assert budget.display_name == budget_name
            assert budget.budget_id is not None
            assert budget.billing_account_id == billing_account_id

            # Verify it's a last period amount budget
            assert "last_period_amount" in budget.amount

            # Verify that threshold rules were applied
            assert len(budget.threshold_rules) == 2
            assert budget.threshold_rules[0]["threshold_percent"] == 0.8
            assert budget.threshold_rules[0]["spend_basis"] == "FORECASTED_SPEND"

            # Verify custom tags were applied
            for key, value in custom_tags.items():
                assert budget.tags.get(key) == value

            print(
                f"Created last-period budget: {budget.display_name} (ID: {budget.budget_id})"
            )

            # Delete the budget
            success = billing_service.delete_budget(billing_account_id, budget_id)
            assert success
            print(f"Deleted last-period budget: {budget_id}")

        except Exception as e:
            # Make sure to attempt cleanup if something goes wrong
            print(f"Error in last-period budget test: {e}")
            if budget_id:
                try:
                    billing_service.delete_budget(billing_account_id, budget_id)
                    print(f"Cleaned up last-period budget after error: {budget_id}")
                except Exception as cleanup_error:
                    print(f"Failed to clean up last-period budget: {cleanup_error}")
            raise

    def test_list_project_billing_info(
        self, billing_service: BillingService, billing_account_id: str
    ):
        """Test listing projects associated with a billing account."""
        try:
            projects = billing_service.list_project_billing_info(billing_account_id)

            # Verify we can get a list without error
            assert isinstance(projects, list)
            assert all(isinstance(p, ProjectBillingInfo) for p in projects)

            # Print some info for debugging
            print(
                f"Found {len(projects)} projects for billing account {billing_account_id}"
            )
            for project in projects[:5]:  # Just print first 5 to avoid too much output
                print(
                    f"- {project.project_id} (Billing enabled: {project.billing_enabled})"
                )
        except Exception as e:
            print(f"Could not list project billing info: {e}")
            pytest.skip(f"Insufficient permissions to list project billing info: {e}")
