"""Unit tests for Billing JSON schemas."""

import pytest
import json
from typing import Dict, Any
from jsonschema import validate, ValidationError

from gcpoto.models.billing import BillingAccount, ProjectBillingInfo, BillingBudget


def test_billing_account_schema():
    """Test that the BillingAccount model has a valid JSON schema."""
    # Get schema from model
    schema = BillingAccount.model_json_schema()
    
    # Validate schema structure
    assert schema is not None
    assert "$defs" in schema or "properties" in schema
    
    if "properties" in schema:
        # Check required properties are in the schema
        props = schema["properties"]
        assert "billing_account_id" in props
        assert "display_name" in props
        assert "open" in props
        
        # Validate descriptions are present
        assert "description" in props["billing_account_id"]
        assert "description" in props["display_name"]
    
    # Create a valid instance
    account = BillingAccount(
        id="billingAccounts/ABCDEF-123456-789012",
        name="billingAccounts/ABCDEF-123456-789012",
        type="billing.account",
        project="test-project",
        billing_account_id="ABCDEF-123456-789012",
        display_name="Test Billing Account",
        open=True
    )
    
    # Convert to dict and validate against schema
    account_dict = account.model_dump()
    try:
        validate(instance=account_dict, schema=schema)
        assert True, "Valid instance passed schema validation"
    except ValidationError as e:
        assert False, f"Schema validation failed: {str(e)}"


def test_project_billing_info_schema():
    """Test that the ProjectBillingInfo model has a valid JSON schema."""
    # Get schema from model
    schema = ProjectBillingInfo.model_json_schema()
    
    # Validate schema structure
    assert schema is not None
    assert "$defs" in schema or "properties" in schema
    
    if "properties" in schema:
        # Check required properties are in the schema
        props = schema["properties"]
        assert "project_id" in props
        assert "billing_account_name" in props
        assert "billing_enabled" in props
        
        # Validate descriptions are present
        assert "description" in props["project_id"]
        assert "description" in props["billing_enabled"]
    
    # Create a valid instance
    billing_info = ProjectBillingInfo(
        id="projects/test-project/billingInfo",
        name="projects/test-project/billingInfo",
        type="billing.projectBillingInfo",
        project="test-project",
        project_id="test-project",
        billing_account_name="billingAccounts/ABCDEF-123456-789012",
        billing_enabled=True
    )
    
    # Convert to dict and validate against schema
    info_dict = billing_info.model_dump()
    try:
        validate(instance=info_dict, schema=schema)
        assert True, "Valid instance passed schema validation"
    except ValidationError as e:
        assert False, f"Schema validation failed: {str(e)}"


def test_billing_budget_schema():
    """Test that the BillingBudget model has a valid JSON schema."""
    # Get schema from model
    schema = BillingBudget.model_json_schema()
    
    # Validate schema structure
    assert schema is not None
    assert "$defs" in schema or "properties" in schema
    
    if "properties" in schema:
        # Check required properties are in the schema
        props = schema["properties"]
        assert "budget_id" in props
        assert "display_name" in props
        assert "amount" in props
        assert "budget_filter" in props
        assert "threshold_rules" in props
        
        # Validate descriptions are present
        assert "description" in props["budget_id"]
        assert "description" in props["display_name"]
        assert "description" in props["amount"]
    
    # Create a valid instance
    budget = BillingBudget(
        id="billingAccounts/ABCDEF-123456-789012/budgets/budget-123",
        name="billingAccounts/ABCDEF-123456-789012/budgets/budget-123",
        type="billing.budget",
        project="test-project",
        budget_id="budget-123",
        display_name="Test Budget",
        budget_filter={"projects": ["projects/test-project"]},
        amount={"specified_amount": {"units": "1000", "currency_code": "USD"}},
        threshold_rules=[{"threshold_percent": 0.8, "spend_basis": "CURRENT_SPEND"}]
    )
    
    # Convert to dict and validate against schema
    budget_dict = budget.model_dump()
    try:
        validate(instance=budget_dict, schema=schema)
        assert True, "Valid instance passed schema validation"
    except ValidationError as e:
        assert False, f"Schema validation failed: {str(e)}"


def test_serialization_deserialization():
    """Test that the billing models can be properly serialized and deserialized."""
    # Create an instance of BillingAccount
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
    
    # Serialize to JSON
    account_json = account.model_dump_json()
    
    # Deserialize back to object
    account_dict = json.loads(account_json)
    deserialized_account = BillingAccount.model_validate(account_dict)
    
    # Verify equality
    assert deserialized_account.id == account.id
    assert deserialized_account.billing_account_id == account.billing_account_id
    assert deserialized_account.display_name == account.display_name
    assert deserialized_account.open == account.open
    assert deserialized_account.labels == account.labels
    assert deserialized_account.tags == account.tags
    
    # Test with ProjectBillingInfo
    billing_info = ProjectBillingInfo(
        id="projects/test-project/billingInfo",
        name="projects/test-project/billingInfo",
        type="billing.projectBillingInfo",
        project="test-project",
        project_id="test-project",
        billing_account_name="billingAccounts/ABCDEF-123456-789012",
        billing_enabled=True
    )
    
    # Serialize to JSON
    info_json = billing_info.model_dump_json()
    
    # Deserialize back to object
    info_dict = json.loads(info_json)
    deserialized_info = ProjectBillingInfo.model_validate(info_dict)
    
    # Verify equality
    assert deserialized_info.id == billing_info.id
    assert deserialized_info.project_id == billing_info.project_id
    assert deserialized_info.billing_account_name == billing_info.billing_account_name
    assert deserialized_info.billing_enabled == billing_info.billing_enabled
