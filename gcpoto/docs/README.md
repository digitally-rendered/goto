# GCPoto Documentation

Welcome to the GCPoto documentation. This guide provides detailed information about using the GCPoto library and CLI for Google Cloud Platform.

## Overview

GCPoto is a boto-like library and CLI for Google Cloud Platform, providing a simplified, consistent interface for interacting with various GCP services. It features strongly typed resource models, JSON schema validation, and comprehensive testing.

## Key Features

- Simple, consistent API for GCP services
- Unified command-line interface
- Resource tagging across all GCP resources
- Strongly typed resource models
- 100% test coverage with pytest
- JSON Schema validation for all models
- Documentation for each service

## Services

- [Storage Service](services/storage.md) - For interacting with Google Cloud Storage
- [Pub/Sub Service](services/pubsub.md) - For interacting with Google Cloud Pub/Sub

## Getting Started

See the [main README](../README.md) for installation instructions and basic usage examples.

## Testing

GCPoto aims for 100% test coverage using:

- pytest for test execution
- pytest-cov for coverage reporting
- pytest-html and pytest-json-report for report generation
- pytest-xdist for parallel testing

Run tests with:

```bash
# Run all tests with coverage
pytest

# Run specific tests
pytest tests/unit/test_storage_*.py
pytest tests/unit/test_pubsub_*.py

# Run tests in parallel
pytest -xvs
```

## Code Quality

GCPoto follows strict code quality standards using:

- [Black](https://black.readthedocs.io/) for code formatting
- [Pylint](https://pylint.readthedocs.io/) for linting

All models are represented in JSON_SCHEMA documents and are fully tested.

## Contributing

Contributions are welcome! Please ensure:

- All new features have comprehensive tests
- Code coverage is maintained at 100%
- Code passes black formatting and pylint checks
- All models have corresponding JSON schemas
- All changes are well-documented with examples

For more details, see the [Contributing Guide](../CONTRIBUTING.md).
