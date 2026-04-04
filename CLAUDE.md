# gcpoto - GCP Boto Clone

A pythonic SDK for Google Cloud Platform, inspired by AWS boto3.

## Project Structure

```
gcpoto/
  gcpoto/
    __init__.py          # Package exports (exceptions)
    exceptions.py        # Custom exception hierarchy
    utils.py             # Path formatting utilities
    models/              # Pydantic V2 resource models
      base.py            # GCPResource base model
      {service}.py       # Per-service models
    schemas/             # JSON Schema definitions
      base.py            # BASE_RESOURCE_SCHEMA
      {service}.py       # Per-service schemas
    services/            # API interaction layer
      base.py            # GCPService[T] generic base class
      {service}.py       # Per-service implementations
    cli/                 # Click-based CLI
      main.py            # All CLI commands
  tests/
    unit/                # Unit tests (mocked)
    integration/         # Integration tests (real GCP)
  pyproject.toml         # Poetry config, deps
  pytest.ini             # Test config
```

## Coding Conventions

- **Python**: 3.9+, black formatting (line length 88)
- **Models**: Pydantic V2 (`BaseModel`, `ConfigDict`, `Field`)
- **Services**: Extend `GCPService[T]` generic base class
- **CLI**: Click framework with nested command groups
- **Logging**: Use `logging.getLogger(__name__)`, never `print()`
- **Exceptions**: Use custom hierarchy from `gcpoto.exceptions`
- **Path formatting**: Use helpers from `gcpoto.utils` (never inline `if "/" not in`)
- **Imports**: Top-level, no scattered imports inside methods
- **Tags/Labels**: Consistent `_tags` dict pattern with `get_tag(key, default)` method

## Adding a New GCP Service

Every new service requires 5 files:

1. **Model** (`gcpoto/models/{service}.py`) - Pydantic model extending `GCPResource`
2. **Schema** (`gcpoto/schemas/{service}.py`) - JSON Schema dict + `get_schema()` function
3. **Service** (`gcpoto/services/{service}.py`) - Service class extending `GCPService[T]`
4. **CLI** - Add command group to `gcpoto/cli/main.py`
5. **Tests** (`tests/unit/test_{service}.py`) - Unit tests with mocked API calls

### Model Pattern

```python
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from gcpoto.models.base import GCPResource

class MyResource(GCPResource):
    """Model for GCP MyResource."""
    specific_field: str = ""
    optional_field: Optional[str] = None
    _tags: Optional[Dict[str, str]] = None

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "MyResource":
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="service.resource",
            project=response.get("projectId", ""),
            specific_field=response.get("specificField", ""),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance

    def get_tag(self, key: str, default: str = "") -> str:
        if self._tags and key in self._tags:
            return self._tags[key]
        return self.labels.get(key, default)
```

### Service Pattern

```python
import logging
from typing import List, Optional, Dict, Any
from gcpoto.services.base import GCPService
from gcpoto.models.my_service import MyResource
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)

class MyService(GCPService[MyResource]):
    def __init__(self, project_id: str, credentials_file: Optional[str] = None):
        super().__init__(
            project_id=project_id,
            service_name="myservice",
            version="v1",
            credentials_file=credentials_file,
            resource_model=MyResource,
        )

    def list_resources(self, **kwargs) -> List[MyResource]:
        request = self.service.resources().list(project=self.project_id, **kwargs)
        response = request.execute()
        return [self._parse_response(item) for item in response.get("items", [])]

    def get_resource(self, resource_id: str, **kwargs) -> MyResource:
        request = self.service.resources().get(
            project=self.project_id, resource=resource_id, **kwargs
        )
        return self._parse_response(request.execute())

    def create_resource(self, resource: MyResource, **kwargs) -> MyResource:
        body = resource.to_dict()
        request = self.service.resources().insert(
            project=self.project_id, body=body, **kwargs
        )
        return self._parse_response(request.execute())

    def delete_resource(self, resource_id: str, **kwargs) -> bool:
        self.service.resources().delete(
            project=self.project_id, resource=resource_id, **kwargs
        ).execute()
        return True
```

### Schema Pattern

```python
from typing import Dict, Any

MY_RESOURCE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GCP MyResource",
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string", "description": "Resource name"},
        "specificField": {"type": "string", "description": "..."},
    },
}

def get_schema() -> Dict[str, Any]:
    return MY_RESOURCE_SCHEMA
```

### Unit Test Pattern

```python
import pytest
from unittest.mock import MagicMock, patch
from gcpoto.services.my_service import MyService
from gcpoto.models.my_service import MyResource

class TestMyService:
    @pytest.fixture
    def service(self):
        with patch("gcpoto.services.my_service.build") as mock_build:
            svc = MyService(project_id="test-project")
            svc._service = MagicMock()
            yield svc

    def test_list_resources(self, service):
        service._service.resources().list().execute.return_value = {
            "items": [{"id": "1", "name": "test"}]
        }
        results = service.list_resources()
        assert len(results) == 1
        assert results[0].name == "test"

    def test_get_resource(self, service):
        service._service.resources().get().execute.return_value = {
            "id": "1", "name": "test"
        }
        result = service.get_resource("1")
        assert result.name == "test"

    def test_create_resource(self, service):
        service._service.resources().insert().execute.return_value = {
            "id": "1", "name": "new-resource"
        }
        resource = MyResource(name="new-resource")
        result = service.create_resource(resource)
        assert result.name == "new-resource"

    def test_delete_resource(self, service):
        service._service.resources().delete().execute.return_value = {}
        assert service.delete_resource("1") is True
```

## GCP Services - Implementation Status

### Implemented
- Storage (buckets, objects, upload/download)
- Billing (accounts, project billing, budgets)
- Pub/Sub (topics, subscriptions, publish/pull)
- Resource Manager (projects, folders, IAM)
- Compute (instances - minimal)

### Target Services (google-cloud-* client libs or discovery API)
- BigQuery (datasets, tables, jobs, queries)
- Cloud Functions (functions, deploy, invoke)
- Cloud Run (services, revisions, routes)
- Cloud SQL (instances, databases, users, backups)
- Cloud DNS (zones, records)
- Cloud Logging (logs, sinks, metrics)
- Cloud Monitoring (metrics, alerts, uptime checks)
- IAM (roles, service accounts, keys, policies)
- KMS (key rings, crypto keys, encrypt/decrypt)
- Secret Manager (secrets, versions)
- VPC / Networking (networks, subnets, firewalls, routes, IPs)
- Cloud Scheduler (jobs)
- Cloud Tasks (queues, tasks)
- Artifact Registry (repositories, packages)
- Dataflow (jobs, templates)
- GKE (clusters, node pools)
- Firestore (documents, collections)
- Spanner (instances, databases)
- Memorystore / Redis (instances)

## Important Rules

- Never use `print()` for logging - use `logger`
- Never raise bare `Exception` - use exceptions from `gcpoto.exceptions`
- Always implement `from_api_response()` classmethod on models
- Always add `get_tag()` method if the resource supports labels/metadata
- Use `%s` style formatting in log calls (lazy evaluation)
- Keep service methods focused - one API call per method
- Handle pagination with `list_next()` pattern from googleapiclient
- Add type hints to all public methods
