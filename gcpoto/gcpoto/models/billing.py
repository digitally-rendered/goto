"""Models for GCP Billing resources (accounts, budgets, etc.)."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import Field, field_validator, model_validator

from gcpoto.models.base import GCPResource


class BillingAccount(GCPResource):
    """Model for a GCP Billing Account resource."""

    billing_account_id: str = Field(
        ..., description="The billing account ID, such as 'XXXXXX-XXXXXX-XXXXXX'"
    )
    display_name: str = Field(
        ..., description="The human-readable name of the billing account"
    )
    open: bool = Field(True, description="Whether the billing account is open")
    master_billing_account: Optional[str] = Field(
        None, description="For reseller accounts, the parent billing account"
    )

    @field_validator("name", mode="before")
    def validate_name(cls, v):
        """Ensure name is properly formatted."""
        if not v:
            return v
        # Make sure name has the billingAccounts/ prefix
        if not v.startswith("billingAccounts/"):
            return f"billingAccounts/{v}"
        return v

    # Using model_validator because validate_id depends on another field ('billing_account_id')
    @model_validator(mode="before")
    def validate_id(cls, data: Any) -> Any:
        """Set ID from billing_account_id if not provided."""
        if isinstance(data, dict) and not data.get("id") and data.get("billing_account_id"):
            data["id"] = f'billingAccounts/{data["billing_account_id"]}'
        return data

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "BillingAccount":
        """Create a BillingAccount instance from a GCP API response.

        Args:
            response: The GCP API response dictionary.

        Returns:
            BillingAccount: A new BillingAccount instance.
        """
        # Extract billing_account_id from name if present
        billing_account_id = response.get("name", "").split("/")[-1]

        # Add billing_account_id to the response dict if not already present
        if "billingAccountId" not in response and billing_account_id:
            response["billingAccountId"] = billing_account_id

        # Handle potential camelCase vs snake_case inconsistencies
        normalized_response = {
            "name": response.get("name"),
            "billing_account_id": response.get(
                "billingAccountId", billing_account_id
            ),
            "display_name": response.get("displayName"),
            "open": response.get("open"),
            "master_billing_account": response.get("masterBillingAccount"),
        }
        # Filter out None values to let Pydantic handle defaults
        filtered_response = {k: v for k, v in normalized_response.items() if v is not None}
        # Add required base fields
        filtered_response["type"] = "billing.account"
        if "project" in response:
            filtered_response["project"] = response.get("project")
        return cls(**filtered_response)


class ProjectBillingInfo(GCPResource):
    """Model for Project Billing Information."""

    project_id: str = Field(..., description="The ID of the project")
    billing_account_name: Optional[str] = Field(
        None, description="The resource name of the billing account"
    )
    billing_enabled: bool = Field(
        False, description="Whether billing is enabled for this project"
    )

    # Using model_validator because validate_name depends on another field ('project_id')
    @model_validator(mode="before")
    def validate_name(cls, data: Any) -> Any:
        """Ensure name is properly formatted."""
        if isinstance(data, dict):
            if not data.get("name") and data.get("project_id"):
                data["name"] = f'projects/{data["project_id"]}/billingInfo'
            elif data.get("name") and not data["name"].endswith("/billingInfo"):
                # If name is provided but doesn't end with /billingInfo, append it
                if not data["name"].startswith("projects/"):
                    data["name"] = f'projects/{data["name"]}/billingInfo'
                else:
                    data["name"] = f'{data["name"]}/billingInfo'
        return data

    # Using model_validator because validate_id depends on another field ('project_id')
    @model_validator(mode="before")
    def validate_id(cls, data: Any) -> Any:
        """Set ID from project_id if not provided."""
        if isinstance(data, dict) and not data.get("id") and data.get("project_id"):
            data["id"] = data["project_id"]
        return data

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "ProjectBillingInfo":
        """Create a ProjectBillingInfo instance from a GCP API response.

        Args:
            response: The GCP API response dictionary.

        Returns:
            ProjectBillingInfo: A new ProjectBillingInfo instance.
        """
        # Handle potential camelCase vs snake_case inconsistencies
        normalized_response = {
            "name": response.get("name"),
            "project_id": response.get("projectId"),
            "billing_account_name": response.get("billingAccountName"),
            "billing_enabled": response.get("billingEnabled"),
        }
        # Filter out None values to let Pydantic handle defaults
        filtered_response = {k: v for k, v in normalized_response.items() if v is not None}
        # Add required base fields
        filtered_response["type"] = "billing.projectBillingInfo"
        # Project ID is already part of the model, use it for the base field
        if "project_id" in filtered_response:
            filtered_response["project"] = filtered_response["project_id"]
        elif "project" in response:  # Or try to get it from original response
            filtered_response["project"] = response.get("project")

        return cls(**filtered_response)


class BillingBudget(GCPResource):
    """Model for a GCP Billing Budget."""

    budget_id: str = Field(..., description="The budget ID")
    display_name: str = Field(..., description="The human-readable name of the budget")
    budget_filter: Dict[str, Any] = Field(
        default_factory=dict, description="Filter for what the budget applies to"
    )
    amount: Dict[str, Any] = Field(..., description="Budgeted amount")
    threshold_rules: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Rules that trigger alerts at threshold percentages",
    )
    notify_emails: Optional[List[str]] = Field(
        None, description="Email addresses to notify"
    )

    # Using model_validator because validate_name depends on another field ('budget_id'/'billing_account_id')
    @model_validator(mode="before")
    def validate_name(cls, data: Any) -> Any:
        """Ensure name is properly formatted."""
        if isinstance(data, dict):
            name = data.get("name")
            budget_id = data.get("budgetId", data.get("budget_id"))
            # Budget name format: billingAccounts/{billing_account_id}/budgets/{budget_id}
            if name and budget_id and not name.endswith(f"/budgets/{budget_id}"):
                parts = name.split("/")
                if len(parts) >= 2 and parts[0] == "billingAccounts":
                    data["name"] = f"billingAccounts/{parts[1]}/budgets/{budget_id}"
            elif not name and budget_id and data.get("_billing_account_id_internal"):
                # Construct name if not provided, using internal temp field
                data["name"] = f"billingAccounts/{data['_billing_account_id_internal']}/budgets/{budget_id}"

        return data

    # Using model_validator because validate_id depends on another field ('budget_id')
    @model_validator(mode="before")
    def validate_id(cls, data: Any) -> Any:
        """Set ID from budget_id if not provided."""
        if isinstance(data, dict):
            if not data.get("id"):
                budget_id = data.get("budgetId", data.get("budget_id"))
                if budget_id:
                    data["id"] = budget_id
        return data

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], billing_account_id: str = None
    ) -> "BillingBudget":
        """Create a BillingBudget instance from a GCP API response.

        Args:
            response: The GCP API response dictionary.
            billing_account_id: The billing account ID this budget belongs to.

        Returns:
            BillingBudget: A new BillingBudget instance.
        """
        # Handle potential camelCase vs snake_case inconsistencies
        normalized_response = {
            "name": response.get("name"),
            "budget_id": response.get("budgetId"),  # Extract budget_id from response if available
            "display_name": response.get("displayName"),
            "budget_filter": response.get("budgetFilter"),
            "amount": response.get("amount"),
            "threshold_rules": response.get("thresholdRules"),
            "etag": response.get("etag"),
            # Internal field to help construct name if missing
            "_billing_account_id_internal": billing_account_id,
        }

        # Filter out None values to let Pydantic handle defaults
        filtered_response = {k: v for k, v in normalized_response.items() if v is not None}

        # Extract budget_id from name if not in response directly
        if "budget_id" not in filtered_response and "name" in filtered_response:
            name_parts = filtered_response["name"].split("/")
            if len(name_parts) == 4 and name_parts[2] == "budgets":
                filtered_response["budget_id"] = name_parts[3]

        # Add required base fields
        filtered_response["type"] = "billing.budget"
        # Determine project from context or budget filter
        project_id = ""
        if "budget_filter" in filtered_response and "projects" in filtered_response[
            "budget_filter"
        ]:
            # Take the first project in the filter
            projects = filtered_response["budget_filter"].get("projects", [])
            if projects and len(projects) > 0 and projects[0].startswith("projects/"):
                project_id = projects[0].split("/")[-1]
        elif "project" in response:  # Fallback to project from original response
            project_id = response.get("project")
        if project_id:
            filtered_response["project"] = project_id

        return cls(**filtered_response)
