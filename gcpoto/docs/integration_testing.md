# GCPoto Integration Testing Guide

This guide explains how to run the integration tests for GCPoto, which verify the library works correctly against real Google Cloud Platform services.

## Prerequisites

Before running integration tests, you need:

1. A Google Cloud Platform (GCP) project for testing
2. Service account credentials with appropriate permissions
3. Python environment with all dependencies installed

## Required Permissions

The service account used for integration tests needs these permissions:

- For Storage tests:
  - `storage.buckets.create`
  - `storage.buckets.delete`
  - `storage.buckets.get`
  - `storage.buckets.list`
  - `storage.objects.create`
  - `storage.objects.delete`
  - `storage.objects.get`
  - `storage.objects.list`

- For Pub/Sub tests:
  - `pubsub.topics.create`
  - `pubsub.topics.delete`
  - `pubsub.topics.get`
  - `pubsub.topics.list`
  - `pubsub.topics.publish`
  - `pubsub.subscriptions.create`
  - `pubsub.subscriptions.delete`
  - `pubsub.subscriptions.get`
  - `pubsub.subscriptions.list`
  - `pubsub.subscriptions.consume`

For convenience, you can use the following roles:
- `roles/storage.admin`
- `roles/pubsub.admin`

## Environment Setup

Set the following environment variables:

```bash
# Required: The GCP project ID to use for tests
export GCPOTO_TEST_PROJECT_ID="your-test-project-id"

# Required: Enable integration tests
export GCPOTO_RUN_INTEGRATION_TESTS="1"

# Optional: Path to service account credentials file
# If not set, will use the default credentials from the environment
export GCPOTO_TEST_CREDENTIALS="/path/to/service-account-credentials.json"

# Alternative to GCPOTO_TEST_CREDENTIALS:
# Use application default credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

## Running the Tests

### Run All Tests (Unit + Integration)

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run with coverage reporting
pytest --cov=gcpoto --cov-report=html
```

### Run Only Integration Tests

```bash
# Run all integration tests
pytest -v -m integration

# Run specific service integration tests
pytest -v tests/integration/test_storage_integration.py
pytest -v tests/integration/test_pubsub_integration.py
```

### Run Integration Tests in Parallel

```bash
pytest -v -m integration -xvs
```

## Test Structure

The integration tests are organized as follows:

- `tests/integration/conftest.py`: Common fixtures for all integration tests
- `tests/integration/test_storage_integration.py`: Tests for Storage service
- `tests/integration/test_pubsub_integration.py`: Tests for Pub/Sub service

## Test Output and Reporting

Generate HTML and JSON reports:

```bash
pytest -v -m integration --html=integration-report.html --json-report
```

The HTML report provides a visual representation of test results, while the JSON report can be processed programmatically.

## Best Practices

1. **Use a dedicated test project**: Never run integration tests against a production project.

2. **Clean up resources**: While our tests have cleanup logic, always verify that test resources are removed.

3. **Monitor costs**: Running integration tests creates real GCP resources and may incur charges.

4. **CI/CD Integration**: For CI/CD pipelines, create a service account specifically for running tests.

## Debug Tips

If tests fail, you can increase verbosity:

```bash
pytest -vv -m integration
```

To see each test case's output individually:

```bash
pytest -vv -m integration -s
```

## Adding New Integration Tests

When adding new services or features to GCPoto, follow these guidelines for integration tests:

1. Use the `@pytest.mark.integration` decorator for all integration tests

2. Create proper fixtures with cleanup logic to avoid orphaned resources

3. Keep test resources isolated with unique names, preferably using UUID

4. Structure tests to verify both successful operations and error handling

5. Include tests for tagging functionality for all resources

6. Ensure tests work with credentials from environment variables

7. Add appropriate assertions to maintain 100% coverage
