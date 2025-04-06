"""Service for interacting with Google Cloud Platform Billing."""

import time
from typing import Dict, List, Optional, Any, Union

from google.cloud import billing_v1
from google.api_core import exceptions

from gcpoto.models.billing import BillingAccount, ProjectBillingInfo, BillingBudget
from gcpoto.services.base import GCPService


class BillingService(GCPService):
    """Service for managing GCP Billing resources (accounts, project billing, budgets)."""

    def __init__(
        self, project_id: Optional[str] = None, credentials_file: Optional[str] = None
    ):
        """Initialize the Billing service.

        Args:
            project_id: The GCP project ID.
            credentials_file: Path to credentials file. If not provided, will use the
                default credentials from the environment.
        """
        # Don't use the base class discovery mechanism as billing API doesn't support it properly
        # Instead just store the parameters we need directly
        self.project_id = project_id
        self.credentials_file = credentials_file
        self.service_name = "billing"
        self.version = "v1"
        # No self.service initialization through discovery API

        # Create clients with application default credentials if no explicit credentials
        if credentials_file:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_file,
                scopes=[
                    "https://www.googleapis.com/auth/cloud-billing",
                    "https://www.googleapis.com/auth/cloud-platform",
                ],
            )
            self.cloud_billing_client = billing_v1.CloudBillingClient(
                credentials=credentials
            )
            self.cloud_catalog_client = billing_v1.CloudCatalogClient(
                credentials=credentials
            )
        else:
            # Use application default credentials
            self.cloud_billing_client = billing_v1.CloudBillingClient()
            self.cloud_catalog_client = billing_v1.CloudCatalogClient()

        # Initialize budget client when needed to avoid unnecessary imports
        self._budget_client = None

    @property
    def budget_client(self):
        """Lazy-load the Budget client when needed."""
        if self._budget_client is None:
            try:
                # Import here to avoid requiring this dependency for all billing operations
                from google.cloud import billing_budgets_v1

                if self.credentials_file:
                    credentials = service_account.Credentials.from_service_account_file(
                        self.credentials_file,
                        scopes=[
                            "https://www.googleapis.com/auth/cloud-billing",
                            "https://www.googleapis.com/auth/cloud-platform",
                        ],
                    )
                    self._budget_client = billing_budgets_v1.BudgetServiceClient(
                        credentials=credentials
                    )
                else:
                    # Use application default credentials
                    self._budget_client = billing_budgets_v1.BudgetServiceClient()
            except ImportError as e:
                raise ImportError(
                    "Failed to import billing_budgets_v1. "
                    "Make sure google-cloud-billing-budgets is installed."
                ) from e
        return self._budget_client

    def list_billing_accounts(self, only_open: bool = False) -> List[BillingAccount]:
        """List accessible billing accounts.

        Args:
            only_open: If True, only open billing accounts are returned.

        Returns:
            List[BillingAccount]: List of BillingAccount objects.
        """
        # Apply filter for open accounts if requested
        filter_str = "open = true" if only_open else ""
        request = billing_v1.ListBillingAccountsRequest(filter=filter_str)

        accounts = []
        for account in self.cloud_billing_client.list_billing_accounts(request=request):
            # Skip closed accounts if only_open is True
            if only_open and not account.open:
                continue

            accounts.append(
                BillingAccount.from_api_response(
                    {
                        "name": account.name,
                        "billingAccountId": account.name.split("/")[-1],
                        "displayName": account.display_name,
                        "open": account.open,
                        "masterBillingAccount": account.master_billing_account,
                        "project": self.project_id,
                    }
                )
            )

        return accounts

    def get_billing_account(self, billing_account_id: str) -> BillingAccount:
        """Get a billing account by ID.

        Args:
            billing_account_id: The billing account ID.

        Returns:
            BillingAccount: The requested billing account.

        Raises:
            Exception: If the billing account does not exist or cannot be accessed.
        """
        try:
            # Format the name if not already formatted
            name = (
                billing_account_id
                if billing_account_id.startswith("billingAccounts/")
                else f"billingAccounts/{billing_account_id}"
            )
            account = self.cloud_billing_client.get_billing_account(name=name)
            # Print raw response for debugging
            print(f"Raw API response for get_billing_account({name}): {account}")

            # Convert to our model
            return BillingAccount.from_api_response(
                {
                    "name": account.name,
                    "billingAccountId": account.name.split("/")[-1],
                    "displayName": account.display_name,
                    "open": account.open,
                    "masterBillingAccount": account.master_billing_account,
                    "project": self.project_id,
                }
            )
        except Exception as e:
            # Log the original exception details
            print(
                f"Error in get_billing_account for {billing_account_id}: {type(e).__name__} - {e}"
            )
            import traceback

            traceback.print_exc()
            raise Exception(
                f"Failed to get billing account '{billing_account_id}': {e}"
            ) from e

    def get_project_billing_info(self, project_id: str) -> ProjectBillingInfo:
        """Get billing information for a project.

        Args:
            project_id: The project ID to get billing info for.

        Returns:
            ProjectBillingInfo: The project's billing information.

        Raises:
            Exception: If the project does not exist or cannot be accessed.
        """
        try:
            # Format the name if not already formatted
            name = (
                project_id
                if project_id.startswith("projects/")
                else f"projects/{project_id}"
            )
            info = self.cloud_billing_client.get_project_billing_info(name=name)

            # Convert to our model
            return ProjectBillingInfo.from_api_response(
                {
                    "name": info.name,
                    "billingAccountName": info.billing_account_name,
                    "billingEnabled": info.billing_enabled,
                }
            )
        except Exception as e:
            raise Exception(f"Failed to get project billing info: {e}")

    def update_project_billing_info(
        self, project_id: str, billing_account_id: Optional[str] = None
    ) -> ProjectBillingInfo:
        """Update billing information for a project.

        Args:
            project_id: The project ID to update billing for.
            billing_account_id: The billing account to associate with the project.
                                If None, billing will be disabled for the project.

        Returns:
            ProjectBillingInfo: The updated project's billing information.

        Raises:
            Exception: If the update fails.
        """
        try:
            # Format the project name
            project_name = (
                project_id
                if project_id.startswith("projects/")
                else f"projects/{project_id}"
            )

            # Create the project billing info
            project_billing_info = billing_v1.ProjectBillingInfo()

            if billing_account_id:
                # Format the billing account name
                billing_account_name = (
                    billing_account_id
                    if billing_account_id.startswith("billingAccounts/")
                    else f"billingAccounts/{billing_account_id}"
                )
                project_billing_info.billing_account_name = billing_account_name
            else:
                # Disable billing by setting an empty billing account name
                project_billing_info.billing_account_name = ""

            # Update the project billing info
            updated_info = self.cloud_billing_client.update_project_billing_info(
                name=project_name, project_billing_info=project_billing_info
            )

            # Convert to our model
            return ProjectBillingInfo.from_api_response(
                {
                    "name": updated_info.name,
                    "billingAccountName": updated_info.billing_account_name,
                    "billingEnabled": updated_info.billing_enabled,
                }
            )
        except Exception as e:
            raise Exception(f"Failed to update project billing info: {e}")

    def list_project_billing_info(
        self, billing_account_id: str
    ) -> List[ProjectBillingInfo]:
        """List projects associated with a billing account.

        Args:
            billing_account_id: The billing account ID.

        Returns:
            List[ProjectBillingInfo]: List of projects' billing information.
        """
        # Format the billing account name
        name = (
            billing_account_id
            if billing_account_id.startswith("billingAccounts/")
            else f"billingAccounts/{billing_account_id}"
        )

        projects = []
        for info in self.cloud_billing_client.list_project_billing_info(name=name):
            projects.append(
                ProjectBillingInfo.from_api_response(
                    {
                        "name": info.name,
                        "billingAccountName": info.billing_account_name,
                        "billingEnabled": info.billing_enabled,
                    }
                )
            )

        return projects

    def list_budgets(self, billing_account_id: str) -> List[BillingBudget]:
        """List budgets for a billing account.

        Args:
            billing_account_id: The billing account ID.

        Returns:
            List[BillingBudget]: List of BillingBudget objects.
        """
        # Format the billing account name
        parent = (
            billing_account_id
            if billing_account_id.startswith("billingAccounts/")
            else f"billingAccounts/{billing_account_id}"
        )

        budgets = []
        try:
            for budget in self.budget_client.list_budgets(parent=parent):
                budgets.append(
                    BillingBudget.from_api_response(
                        self._proto_to_dict(budget),
                        billing_account_id=(
                            billing_account_id.split("/")[-1]
                            if billing_account_id.startswith("billingAccounts/")
                            else billing_account_id
                        ),
                    )
                )
        except Exception as e:
            raise Exception(f"Failed to list budgets: {e}")

        return budgets

    def get_budget(self, billing_account_id: str, budget_id: str) -> BillingBudget:
        """Get a budget by ID.

        Args:
            billing_account_id: The billing account ID.
            budget_id: The budget ID.

        Returns:
            BillingBudget: The requested budget.

        Raises:
            Exception: If the budget does not exist or cannot be accessed.
        """
        try:
            # Format the budget name
            name = f"billingAccounts/{billing_account_id}/budgets/{budget_id}"
            if billing_account_id.startswith("billingAccounts/"):
                name = f"{billing_account_id}/budgets/{budget_id}"

            budget = self.budget_client.get_budget(name=name)

            # Convert to our model
            return BillingBudget.from_api_response(
                self._proto_to_dict(budget),
                billing_account_id=(
                    billing_account_id.split("/")[-1]
                    if billing_account_id.startswith("billingAccounts/")
                    else billing_account_id
                ),
            )
        except Exception as e:
            raise Exception(f"Failed to get budget: {e}")

    def create_budget(
        self,
        billing_account_id: str,
        display_name: str,
        amount: Dict[str, Any],
        budget_filter: Optional[Dict[str, Any]] = None,
        threshold_rules: Optional[List[Dict[str, Any]]] = None,
        notify_emails: Optional[List[str]] = None,
    ) -> BillingBudget:
        """Create a new budget for a billing account.

        Args:
            billing_account_id: The billing account ID.
            display_name: Human-readable name for the budget.
            amount: Budget amount with currency and units.
                Example: {'specified_amount': {'currency_code': 'USD', 'units': '1000'}}
            budget_filter: Filters that define what the budget applies to.
                Example: {'projects': ['projects/my-project'], 'credit_types_treatment': 'INCLUDE_ALL_CREDITS'}
            threshold_rules: Rules that trigger alerts at specified percentages.
                Example: [{'threshold_percent': 0.9}, {'threshold_percent': 1.0}]
            notify_emails: Email addresses to notify when thresholds are crossed.

        Returns:
            BillingBudget: The newly created budget.

        Raises:
            Exception: If budget creation fails.
        """
        try:
            from google.cloud.billing_budgets_v1.types import Budget
            from google.cloud.billing_budgets_v1.types import ThresholdRule
            from google.cloud.billing_budgets_v1.types import NotificationsRule

            # Format the billing account name
            parent = (
                billing_account_id
                if billing_account_id.startswith("billingAccounts/")
                else f"billingAccounts/{billing_account_id}"
            )

            # Create the budget object
            budget = Budget()
            budget.display_name = display_name

            # Set amount
            if "specified_amount" in amount:
                budget.amount.specified_amount.currency_code = amount[
                    "specified_amount"
                ].get("currency_code", "USD")
                budget.amount.specified_amount.units = str(
                    amount["specified_amount"].get("units", "0")
                )
                budget.amount.specified_amount.nanos = int(
                    amount["specified_amount"].get("nanos", 0)
                )
            elif "last_period_amount" in amount:
                budget.amount.last_period_amount = True

            # Set budget filter
            if budget_filter:
                for key, value in budget_filter.items():
                    if key == "projects":
                        budget.budget_filter.projects.extend(value)
                    elif key == "credit_types_treatment":
                        budget.budget_filter.credit_types_treatment = getattr(
                            Budget.Filter.CreditTypesTreatment,
                            value,
                            Budget.Filter.CreditTypesTreatment.CREDIT_TYPES_TREATMENT_UNSPECIFIED,
                        )
                    elif key == "services":
                        budget.budget_filter.services.extend(value)
                    elif key == "subaccounts":
                        budget.budget_filter.subaccounts.extend(value)
                    elif key == "labels":
                        for label_key, label_value in value.items():
                            budget.budget_filter.labels[label_key] = label_value

            # Set threshold rules
            if threshold_rules:
                for rule in threshold_rules:
                    threshold_rule = ThresholdRule()
                    if "threshold_percent" in rule:
                        threshold_rule.threshold_percent = float(
                            rule["threshold_percent"]
                        )
                    if "spend_basis" in rule:
                        threshold_rule.spend_basis = getattr(
                            ThresholdRule.Basis,
                            rule["spend_basis"],
                            ThresholdRule.Basis.BASIS_UNSPECIFIED,
                        )
                    budget.threshold_rules.append(threshold_rule)
            else:
                # Default thresholds at 90% and 100%
                budget.threshold_rules.append(ThresholdRule(threshold_percent=0.9))
                budget.threshold_rules.append(ThresholdRule(threshold_percent=1.0))

            # Set notification rules
            if notify_emails:
                notification_rule = NotificationsRule()
                # We can't set email directly, so we need to have notification channels configured
                # Here we'd attach to existing channels, but for now just store in our model
                budget.notifications_rule.pubsub_topic = (
                    f"projects/{self.project_id}/topics/budget-notifications"
                )
                budget.notifications_rule.schema_version = "1.0"

            # Create the budget
            created_budget = self.budget_client.create_budget(
                parent=parent, budget=budget
            )

            # Convert to our model
            budget_dict = self._proto_to_dict(created_budget)
            budget_dict["notifyEmails"] = notify_emails  # Add emails to our model

            return BillingBudget.from_api_response(
                budget_dict,
                billing_account_id=(
                    billing_account_id.split("/")[-1]
                    if billing_account_id.startswith("billingAccounts/")
                    else billing_account_id
                ),
            )
        except Exception as e:
            raise Exception(f"Failed to create budget: {e}")

    def update_budget(
        self,
        billing_account_id: str,
        budget_id: str,
        display_name: Optional[str] = None,
        amount: Optional[Dict[str, Any]] = None,
        budget_filter: Optional[Dict[str, Any]] = None,
        threshold_rules: Optional[List[Dict[str, Any]]] = None,
        notify_emails: Optional[List[str]] = None,
    ) -> BillingBudget:
        """Update an existing budget.

        Args:
            billing_account_id: The billing account ID.
            budget_id: The budget ID.
            display_name: Updated human-readable name for the budget.
            amount: Updated budget amount.
            budget_filter: Updated filters for what the budget applies to.
            threshold_rules: Updated rules that trigger alerts.
            notify_emails: Updated email addresses to notify.

        Returns:
            BillingBudget: The updated budget.

        Raises:
            Exception: If budget update fails.
        """
        try:
            from google.cloud.billing_budgets_v1.types import (
                Budget,
                UpdateBudgetRequest,
            )
            from google.cloud.billing_budgets_v1.types import ThresholdRule
            from google.cloud.billing_budgets_v1.types import NotificationsRule
            from google.protobuf.field_mask_pb2 import FieldMask

            # First get the current budget
            current_budget = self.get_budget(billing_account_id, budget_id)

            # Format the budget name
            name = f"billingAccounts/{billing_account_id}/budgets/{budget_id}"
            if billing_account_id.startswith("billingAccounts/"):
                name = f"{billing_account_id}/budgets/{budget_id}"

            # Create a new budget with the updates
            budget = Budget()
            budget.name = name

            # Track updated fields
            update_mask = []

            # Update display name if provided
            if display_name is not None:
                budget.display_name = display_name
                update_mask.append("display_name")

            # Update amount if provided
            if amount is not None:
                if "specified_amount" in amount:
                    budget.amount.specified_amount.currency_code = amount[
                        "specified_amount"
                    ].get("currency_code", "USD")
                    budget.amount.specified_amount.units = str(
                        amount["specified_amount"].get("units", "0")
                    )
                    budget.amount.specified_amount.nanos = int(
                        amount["specified_amount"].get("nanos", 0)
                    )
                    update_mask.append("amount.specified_amount")
                elif "last_period_amount" in amount:
                    budget.amount.last_period_amount = True
                    update_mask.append("amount.last_period_amount")

            # Update filter if provided
            if budget_filter is not None:
                for key, value in budget_filter.items():
                    if key == "projects":
                        budget.budget_filter.projects.extend(value)
                        update_mask.append("budget_filter.projects")
                    elif key == "credit_types_treatment":
                        budget.budget_filter.credit_types_treatment = getattr(
                            Budget.Filter.CreditTypesTreatment,
                            value,
                            Budget.Filter.CreditTypesTreatment.CREDIT_TYPES_TREATMENT_UNSPECIFIED,
                        )
                        update_mask.append("budget_filter.credit_types_treatment")
                    elif key == "services":
                        budget.budget_filter.services.extend(value)
                        update_mask.append("budget_filter.services")
                    elif key == "subaccounts":
                        budget.budget_filter.subaccounts.extend(value)
                        update_mask.append("budget_filter.subaccounts")
                    elif key == "labels":
                        for label_key, label_value in value.items():
                            budget.budget_filter.labels[label_key] = label_value
                        update_mask.append("budget_filter.labels")

            # Update threshold rules if provided
            if threshold_rules is not None:
                for rule in threshold_rules:
                    threshold_rule = ThresholdRule()
                    if "threshold_percent" in rule:
                        threshold_rule.threshold_percent = float(
                            rule["threshold_percent"]
                        )
                    if "spend_basis" in rule:
                        threshold_rule.spend_basis = getattr(
                            ThresholdRule.Basis,
                            rule["spend_basis"],
                            ThresholdRule.Basis.BASIS_UNSPECIFIED,
                        )
                    budget.threshold_rules.append(threshold_rule)
                update_mask.append("threshold_rules")

            # Update notification settings if provided
            if notify_emails is not None:
                # In reality, we'd need to update notification channels
                # Here we're just adding the emails to our model
                pass

            # Update the budget if there are changes
            if update_mask:
                update_request = UpdateBudgetRequest(
                    budget=budget, update_mask=FieldMask(paths=update_mask)
                )

                updated_budget = self.budget_client.update_budget(update_request)

                # Convert to our model
                budget_dict = self._proto_to_dict(updated_budget)
                if notify_emails is not None:
                    budget_dict["notifyEmails"] = notify_emails

                return BillingBudget.from_api_response(
                    budget_dict,
                    billing_account_id=(
                        billing_account_id.split("/")[-1]
                        if billing_account_id.startswith("billingAccounts/")
                        else billing_account_id
                    ),
                )
            else:
                # No changes, return the current budget
                return current_budget

        except Exception as e:
            raise Exception(f"Failed to update budget: {e}")

    def delete_budget(self, billing_account_id: str, budget_id: str) -> bool:
        """Delete a budget.

        Args:
            billing_account_id: The billing account ID.
            budget_id: The budget ID to delete.

        Returns:
            bool: True if delete request was successful.

        Raises:
            Exception: If budget deletion fails.
        """
        try:
            # Format the budget name
            name = f"billingAccounts/{billing_account_id}/budgets/{budget_id}"
            if billing_account_id.startswith("billingAccounts/"):
                name = f"{billing_account_id}/budgets/{budget_id}"

            # Delete the budget
            self.budget_client.delete_budget(name=name)

            return True

        except Exception as e:
            raise Exception(f"Failed to delete budget: {e}")

    def list_services(self) -> List[Dict[str, Any]]:
        """List available services in the billing catalog.

        Returns:
            List[Dict[str, Any]]: List of available services.
        """
        services = []
        for service in self.cloud_catalog_client.list_services():
            services.append(
                {
                    "name": service.name,
                    "service_id": service.service_id,
                    "display_name": service.display_name,
                }
            )

        return services

    def list_skus(self, service_id: str) -> List[Dict[str, Any]]:
        """List SKUs for a specific service.

        Args:
            service_id: The service ID.

        Returns:
            List[Dict[str, Any]]: List of SKUs for the service.
        """
        # Format the service name
        parent = (
            service_id
            if service_id.startswith("services/")
            else f"services/{service_id}"
        )

        skus = []
        for sku in self.cloud_catalog_client.list_skus(parent=parent):
            skus.append(
                {
                    "name": sku.name,
                    "sku_id": sku.sku_id,
                    "description": sku.description,
                    "category": sku.category.resource_family,
                    "service_regions": list(sku.service_regions),
                    "pricing_info": [
                        {
                            "pricing_expression": {
                                "tiered_rates": [
                                    {
                                        "start_usage_amount": rate.start_usage_amount,
                                        "unit_price": {
                                            "currency_code": rate.unit_price.currency_code,
                                            "units": rate.unit_price.units,
                                            "nanos": rate.unit_price.nanos,
                                        },
                                    }
                                    for rate in info.pricing_expression.tiered_rates
                                ]
                            }
                        }
                        for info in sku.pricing_info
                    ],
                }
            )

        return skus

    def _proto_to_dict(self, proto) -> Dict[str, Any]:
        """Convert a protobuf object to a Python dictionary.

        This is a simplified implementation. For production, consider a full featured solution.

        Args:
            proto: Protobuf object to convert.

        Returns:
            Dict[str, Any]: Dictionary representation of the protobuf.
        """
        import json
        from google.protobuf.json_format import MessageToJson

        # Convert proto to JSON string and then to Python dict
        json_str = MessageToJson(proto, preserving_proto_field_name=True)
        return json.loads(json_str)

    def list_resources(self, filter_str: Optional[str] = None) -> List[BillingAccount]:
        """Implementation of base class method to list resources (billing accounts).

        Args:
            filter_str: Optional filter string (not used in Billing).

        Returns:
            List[BillingAccount]: List of billing accounts.
        """
        return self.list_billing_accounts()

    def get_resource(self, resource_id: str) -> BillingAccount:
        """Implementation of base class method to get a resource (billing account).

        Args:
            resource_id: The billing account ID.

        Returns:
            BillingAccount: The requested billing account.
        """
        return self.get_billing_account(resource_id)
