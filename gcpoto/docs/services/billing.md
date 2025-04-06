# GCPoto Billing Service

The Billing Service provides a simplified interface for managing Google Cloud Platform billing resources, including billing accounts, project billing configurations, and budgets.

## Features

- List and get billing accounts
- Manage project billing configurations
- Create, list, update, and delete billing budgets
- View available GCP services and SKUs in the billing catalog
- Full support for integration tests with real GCP resources
- Strongly typed models with full JSON schema validation

## Installation

The Billing Service is included with the GCPoto package:

```bash
# Install from source
git clone https://github.com/digitally-rendered/gcpoto.git
cd gcpoto
pip install .

# Or with poetry
poetry install
```

## Required Dependencies

Ensure you have the required dependencies:

```bash
pip install google-cloud-billing google-cloud-billing-budgets
```

Or with Poetry:

```bash
poetry add google-cloud-billing google-cloud-billing-budgets
```

## Initialization

```python
from gcpoto.services.billing import BillingService

# Initialize with project ID and credentials
billing = BillingService(
    project_id="my-project-id",
    credentials_file="path/to/credentials.json"
)

# Or use environment credentials
# Make sure GOOGLE_APPLICATION_CREDENTIALS environment variable is set
billing = BillingService(project_id="my-project-id")
```

## Working with Billing Accounts

### List Billing Accounts

```python
# List all accessible billing accounts
accounts = billing.list_billing_accounts()

# List only open billing accounts
open_accounts = billing.list_billing_accounts(only_open=True)

# Print billing account details
for account in accounts:
    print(f"Billing Account: {account.billing_account_id}")
    print(f"  Display name: {account.display_name}")
    print(f"  Open: {account.open}")
    if account.master_billing_account:
        print(f"  Master account: {account.master_billing_account}")
    if account.tags:
        print(f"  Tags: {account.tags}")
```

### Get a Billing Account

```python
# Get details for a specific billing account
account = billing.get_billing_account("ABCDEF-123456")

# Access billing account properties
print(f"Billing Account: {account.billing_account_id}")
print(f"Display name: {account.display_name}")
print(f"Open: {account.open}")
```

## Working with Project Billing

### Get Project Billing Info

```python
# Get billing information for a project
info = billing.get_project_billing_info("my-project-id")

# Access project billing properties
print(f"Project: {info.project_id}")
print(f"Billing account: {info.billing_account_name}")
print(f"Billing enabled: {info.billing_enabled}")
```

### Update Project Billing

```python
# Associate a project with a billing account
info = billing.update_project_billing_info(
    project_id="my-project-id",
    billing_account_id="ABCDEF-123456"
)

# Disable billing for a project
info = billing.update_project_billing_info(
    project_id="my-project-id",
    billing_account_id=None  # Setting to None disables billing
)
```

### List Projects for a Billing Account

```python
# Get all projects associated with a billing account
projects = billing.list_project_billing_info("ABCDEF-123456")

# Print project details
for project in projects:
    print(f"Project: {project.project_id}")
    print(f"  Billing enabled: {project.billing_enabled}")
```

## Working with Budgets

### List Budgets

```python
# List all budgets for a billing account
budgets = billing.list_budgets("ABCDEF-123456")

# Print budget details
for budget in budgets:
    print(f"Budget: {budget.display_name}")
    
    # Show amount
    if 'specified_amount' in budget.amount:
        amount = budget.amount['specified_amount']
        print(f"  Amount: {amount.get('units', '0')}.{amount.get('nanos', 0) // 1000000} {amount.get('currency_code', 'USD')}")
    elif 'last_period_amount' in budget.amount:
        print("  Amount: Based on last period's spend")
    
    # Show threshold rules
    print(f"  Thresholds: {len(budget.threshold_rules)}")
    for rule in budget.threshold_rules:
        print(f"    {int(rule['threshold_percent'] * 100)}%")
    
    # Show budget filter
    if budget.budget_filter.get('projects'):
        projects = [p.split('/')[-1] for p in budget.budget_filter.get('projects', [])]
        print(f"  Projects: {', '.join(projects)}")
```

### Get a Budget

```python
# Get details for a specific budget
budget = billing.get_budget("ABCDEF-123456", "budget-12345678")

# Access budget properties
print(f"Budget: {budget.display_name}")
print(f"ID: {budget.budget_id}")
```

### Create a Budget

```python
# Create a budget with a specified amount
budget = billing.create_budget(
    billing_account_id="ABCDEF-123456",
    display_name="Monthly Development Budget",
    amount={
        "specified_amount": {
            "currency_code": "USD",
            "units": "1000"  # $1,000 budget
        }
    },
    budget_filter={
        "projects": ["projects/my-dev-project"],
        "credit_types_treatment": "INCLUDE_ALL_CREDITS"  # Include credits in budget calculation
    },
    threshold_rules=[
        {"threshold_percent": 0.5},  # Alert at 50% of budget
        {"threshold_percent": 0.9},  # Alert at 90% of budget
        {"threshold_percent": 1.0}   # Alert at 100% of budget
    ],
    notify_emails=["budget-alerts@example.com"]
)

# Create a budget based on last period's spend
budget = billing.create_budget(
    billing_account_id="ABCDEF-123456",
    display_name="Monthly Automatic Budget",
    amount={"last_period_amount": True},  # Use last period's spend as the budget
    budget_filter={
        "projects": ["projects/my-prod-project"]
    }
)
```

### Update a Budget

```python
# Update a budget's display name
budget = billing.update_budget(
    billing_account_id="ABCDEF-123456",
    budget_id="budget-12345678",
    display_name="Updated Budget Name"
)

# Update a budget's amount
budget = billing.update_budget(
    billing_account_id="ABCDEF-123456",
    budget_id="budget-12345678",
    amount={"specified_amount": {"currency_code": "USD", "units": "2000"}}
)

# Update multiple properties
budget = billing.update_budget(
    billing_account_id="ABCDEF-123456",
    budget_id="budget-12345678",
    display_name="Comprehensive Budget",
    amount={"specified_amount": {"currency_code": "USD", "units": "5000"}},
    budget_filter={"projects": ["projects/project-1", "projects/project-2"]},
    threshold_rules=[
        {"threshold_percent": 0.25},
        {"threshold_percent": 0.5},
        {"threshold_percent": 0.75},
        {"threshold_percent": 1.0}
    ]
)
```

### Delete a Budget

```python
# Delete a budget
success = billing.delete_budget("ABCDEF-123456", "budget-12345678")
if success:
    print("Budget deleted successfully")
```

## Billing Catalog

### List Services

```python
# List all available services in the billing catalog
services = billing.list_services()

# Print service details
for service in services:
    print(f"Service: {service['display_name']}")
    print(f"  ID: {service['service_id']}")
```

### List SKUs

```python
# List all SKUs for a specific service
service_id = "6F81-5844-456A"  # Compute Engine
skus = billing.list_skus(service_id)

# Print SKU details
for sku in skus[:5]:  # Just print the first 5
    print(f"SKU: {sku['description']}")
    print(f"  ID: {sku['sku_id']}")
    print(f"  Category: {sku['category']}")
    if sku['service_regions']:
        print(f"  Regions: {', '.join(sku['service_regions'])}")
    
    # Print pricing tiers if available
    if sku['pricing_info']:
        print("  Pricing:")
        for tier in sku['pricing_info'][0]['pricing_expression']['tiered_rates']:
            start = tier['start_usage_amount']
            price = tier['unit_price']
            print(f"    {start}+ units: {price['units']}.{price['nanos'] // 1000000} {price['currency_code']}/unit")
```

## Base Service Methods

The BillingService implements the base GCPService methods for consistent API usage:

```python
# List billing accounts using the base method
accounts = billing.list_resources()

# Get a billing account using the base method
account = billing.get_resource("ABCDEF-123456")
```

## CLI Usage

GCPoto provides a command-line interface for common Billing operations:

```bash
# List billing accounts
gcpoto --project=my-project-id billing list-accounts

# Get a billing account
gcpoto --project=my-project-id billing get-account ABCDEF-123456

# List budgets for a billing account
gcpoto --project=my-project-id billing list-budgets ABCDEF-123456

# Get project billing info
gcpoto --project=my-project-id billing get-project-billing my-project-id

# Update project billing (link to billing account)
gcpoto --project=my-project-id billing link-project-billing my-project-id ABCDEF-123456

# Disable project billing
gcpoto --project=my-project-id billing disable-project-billing my-project-id

# Create a budget
gcpoto --project=my-project-id billing create-budget ABCDEF-123456 "Monthly Budget" --amount=1000 --threshold=0.5 --threshold=0.9 --threshold=1.0 --project=my-project-id
```

## Permissions and Required Roles

Different operations require different levels of permissions:

- **Listing and viewing billing accounts**: Requires `billing.accounts.list` and `billing.accounts.get` permissions
- **Viewing project billing info**: Requires `billing.resourceAssociations.list` on the billing account
- **Updating project billing**: Requires `billing.resourceAssociations.create` on the billing account
- **Managing budgets**: Requires `billing.budgets.create`, `billing.budgets.update`, and `billing.budgets.delete` permissions

Common roles that include these permissions:
- `roles/billing.viewer` - For viewing billing accounts and budgets
- `roles/billing.user` - For linking/unlinking projects to billing accounts
- `roles/billing.admin` - Full access to billing accounts and budgets
- `roles/billing.costsManager` - For creating and managing budgets

## Error Handling

The Billing service provides meaningful error messages for common issues:

```python
try:
    # Try to update billing for a project without sufficient permissions
    billing.update_project_billing_info("my-project", "ABCDEF-123456")
except Exception as e:
    print(f"Error: {e}")  # Will print a descriptive error

try:
    # Try to create a budget with an invalid amount
    billing.create_budget(
        billing_account_id="ABCDEF-123456",
        display_name="Invalid Budget",
        amount={"invalid_type": True}
    )
except Exception as e:
    print(f"Error: {e}")  # Will inform about the invalid amount type
```

## Testing

All Billing functionality is fully tested with both unit and integration tests.

To run the unit tests:

```bash
pytest tests/unit/test_billing*.py -v
```

To run the integration tests (requires GCP credentials):

```bash
# Set required environment variables
export GCPOTO_TEST_PROJECT_ID="your-test-project-id"
export GCPOTO_RUN_INTEGRATION_TESTS="1"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# For budget tests, set a billing account ID
export GCPOTO_TEST_BILLING_ACCOUNT="ABCDEF-123456"

# To enable tests that create actual resources (requires admin permissions)
export GCPOTO_CREATE_RESOURCES="1"
export GCPOTO_TEST_CREATE_BUDGET="1"

# Then run the tests
pytest tests/integration/test_billing_integration.py -v
```
