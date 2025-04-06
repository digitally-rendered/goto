"""Unit tests for GCP Resource Manager service."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, Mock, MagicMock

from google.cloud import resourcemanager_v3
from google.longrunning import operations_pb2
from google.protobuf import timestamp_pb2, any_pb2

from gcpoto.services.resource_manager import ResourceManagerService
from gcpoto.models.resource_manager import Project, Folder


@pytest.fixture
def mock_projects_client():
    """Create a mock ProjectsClient."""
    with patch('google.cloud.resourcemanager_v3.ProjectsClient') as mock_client:
        # Setup mock operations client
        operations_client = MagicMock()
        mock_client.return_value.transport.operations_client = operations_client
        
        # Setup other return values
        mock_client.return_value.list_projects.return_value = []
        mock_client.return_value.get_project.return_value = None
        mock_client.return_value.create_project.return_value = None
        mock_client.return_value.update_project.return_value = None
        mock_client.return_value.delete_project.return_value = None
        mock_client.return_value.undelete_project.return_value = None
        mock_client.return_value.move_project.return_value = None
        
        yield mock_client.return_value


@pytest.fixture
def mock_folders_client():
    """Create a mock FoldersClient."""
    with patch('google.cloud.resourcemanager_v3.FoldersClient') as mock_client:
        # Setup mock operations client
        operations_client = MagicMock()
        mock_client.return_value.transport.operations_client = operations_client
        
        # Setup other return values
        mock_client.return_value.list_folders.return_value = []
        mock_client.return_value.get_folder.return_value = None
        mock_client.return_value.create_folder.return_value = None
        mock_client.return_value.update_folder.return_value = None
        mock_client.return_value.delete_folder.return_value = None
        mock_client.return_value.undelete_folder.return_value = None
        mock_client.return_value.move_folder.return_value = None
        
        yield mock_client.return_value


@pytest.fixture
def mock_resource_manager_service(mock_projects_client, mock_folders_client):
    """Create a ResourceManagerService with mocked clients."""
    with patch('gcpoto.services.resource_manager.ResourceManagerService._wait_for_operation') as mock_wait:
        # Configure the mock wait_for_operation to return immediately
        mock_wait.return_value = None
        
        # Create the service
        service = ResourceManagerService(project_id="test-project")
        service.projects_client = mock_projects_client
        service.folders_client = mock_folders_client
        
        yield service


@pytest.fixture
def sample_project_proto():
    """Create a sample Project proto response."""
    project = resourcemanager_v3.Project()
    project.name = "projects/test-project"
    project.project_id = "test-project"
    project.project_number = "12345678"
    project.display_name = "Test Project"
    project.parent = "folders/98765"
    project.state = resourcemanager_v3.Project.State.ACTIVE
    
    # Set timestamps
    create_time = timestamp_pb2.Timestamp()
    create_time.FromDatetime(datetime.now())
    project.create_time = create_time
    
    update_time = timestamp_pb2.Timestamp()
    update_time.FromDatetime(datetime.now())
    project.update_time = update_time
    
    project.etag = "abc123"
    project.labels["env"] = "test"
    project.labels["team"] = "engineering"
    
    return project


@pytest.fixture
def sample_folder_proto():
    """Create a sample Folder proto response."""
    folder = resourcemanager_v3.Folder()
    folder.name = "folders/test-folder"
    folder.display_name = "Test Folder"
    folder.parent = "organizations/12345"
    folder.state = resourcemanager_v3.Folder.State.ACTIVE
    
    # Set timestamps
    create_time = timestamp_pb2.Timestamp()
    create_time.FromDatetime(datetime.now())
    folder.create_time = create_time
    
    update_time = timestamp_pb2.Timestamp()
    update_time.FromDatetime(datetime.now())
    folder.update_time = update_time
    
    folder.etag = "def456"
    
    return folder


@pytest.fixture
def mock_operation():
    """Create a mock Operation that is done and successful."""
    operation = operations_pb2.Operation()
    operation.name = "operations/test-operation"
    operation.done = True
    
    # Create a response Any proto
    response = any_pb2.Any()
    operation.response.CopyFrom(response)
    
    return operation


class TestResourceManagerService:
    """Tests for the ResourceManagerService class."""
    
    def test_list_projects(self, mock_resource_manager_service, sample_project_proto):
        """Test listing projects."""
        # Setup
        projects_client = mock_resource_manager_service.projects_client
        projects_client.list_projects.return_value = [sample_project_proto]
        
        # Execute
        projects = mock_resource_manager_service.list_projects()
        
        # Verify
        assert len(projects) == 1
        assert projects[0].id == "projects/test-project"
        assert projects[0].project_id == "test-project"
        assert projects[0].display_name == "Test Project"
        
        # Verify client was called correctly
        projects_client.list_projects.assert_called_once()
        
        # Test with parent
        mock_resource_manager_service.list_projects(parent="organizations/12345")
        # 2nd call should include parent
        assert projects_client.list_projects.call_count == 2
    
    def test_get_project(self, mock_resource_manager_service, sample_project_proto):
        """Test getting a project."""
        # Setup
        projects_client = mock_resource_manager_service.projects_client
        projects_client.get_project.return_value = sample_project_proto
        
        # Execute
        project = mock_resource_manager_service.get_project("test-project")
        
        # Verify
        assert project.id == "projects/test-project"
        assert project.project_id == "test-project"
        assert project.display_name == "Test Project"
        
        # Verify client was called correctly
        projects_client.get_project.assert_called_once_with(name="projects/test-project")
        
        # Test with already formatted name
        mock_resource_manager_service.get_project("projects/test-project-2")
        projects_client.get_project.assert_called_with(name="projects/test-project-2")
        
        # Test error handling
        projects_client.get_project.side_effect = Exception("Not found")
        with pytest.raises(Exception, match="Failed to get project"):
            mock_resource_manager_service.get_project("non-existent")
    
    def test_create_project(self, mock_resource_manager_service, sample_project_proto):
        """Test creating a project."""
        # Setup
        projects_client = mock_resource_manager_service.projects_client
        projects_client.get_project.return_value = sample_project_proto
        
        # Mock the long-running operation
        operation = MagicMock()
        projects_client.create_project.return_value = operation
        
        # Execute
        project = mock_resource_manager_service.create_project(
            project_id="test-project",
            display_name="Test Project",
            parent="folders/98765",
            labels={"env": "test"},
            tags={"team": "engineering"}
        )
        
        # Verify
        assert project.id == "projects/test-project"  # The result comes from get_project
        projects_client.create_project.assert_called_once()
        mock_resource_manager_service._wait_for_operation.assert_called_once_with(operation)
        
        # Test error handling
        projects_client.create_project.side_effect = Exception("Creation failed")
        with pytest.raises(Exception, match="Failed to create project"):
            mock_resource_manager_service.create_project(
                project_id="error-project",
                display_name="Error Project"
            )
    
    def test_update_project(self, mock_resource_manager_service, sample_project_proto):
        """Test updating a project."""
        # Setup
        projects_client = mock_resource_manager_service.projects_client
        projects_client.get_project.return_value = sample_project_proto
        
        # Mock the long-running operation
        operation = MagicMock()
        projects_client.update_project.return_value = operation
        
        # Execute - test updating display name only
        project = mock_resource_manager_service.update_project(
            project_id="test-project",
            display_name="Updated Project"
        )
        
        # Verify
        assert project.id == "projects/test-project"  # The result comes from get_project
        projects_client.update_project.assert_called_once()
        mock_resource_manager_service._wait_for_operation.assert_called_once_with(operation)
        
        # Test updating labels
        mock_resource_manager_service._wait_for_operation.reset_mock()
        projects_client.update_project.reset_mock()
        
        project = mock_resource_manager_service.update_project(
            project_id="test-project",
            labels={"env": "prod"},
            tags={"cost-center": "12345"}
        )
        
        # Verify
        projects_client.update_project.assert_called_once()
        mock_resource_manager_service._wait_for_operation.assert_called_once_with(operation)
        
        # Test error handling
        projects_client.update_project.side_effect = Exception("Update failed")
        with pytest.raises(Exception, match="Failed to update project"):
            mock_resource_manager_service.update_project(
                project_id="test-project",
                display_name="Error Update"
            )
    
    def test_delete_project(self, mock_resource_manager_service):
        """Test deleting a project."""
        # Setup
        projects_client = mock_resource_manager_service.projects_client
        
        # Mock the long-running operation
        operation = MagicMock()
        projects_client.delete_project.return_value = operation
        
        # Execute
        result = mock_resource_manager_service.delete_project("test-project")
        
        # Verify
        assert result is True
        projects_client.delete_project.assert_called_once_with(name="projects/test-project")
        mock_resource_manager_service._wait_for_operation.assert_called_once_with(operation)
        
        # Test error handling
        projects_client.delete_project.side_effect = Exception("Deletion failed")
        with pytest.raises(Exception, match="Failed to delete project"):
            mock_resource_manager_service.delete_project("test-project")
    
    def test_undelete_project(self, mock_resource_manager_service, sample_project_proto):
        """Test undeleting a project."""
        # Setup
        projects_client = mock_resource_manager_service.projects_client
        projects_client.get_project.return_value = sample_project_proto
        
        # Mock the long-running operation
        operation = MagicMock()
        projects_client.undelete_project.return_value = operation
        
        # Execute
        project = mock_resource_manager_service.undelete_project("test-project")
        
        # Verify
        assert project.id == "projects/test-project"  # The result comes from get_project
        projects_client.undelete_project.assert_called_once_with(name="projects/test-project")
        mock_resource_manager_service._wait_for_operation.assert_called_once_with(operation)
        
        # Test error handling
        projects_client.undelete_project.side_effect = Exception("Undeletion failed")
        with pytest.raises(Exception, match="Failed to undelete project"):
            mock_resource_manager_service.undelete_project("test-project")
    
    def test_list_folders(self, mock_resource_manager_service, sample_folder_proto):
        """Test listing folders."""
        # Setup
        folders_client = mock_resource_manager_service.folders_client
        folders_client.list_folders.return_value = [sample_folder_proto]
        
        # Execute
        folders = mock_resource_manager_service.list_folders()
        
        # Verify
        assert len(folders) == 1
        assert folders[0].id == "folders/test-folder"
        assert folders[0].display_name == "Test Folder"
        
        # Verify client was called correctly
        folders_client.list_folders.assert_called_once()
        
        # Test with parent
        mock_resource_manager_service.list_folders(parent="organizations/12345")
        # 2nd call should include parent
        assert folders_client.list_folders.call_count == 2
    
    def test_get_folder(self, mock_resource_manager_service, sample_folder_proto):
        """Test getting a folder."""
        # Setup
        folders_client = mock_resource_manager_service.folders_client
        folders_client.get_folder.return_value = sample_folder_proto
        
        # Execute
        folder = mock_resource_manager_service.get_folder("test-folder")
        
        # Verify
        assert folder.id == "folders/test-folder"
        assert folder.display_name == "Test Folder"
        
        # Verify client was called correctly
        folders_client.get_folder.assert_called_once_with(name="folders/test-folder")
        
        # Test with already formatted name
        mock_resource_manager_service.get_folder("folders/test-folder-2")
        folders_client.get_folder.assert_called_with(name="folders/test-folder-2")
        
        # Test error handling
        folders_client.get_folder.side_effect = Exception("Not found")
        with pytest.raises(Exception, match="Failed to get folder"):
            mock_resource_manager_service.get_folder("non-existent")
    
    def test_create_folder(self, mock_resource_manager_service, sample_folder_proto):
        """Test creating a folder."""
        # Setup
        folders_client = mock_resource_manager_service.folders_client
        folders_client.get_folder.return_value = sample_folder_proto
        
        # Mock the long-running operation and result
        operation = MagicMock()
        result_folder = MagicMock()
        result_folder.name = "folders/test-folder"
        mock_resource_manager_service._wait_for_operation.return_value = result_folder
        
        folders_client.create_folder.return_value = operation
        
        # Execute
        folder = mock_resource_manager_service.create_folder(
            display_name="Test Folder",
            parent="organizations/12345",
            tags={"team": "engineering"}
        )
        
        # Verify
        assert folder.id == "folders/test-folder"  # The result comes from get_folder
        folders_client.create_folder.assert_called_once()
        mock_resource_manager_service._wait_for_operation.assert_called_once_with(operation)
        
        # Test error handling
        folders_client.create_folder.side_effect = Exception("Creation failed")
        with pytest.raises(Exception, match="Failed to create folder"):
            mock_resource_manager_service.create_folder(
                display_name="Error Folder",
                parent="organizations/12345"
            )
    
    def test_update_folder(self, mock_resource_manager_service, sample_folder_proto):
        """Test updating a folder."""
        # Setup
        folders_client = mock_resource_manager_service.folders_client
        folders_client.get_folder.return_value = sample_folder_proto
        
        # Mock the long-running operation
        operation = MagicMock()
        folders_client.update_folder.return_value = operation
        
        # Execute
        folder = mock_resource_manager_service.update_folder(
            folder_id="test-folder",
            display_name="Updated Folder"
        )
        
        # Verify
        assert folder.id == "folders/test-folder"  # The result comes from get_folder
        folders_client.update_folder.assert_called_once()
        mock_resource_manager_service._wait_for_operation.assert_called_once_with(operation)
        
        # Test error handling
        folders_client.update_folder.side_effect = Exception("Update failed")
        with pytest.raises(Exception, match="Failed to update folder"):
            mock_resource_manager_service.update_folder(
                folder_id="test-folder",
                display_name="Error Update"
            )
    
    def test_delete_folder(self, mock_resource_manager_service):
        """Test deleting a folder."""
        # Setup
        folders_client = mock_resource_manager_service.folders_client
        
        # Mock the long-running operation
        operation = MagicMock()
        folders_client.delete_folder.return_value = operation
        
        # Execute
        result = mock_resource_manager_service.delete_folder("test-folder")
        
        # Verify
        assert result is True
        folders_client.delete_folder.assert_called_once_with(name="folders/test-folder")
        mock_resource_manager_service._wait_for_operation.assert_called_once_with(operation)
        
        # Test error handling
        folders_client.delete_folder.side_effect = Exception("Deletion failed")
        with pytest.raises(Exception, match="Failed to delete folder"):
            mock_resource_manager_service.delete_folder("test-folder")
    
    def test_undelete_folder(self, mock_resource_manager_service, sample_folder_proto):
        """Test undeleting a folder."""
        # Setup
        folders_client = mock_resource_manager_service.folders_client
        folders_client.get_folder.return_value = sample_folder_proto
        
        # Mock the long-running operation
        operation = MagicMock()
        folders_client.undelete_folder.return_value = operation
        
        # Execute
        folder = mock_resource_manager_service.undelete_folder("test-folder")
        
        # Verify
        assert folder.id == "folders/test-folder"  # The result comes from get_folder
        folders_client.undelete_folder.assert_called_once_with(name="folders/test-folder")
        mock_resource_manager_service._wait_for_operation.assert_called_once_with(operation)
        
        # Test error handling
        folders_client.undelete_folder.side_effect = Exception("Undeletion failed")
        with pytest.raises(Exception, match="Failed to undelete folder"):
            mock_resource_manager_service.undelete_folder("test-folder")
    
    def test_move_folder(self, mock_resource_manager_service, sample_folder_proto):
        """Test moving a folder."""
        # Setup
        folders_client = mock_resource_manager_service.folders_client
        folders_client.get_folder.return_value = sample_folder_proto
        
        # Mock the long-running operation
        operation = MagicMock()
        folders_client.move_folder.return_value = operation
        
        # Execute
        folder = mock_resource_manager_service.move_folder(
            folder_id="test-folder",
            new_parent="organizations/67890"
        )
        
        # Verify
        assert folder.id == "folders/test-folder"  # The result comes from get_folder
        folders_client.move_folder.assert_called_once()
        mock_resource_manager_service._wait_for_operation.assert_called_once_with(operation)
        
        # Test error handling
        folders_client.move_folder.side_effect = Exception("Move failed")
        with pytest.raises(Exception, match="Failed to move folder"):
            mock_resource_manager_service.move_folder(
                folder_id="test-folder",
                new_parent="organizations/67890"
            )
    
    def test_move_project(self, mock_resource_manager_service, sample_project_proto):
        """Test moving a project."""
        # Setup
        projects_client = mock_resource_manager_service.projects_client
        projects_client.get_project.return_value = sample_project_proto
        
        # Mock the long-running operation
        operation = MagicMock()
        projects_client.move_project.return_value = operation
        
        # Execute
        project = mock_resource_manager_service.move_project(
            project_id="test-project",
            new_parent="organizations/67890"
        )
        
        # Verify
        assert project.id == "projects/test-project"  # The result comes from get_project
        projects_client.move_project.assert_called_once()
        mock_resource_manager_service._wait_for_operation.assert_called_once_with(operation)
        
        # Test error handling
        projects_client.move_project.side_effect = Exception("Move failed")
        with pytest.raises(Exception, match="Failed to move project"):
            mock_resource_manager_service.move_project(
                project_id="test-project",
                new_parent="organizations/67890"
            )
    
    def test_base_methods(self, mock_resource_manager_service, sample_project_proto):
        """Test the base class methods implementation."""
        # Setup for get_resource
        projects_client = mock_resource_manager_service.projects_client
        projects_client.get_project.return_value = sample_project_proto
        
        # Test get_resource
        project = mock_resource_manager_service.get_resource("test-project")
        assert project.id == "projects/test-project"
        
        # Setup for list_resources
        projects_client.list_projects.return_value = [sample_project_proto]
        
        # Test list_resources
        projects = mock_resource_manager_service.list_resources()
        assert len(projects) == 1
        assert projects[0].id == "projects/test-project"
        
        # Setup for create_resource
        project_model = Project(
            id="projects/new-project",
            name="projects/new-project",
            type="resourcemanager.project",
            project="new-project",
            project_id="new-project",
            display_name="New Project",
            parent="folders/98765",
            tags={"env": "test"}
        )
        
        # Test create_resource
        with patch.object(mock_resource_manager_service, 'create_project') as mock_create:
            mock_create.return_value = project_model
            created = mock_resource_manager_service.create_resource(project_model)
            assert created.id == "projects/new-project"
            mock_create.assert_called_once()
        
        # Setup for update_resource
        project_model.display_name = "Updated Project"
        
        # Test update_resource
        with patch.object(mock_resource_manager_service, 'update_project') as mock_update:
            mock_update.return_value = project_model
            updated = mock_resource_manager_service.update_resource(project_model)
            assert updated.id == "projects/new-project"
            assert updated.display_name == "Updated Project"
            mock_update.assert_called_once()
        
        # Test delete_resource
        with patch.object(mock_resource_manager_service, 'delete_project') as mock_delete:
            mock_delete.return_value = True
            result = mock_resource_manager_service.delete_resource("test-project")
            assert result is True
            mock_delete.assert_called_once_with("test-project")
