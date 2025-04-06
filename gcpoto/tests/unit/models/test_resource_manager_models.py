"""Unit tests for the resource manager models."""

import pytest
from datetime import datetime
from typing import Dict, Any

from gcpoto.models.resource_manager import Project, Folder


def test_project_model():
    """Test the Project model."""
    # Test model creation with all attributes
    created_time = datetime.now()
    deleted_time = None
    
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
        delete_time=deleted_time,
        etag="etag123",
        labels={"env": "test"},
        tags={"owner": "test-team"}
    )
    
    # Verify attributes
    assert project.id == "projects/test-project"
    assert project.project_id == "test-project"
    assert project.project_number == "123456789012"
    assert project.display_name == "Test Project"
    assert project.parent == "folders/12345"
    assert project.state == "ACTIVE"
    assert project.create_time == created_time
    assert project.delete_time is None
    assert project.etag == "etag123"
    assert project.labels == {"env": "test"}
    assert project.tags == {"owner": "test-team"}


def test_project_validators():
    """Test the Project validators."""
    # Test name validator
    project = Project(
        project_id="test-project",
        name="test-project",  # Missing prefix
        display_name="Test Project",
        type="resourcemanager.project",
        project="test-project"
    )
    assert project.name == "projects/test-project"
    
    # Test id validator
    project = Project(
        project_id="test-project",
        display_name="Test Project",
        type="resourcemanager.project",
        project="test-project"
    )
    assert project.id == "projects/test-project"


def test_project_from_api_response():
    """Test creating Project from API response."""
    # Complete API response
    response = {
        "name": "projects/test-project",
        "projectId": "test-project",
        "projectNumber": "123456789012",
        "displayName": "Test Project",
        "parent": "folders/12345",
        "state": "ACTIVE",
        "createTime": "2023-01-01T12:00:00Z",
        "etag": "etag123",
        "labels": {"environment": "development", "team": "engineering"}
    }
    
    project = Project.from_api_response(response)
    
    assert project.project_id == "test-project"
    assert project.project_number == "123456789012"
    assert project.display_name == "Test Project"
    assert project.parent == "folders/12345"
    assert project.state == "ACTIVE"
    assert project.etag == "etag123"
    assert project.labels == {"environment": "development", "team": "engineering"}
    assert project.tags == {"environment": "development", "team": "engineering"}
    
    # Test with minimal response
    minimal_response = {
        "name": "projects/minimal-project",
        "displayName": "Minimal Project",
    }
    
    minimal_project = Project.from_api_response(minimal_response)
    assert minimal_project.project_id == "minimal-project"
    assert minimal_project.display_name == "Minimal Project"
    assert minimal_project.parent is None
    
    # Test with empty name but projectId present
    alt_response = {
        "projectId": "alt-project",
        "displayName": "Alternative Project",
        "state": "ACTIVE"
    }
    
    alt_project = Project.from_api_response(alt_response)
    assert alt_project.project_id == "alt-project"


def test_folder_model():
    """Test the Folder model."""
    # Test model creation with all attributes
    created_time = datetime.now()
    updated_time = datetime.now()
    
    folder = Folder(
        id="folders/12345",
        name="folders/12345",
        type="resourcemanager.folder",
        project="test-project",
        folder_id="12345",
        display_name="Test Folder",
        parent="organizations/67890",
        state="ACTIVE",
        create_time=created_time,
        update_time=updated_time,
        delete_time=None,
        etag="folder-etag-123",
        labels={"env": "prod"},
        tags={"purpose": "organization"}
    )
    
    # Verify attributes
    assert folder.id == "folders/12345"
    assert folder.folder_id == "12345"
    assert folder.display_name == "Test Folder"
    assert folder.parent == "organizations/67890"
    assert folder.state == "ACTIVE"
    assert folder.create_time == created_time
    assert folder.update_time == updated_time
    assert folder.delete_time is None
    assert folder.etag == "folder-etag-123"
    assert folder.labels == {"env": "prod"}
    assert folder.tags == {"purpose": "organization"}


def test_folder_validators():
    """Test the Folder validators."""
    # Test name validator
    folder = Folder(
        folder_id="67890",
        name="67890",  # Missing prefix
        display_name="Another Folder",
        parent="folders/12345",
        type="resourcemanager.folder",
        project="test-project"
    )
    assert folder.name == "folders/67890"
    
    # Test id validator
    folder = Folder(
        folder_id="67890",
        display_name="Another Folder",
        parent="folders/12345",
        type="resourcemanager.folder",
        project="test-project"
    )
    assert folder.id == "folders/67890"


def test_folder_from_api_response():
    """Test creating Folder from API response."""
    # Complete API response
    response = {
        "name": "folders/12345",
        "displayName": "API Test Folder",
        "parent": "organizations/67890",
        "state": "ACTIVE",
        "createTime": "2023-02-01T10:00:00Z",
        "updateTime": "2023-02-02T15:30:00Z",
        "etag": "folder-etag-456",
        "labels": {"department": "finance"}
    }
    
    folder = Folder.from_api_response(response)
    
    assert folder.folder_id == "12345"
    assert folder.display_name == "API Test Folder"
    assert folder.parent == "organizations/67890"
    assert folder.state == "ACTIVE"
    assert folder.etag == "folder-etag-456"
    assert folder.labels == {"department": "finance"}
    assert folder.tags == {"department": "finance"}
    
    # Test with project in parent
    project_parent_response = {
        "name": "folders/56789",
        "displayName": "Project Parent Folder",
        "parent": "projects/test-project",
    }
    
    project_folder = Folder.from_api_response(project_parent_response)
    assert project_folder.folder_id == "56789"
    assert project_folder.parent == "projects/test-project"
    assert project_folder.project == "test-project"
    
    # Test with explicit project field
    explicit_project_response = {
        "name": "folders/98765",
        "displayName": "Explicit Project Folder",
        "parent": "organizations/67890",
        "project": "explicit-project"
    }
    
    explicit_folder = Folder.from_api_response(explicit_project_response)
    assert explicit_folder.folder_id == "98765"
    assert explicit_folder.project == "explicit-project"
