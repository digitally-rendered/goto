"""Unit tests for GCP Resource Manager models."""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any

from gcpoto.models.resource_manager import Project, Folder


class TestProjectModel:
    """Tests for the Project model."""
    
    def test_project_creation(self):
        """Test creating a Project model."""
        project_id = f"test-project-{uuid.uuid4().hex[:8]}"
        project = Project(
            id=f"projects/{project_id}",
            name=f"projects/{project_id}",
            type="resourcemanager.project",
            project=project_id,
            project_id=project_id,
            project_number="12345678",
            display_name="Test Project",
            parent="folders/98765",
            state="ACTIVE",
            labels={"env": "test"},
            tags={"team": "engineering", "purpose": "testing"}
        )
        
        assert project.id == f"projects/{project_id}"
        assert project.name == f"projects/{project_id}"
        assert project.type == "resourcemanager.project"
        assert project.project == project_id
        assert project.project_id == project_id
        assert project.project_number == "12345678"
        assert project.display_name == "Test Project"
        assert project.parent == "folders/98765"
        assert project.state == "ACTIVE"
        assert project.labels == {"env": "test"}
        assert project.tags == {"team": "engineering", "purpose": "testing"}
    
    def test_project_validators(self):
        """Test the Project model validators."""
        # Test name validator
        project_id = f"test-project-{uuid.uuid4().hex[:8]}"
        project = Project(
            id=f"projects/{project_id}",
            name=project_id,  # Missing projects/ prefix
            type="resourcemanager.project",
            project=project_id,
            project_id=project_id,
            display_name="Test Project"
        )
        
        # Validator should have added the prefix
        assert project.name == f"projects/{project_id}"
        
        # Test ID validator with missing ID
        project2 = Project(
            id="",  # Empty ID
            name=f"projects/{project_id}",
            type="resourcemanager.project",
            project=project_id,
            project_id=project_id,
            display_name="Test Project"
        )
        
        # ID should be set from project_id
        assert project2.id == f"projects/{project_id}"
    
    def test_project_from_api_response(self):
        """Test creating a Project from an API response."""
        project_id = f"test-project-{uuid.uuid4().hex[:8]}"
        create_time = datetime.now()
        response = {
            "name": f"projects/{project_id}",
            "projectId": project_id,
            "projectNumber": "12345678",
            "displayName": "Test API Project",
            "parent": "folders/98765",
            "state": "ACTIVE",
            "createTime": create_time,
            "etag": "abc123",
            "labels": {"env": "test", "managed-by": "gcpoto"}
        }
        
        project = Project.from_api_response(response)
        
        assert project.id == f"projects/{project_id}"
        assert project.name == f"projects/{project_id}"
        assert project.project_id == project_id
        assert project.project_number == "12345678"
        assert project.display_name == "Test API Project"
        assert project.parent == "folders/98765"
        assert project.state == "ACTIVE"
        assert project.create_time == create_time
        assert project.etag == "abc123"
        assert project.labels == {"env": "test", "managed-by": "gcpoto"}
        assert project.tags == {"env": "test", "managed-by": "gcpoto"}
        
        # Test with minimal response
        minimal_response = {
            "name": f"projects/{project_id}",
            "displayName": "Minimal Project"
        }
        
        minimal_project = Project.from_api_response(minimal_response)
        assert minimal_project.id == f"projects/{project_id}"
        assert minimal_project.project_id == project_id
        assert minimal_project.display_name == "Minimal Project"


class TestFolderModel:
    """Tests for the Folder model."""
    
    def test_folder_creation(self):
        """Test creating a Folder model."""
        folder_id = f"{uuid.uuid4().hex[:8]}"
        folder = Folder(
            id=f"folders/{folder_id}",
            name=f"folders/{folder_id}",
            type="resourcemanager.folder",
            project="test-project",
            folder_id=folder_id,
            display_name="Test Folder",
            parent="organizations/12345",
            state="ACTIVE",
            labels={"env": "test"},
            tags={"team": "engineering", "purpose": "testing"}
        )
        
        assert folder.id == f"folders/{folder_id}"
        assert folder.name == f"folders/{folder_id}"
        assert folder.type == "resourcemanager.folder"
        assert folder.project == "test-project"
        assert folder.folder_id == folder_id
        assert folder.display_name == "Test Folder"
        assert folder.parent == "organizations/12345"
        assert folder.state == "ACTIVE"
        assert folder.labels == {"env": "test"}
        assert folder.tags == {"team": "engineering", "purpose": "testing"}
    
    def test_folder_validators(self):
        """Test the Folder model validators."""
        # Test name validator
        folder_id = f"{uuid.uuid4().hex[:8]}"
        folder = Folder(
            id=f"folders/{folder_id}",
            name=folder_id,  # Missing folders/ prefix
            type="resourcemanager.folder",
            project="test-project",
            folder_id=folder_id,
            display_name="Test Folder",
            parent="organizations/12345"
        )
        
        # Validator should have added the prefix
        assert folder.name == f"folders/{folder_id}"
        
        # Test ID validator with missing ID
        folder2 = Folder(
            id="",  # Empty ID
            name=f"folders/{folder_id}",
            type="resourcemanager.folder",
            project="test-project",
            folder_id=folder_id,
            display_name="Test Folder",
            parent="organizations/12345"
        )
        
        # ID should be set from folder_id
        assert folder2.id == f"folders/{folder_id}"
    
    def test_folder_from_api_response(self):
        """Test creating a Folder from an API response."""
        folder_id = f"{uuid.uuid4().hex[:8]}"
        create_time = datetime.now()
        update_time = datetime.now()
        response = {
            "name": f"folders/{folder_id}",
            "displayName": "Test API Folder",
            "parent": "organizations/12345",
            "state": "ACTIVE",
            "createTime": create_time,
            "updateTime": update_time,
            "etag": "def456"
        }
        
        folder = Folder.from_api_response(response)
        
        assert folder.id == f"folders/{folder_id}"
        assert folder.name == f"folders/{folder_id}"
        assert folder.folder_id == folder_id
        assert folder.display_name == "Test API Folder"
        assert folder.parent == "organizations/12345"
        assert folder.state == "ACTIVE"
        assert folder.create_time == create_time
        assert folder.update_time == update_time
        assert folder.etag == "def456"
        
        # Test with parent in projects format
        project_parent_response = {
            "name": f"folders/{folder_id}",
            "displayName": "Project Parent Folder",
            "parent": "projects/test-project",
        }
        
        project_folder = Folder.from_api_response(project_parent_response)
        assert project_folder.id == f"folders/{folder_id}"
        assert project_folder.project == "test-project"
        
        # Test with project field
        project_field_response = {
            "name": f"folders/{folder_id}",
            "displayName": "Project Field Folder",
            "parent": "organizations/12345",
            "project": "explicit-project"
        }
        
        explicit_project_folder = Folder.from_api_response(project_field_response)
        assert explicit_project_folder.project == "explicit-project"
