#!/bin/bash
# Script to run integration tests for gcpoto

# Required for all integration tests
export GCPOTO_RUN_INTEGRATION_TESTS=1

# Try to source gcloud initialization files if they exist
if [ -f "$HOME/google-cloud-sdk/path.bash.inc" ]; then
  source "$HOME/google-cloud-sdk/path.bash.inc"
fi

if [ -f "$HOME/google-cloud-sdk/completion.bash.inc" ]; then
  source "$HOME/google-cloud-sdk/completion.bash.inc"
fi

# Check if gcloud is available
if ! command -v gcloud &> /dev/null; then
  echo "ERROR: 'gcloud' command not found. Please ensure Google Cloud SDK is installed and in your PATH."
  echo "You may need to restart your shell or source the appropriate path files."
  exit 1
fi

# Get the currently active GCP project from gcloud
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)

# GCP project to use for tests
# By default, use the active gcloud project
export GCPOTO_TEST_PROJECT_ID="${CURRENT_PROJECT}"

# Authentication will use the default gcloud credentials
# Explicitly unset credentials variables to ensure we use gcloud auth
unset GCPOTO_TEST_CREDENTIALS
unset GOOGLE_APPLICATION_CREDENTIALS

# Verify gcloud auth is active
echo "Verifying gcloud authentication..."
gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q @ || {
  echo "ERROR: No active gcloud account found. Please run 'gcloud auth login' first."
  exit 1
}

# Print the project being used
echo "Using GCP project for tests: ${GCPOTO_TEST_PROJECT_ID}"
echo "Using default gcloud authentication"

# Enable resource creation tests
# WARNING: This will create and delete actual GCP resources
export GCPOTO_CREATE_RESOURCES=1

# Enable specific resource creation tests
export GCPOTO_TEST_CREATE_BUDGET=1
export GCPOTO_TEST_CREATE_PROJECT=1
export GCPOTO_TEST_CREATE_FOLDER=1

# Optional: Enable organization tests
# export GCPOTO_TEST_ORG_ID="your-org-id"

# Optional: Enable billing tests
# export GCPOTO_TEST_BILLING_ACCOUNT="your-billing-account-id"

# Configure test output directory with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TEST_OUTPUT_DIR="test-reports/integration_${TIMESTAMP}"
mkdir -p ${TEST_OUTPUT_DIR}

# Set up logging for better debugging
export PYTHONUNBUFFERED=1

# Add safety confirmation since we're creating real resources
echo "
==============================================================="
echo "WARNING: You are about to run integration tests that will CREATE ACTUAL RESOURCES in your GCP project."
echo "Project ID: ${GCPOTO_TEST_PROJECT_ID}"
echo "These resources should be automatically cleaned up, but may incur costs."
echo "===============================================================
"
read -p "Are you sure you want to continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Test run aborted by user."
    exit 1
fi

echo "
Running integration tests with resource creation enabled..."
echo "Test results and logs will be saved to: ${TEST_OUTPUT_DIR}"
echo

# Skip code quality checks during integration testing
echo "Skipping code quality checks to focus on integration test functionality"
# Note: Code quality checks with black and pylint should be run separately
# This keeps integration tests focused on functional behavior

# Ensure Poetry environment is activated and run the tests
echo "Running tests using Poetry..."

# Run the tests with coverage reporting
poetry run pytest tests/integration -v \
  --cov=gcpoto \
  --cov-report=term-missing \
  --cov-report=html:${TEST_OUTPUT_DIR}/coverage_html \
  --cov-report=json:${TEST_OUTPUT_DIR}/coverage.json \
  --html=${TEST_OUTPUT_DIR}/test-report.html \
  --json-report --json-report-file=${TEST_OUTPUT_DIR}/test-report.json \
  -n auto \
  --cov-fail-under=100 | tee ${TEST_OUTPUT_DIR}/test-run.log

# Check if we reached 100% coverage
COV_STATUS=$?
if [ $COV_STATUS -ne 0 ]; then
  echo "
WARNING: Test coverage target of 100% not met! Please add more tests."
fi
