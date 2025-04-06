"""Tests for the base models."""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from gcpoto.models.base import GCPResource
from gcpoto.schemas.base import BASE_RESOURCE_SCHEMA


def test_gcp_resource_model_creation():
    """Test creating a GCPResource instance."""
    # Test creating a resource with required fields
    resource = GCPResource(
        id="test-id",
        name="test-resource",
        type="test-type",
        project="test-project"
    )
    
    assert resource.id == "test-id"
    assert resource.name == "test-resource"
    assert resource.type == "test-type"
    assert resource.project == "test-project"
    assert resource.labels is None
    assert resource.created is None
    assert resource.updated is None


def test_gcp_resource_with_optional_fields():
    """Test creating a GCPResource with all fields."""
    # Create timestamp objects
    created = datetime.fromisoformat("2023-01-01T00:00:00")
    updated = datetime.fromisoformat("2023-01-02T00:00:00")
    
    # Test creating a resource with all fields
    resource = GCPResource(
        id="test-id",
        name="test-resource",
        type="test-type",
        project="test-project",
        labels={"env": "test", "owner": "tester"},
        created=created,
        updated=updated
    )
    
    assert resource.id == "test-id"
    assert resource.name == "test-resource"
    assert resource.type == "test-type"
    assert resource.project == "test-project"
    assert resource.labels == {"env": "test", "owner": "tester"}
    assert resource.created == created
    assert resource.updated == updated


def test_gcp_resource_validation():
    """Test validation of GCPResource model."""
    # Test missing required fields
    with pytest.raises(ValidationError):
        GCPResource(id="test-id")
    
    with pytest.raises(ValidationError):
        GCPResource(id="test-id", name="test-resource")


def test_gcp_resource_to_dict():
    """Test converting a GCPResource to a dictionary."""
    resource = GCPResource(
        id="test-id",
        name="test-resource",
        type="test-type",
        project="test-project"
    )
    
    resource_dict = resource.to_dict()
    assert resource_dict["id"] == "test-id"
    assert resource_dict["name"] == "test-resource"
    assert resource_dict["type"] == "test-type"
    assert resource_dict["project"] == "test-project"
    assert "labels" not in resource_dict
    assert "created" not in resource_dict
    assert "updated" not in resource_dict


def test_gcp_resource_from_api_response():
    """Test creating a GCPResource from an API response."""
    api_response = {
        "id": "123456789",
        "name": "my-resource",
        "kind": "compute#instance",
        "projectId": "my-project",
        "labels": {"env": "prod"},
        "creationTimestamp": "2023-01-01T00:00:00Z",
        "updateTime": "2023-01-02T00:00:00Z"
    }
    
    resource = GCPResource.from_api_response(api_response)
    
    assert resource.id == "123456789"
    assert resource.name == "my-resource"
    assert resource.type == "instance"
    assert resource.project == "my-project"
    assert resource.labels == {"env": "prod"}
    # Check datetime objects are properly parsed
    assert resource.created.isoformat().startswith("2023-01-01T00:00:00")
    assert resource.updated.isoformat().startswith("2023-01-02T00:00:00")


def test_json_schema_representation():
    """Test the JSON Schema representation of the model."""
    schema = GCPResource.model_json_schema()
    
    # Verify the schema has the expected structure
    assert "$schema" in json.dumps(schema)
    assert "title" in schema
    assert schema["title"] == "GCPResource"
    assert "properties" in schema
    assert "id" in schema["properties"]
    assert "name" in schema["properties"]
    assert "type" in schema["properties"]
    assert "project" in schema["properties"]
    
    # Verify that our model schema is using elements from our JSON schema
    assert "id" in BASE_RESOURCE_SCHEMA["properties"]
    assert "name" in BASE_RESOURCE_SCHEMA["properties"]
    assert "type" in BASE_RESOURCE_SCHEMA["properties"]
    assert "project" in BASE_RESOURCE_SCHEMA["properties"]
