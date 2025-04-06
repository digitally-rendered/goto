"""Unit tests for Resource Manager JSON schemas."""

import pytest
import json
from typing import Dict, Any
from jsonschema import validate, ValidationError
from datetime import datetime

from gcpoto.models.resource_manager import Project, Folder


def test_project_schema():
    """Test that the Project model has a valid JSON schema."""
    # Get schema from model
    schema = Project.model_json_schema()
    
    # Validate schema structure
    assert schema is not None
    assert "$defs" in schema or "properties" in schema
    
    if "properties" in schema:
        # Check required properties are in the schema
        props = schema["properties"]
        assert "project_id" in props
        assert "display_name" in props
        assert "state" in props
        
        # Validate descriptions are present
        assert "description" in props["project_id"]
        assert "description" in props["display_name"]
    
    # Create a valid instance
    project = Project(
        id="projects/test-project",
        name="projects/test-project",
        type="resourcemanager.project",
        project="test-project",
        project_id="test-project",
        project_number="123456789012",
        display_name="Test Project",
        parent="folders/12345",
        state="ACTIVE",
        labels={"env": "test"},
        tags={"purpose": "testing"}
    )
    
    # Convert to dict and validate against schema
    project_dict = project.model_dump()
    try:
        validate(instance=project_dict, schema=schema)
        assert True, "Valid instance passed schema validation"
    except ValidationError as e:
        assert False, f"Schema validation failed: {str(e)}"


def test_folder_schema():
    """Test that the Folder model has a valid JSON schema."""
    # Get schema from model
    schema = Folder.model_json_schema()
    
    # Validate schema structure
    assert schema is not None
    assert "$defs" in schema or "properties" in schema
    
    if "properties" in schema:
        # Check required properties are in the schema
        props = schema["properties"]
        assert "folder_id" in props
        assert "display_name" in props
        assert "parent" in props
        
        # Validate descriptions are present
        assert "description" in props["folder_id"]
        assert "description" in props["display_name"]
        assert "description" in props["parent"]
    
    # Create a valid instance
    folder = Folder(
        id="folders/12345",
        name="folders/12345",
        type="resourcemanager.folder",
        project="test-project",
        folder_id="12345",
        display_name="Test Folder",
        parent="organizations/67890",
        state="ACTIVE",
        labels={"env": "prod"},
        tags={"purpose": "organization"}
    )
    
    # Convert to dict and validate against schema
    folder_dict = folder.model_dump()
    try:
        validate(instance=folder_dict, schema=schema)
        assert True, "Valid instance passed schema validation"
    except ValidationError as e:
        assert False, f"Schema validation failed: {str(e)}"


def test_serialization_deserialization():
    """Test that the resource manager models can be properly serialized and deserialized."""
    # Create an instance of Project
    created_time = datetime.now().isoformat()
    project = Project(
        id="projects/test-project",
        name="projects/test-project",
        type="resourcemanager.project",
        project="test-project",
        project_id="test-project",
        project_number="123456789012",
        display_name="Test Project",
        parent="folders/12345",
        state="ACTIVE",
        create_time=created_time,
        etag="etag123",
        labels={"env": "test"},
        tags={"purpose": "testing"}
    )
    
    # Serialize to JSON
    project_json = project.model_dump_json()
    
    # Deserialize back to object
    project_dict = json.loads(project_json)
    deserialized_project = Project.model_validate(project_dict)
    
    # Verify equality
    assert deserialized_project.id == project.id
    assert deserialized_project.project_id == project.project_id
    assert deserialized_project.project_number == project.project_number
    assert deserialized_project.display_name == project.display_name
    assert deserialized_project.parent == project.parent
    assert deserialized_project.state == project.state
    assert deserialized_project.labels == project.labels
    assert deserialized_project.tags == project.tags
    
    # Test with Folder
    folder = Folder(
        id="folders/12345",
        name="folders/12345",
        type="resourcemanager.folder",
        project="test-project",
        folder_id="12345",
        display_name="Test Folder",
        parent="organizations/67890",
        state="ACTIVE",
        labels={"env": "prod"},
        tags={"purpose": "organization"}
    )
    
    # Serialize to JSON
    folder_json = folder.model_dump_json()
    
    # Deserialize back to object
    folder_dict = json.loads(folder_json)
    deserialized_folder = Folder.model_validate(folder_dict)
    
    # Verify equality
    assert deserialized_folder.id == folder.id
    assert deserialized_folder.folder_id == folder.folder_id
    assert deserialized_folder.display_name == folder.display_name
    assert deserialized_folder.parent == folder.parent
    assert deserialized_folder.state == folder.state
    assert deserialized_folder.labels == folder.labels
    assert deserialized_folder.tags == folder.tags


def test_project_api_response_compatibility():
    """Test that the Project model is compatible with API responses."""
    # Sample API response format
    api_response = {
        "name": "projects/test-project",
        "projectId": "test-project",
        "projectNumber": "123456789012",
        "displayName": "API Test Project",
        "parent": "folders/12345",
        "state": "ACTIVE",
        "createTime": "2023-01-01T12:00:00Z",
        "etag": "etag123",
        "labels": {"environment": "development", "team": "engineering"}
    }
    
    # Create model from API response
    project = Project.from_api_response(api_response)
    
    # Verify model fields match API response
    assert project.project_id == api_response["projectId"]
    assert project.display_name == api_response["displayName"]
    assert project.parent == api_response["parent"]
    assert project.state == api_response["state"]
    assert project.etag == api_response["etag"]
    assert project.labels == api_response["labels"]
    
    # Verify the model can be serialized back to a format compatible with API requests
    model_dict = project.model_dump()
    assert "project_id" in model_dict
    assert "display_name" in model_dict
    assert "state" in model_dict


def test_folder_api_response_compatibility():
    """Test that the Folder model is compatible with API responses."""
    # Sample API response format
    api_response = {
        "name": "folders/67890",
        "displayName": "API Test Folder",
        "parent": "organizations/12345",
        "state": "ACTIVE",
        "createTime": "2023-02-01T10:00:00Z",
        "updateTime": "2023-02-02T15:30:00Z",
        "etag": "folder-etag-456",
        "labels": {"department": "finance"}
    }
    
    # Create model from API response
    folder = Folder.from_api_response(api_response)
    
    # Verify model fields match API response
    assert folder.folder_id == "67890"
    assert folder.display_name == api_response["displayName"]
    assert folder.parent == api_response["parent"]
    assert folder.state == api_response["state"]
    assert folder.etag == api_response["etag"]
    assert folder.labels == api_response["labels"]
    
    # Verify the model can be serialized back to a format compatible with API requests
    model_dict = folder.model_dump()
    assert "folder_id" in model_dict
    assert "display_name" in model_dict
    assert "parent" in model_dict
