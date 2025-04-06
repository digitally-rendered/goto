"""Integration tests for the Resource Manager service."""

import os
import time
import uuid
import pytest
from typing import Dict, Any, List

from gcpoto.services.resource_manager import ResourceManagerService
from gcpoto.models.resource_manager import Project, Folder
from tests.integration.conftest import ResourceTracker, register_resource_for_cleanup


pytest.mark.integration = pytest.mark.skipif(
    "GCPOTO_RUN_INTEGRATION_TESTS" not in os.environ,
    reason="Integration tests are skipped unless GCPOTO_RUN_INTEGRATION_TESTS is set",
)


@pytest.fixture(scope="session")  # Changed from module to session
def resource_manager_service(test_project_id: str, credentials_file: str) -> ResourceManagerService:
    """Create a ResourceManagerService instance for integration tests.
    
    Args:
        test_project_id: The GCP project ID to use.
        credentials_file: Path to credentials file, if any.
        
    Returns:
        ResourceManagerService: An initialized resource manager service.
    """
    return ResourceManagerService(
        project_id=test_project_id,
        credentials_file=credentials_file
    )


@pytest.fixture(scope="module")
def test_project_name(test_resource_prefix: str) -> str:
    """Generate a unique project ID for testing.
    
    Args:
        test_resource_prefix: Prefix for test resources.
        
    Returns:
        str: A unique project ID.
    """
    # Project IDs must be between 6 and 30 characters, lowercase letters, numbers, and hyphens
    # Must start with a letter and can't end with a hyphen
    return f"{test_resource_prefix}-proj-{uuid.uuid4().hex[:8]}".lower()


@pytest.fixture(scope="module")
def test_folder_name(test_resource_prefix: str) -> str:
    """Generate a unique folder display name for testing.
    
    Args:
        test_resource_prefix: Prefix for test resources.
        
    Returns:
        str: A unique folder display name.
    """
    return f"{test_resource_prefix} Folder {uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def organization_id() -> str:
    """Get the organization ID for testing.
    
    This will use the GCPOTO_TEST_ORG_ID environment variable.
    
    Returns:
        str: The organization ID.
        
    Raises:
        pytest.skip: If no organization ID is set, these tests will be skipped.
    """
    org_id = os.environ.get("GCPOTO_TEST_ORG_ID")
    if not org_id:
        pytest.skip("Organization ID not set. Set GCPOTO_TEST_ORG_ID to run folder tests.")
    return org_id


@pytest.mark.integration
class TestResourceManagerIntegration:
    """Integration tests for the Resource Manager service."""
    
    def test_list_projects(self, resource_manager_service: ResourceManagerService):
        """Test listing projects."""
        projects = resource_manager_service.list_projects()
        
        # Just verify we can get a list without error
        assert isinstance(projects, list)
        assert all(isinstance(p, Project) for p in projects)
        
        # Print some info for debugging
        print(f"Found {len(projects)} projects")
        for project in projects[:5]:  # Just print first 5 to avoid too much output
            print(f"- {project.project_id} ({project.display_name})")
    
    def test_get_project(self, resource_manager_service: ResourceManagerService, test_project_id: str):
        """Test getting project details."""
        # Get the current project we're running tests in
        project = resource_manager_service.get_project(test_project_id)
        
        # Verify project details
        assert project.project_id == test_project_id
        assert project.id == f"projects/{test_project_id}"
        assert project.display_name  # Should have a display name
        
        # Print project details for debugging
        print(f"Project ID: {project.project_id}")
        print(f"Display Name: {project.display_name}")
        print(f"Parent: {project.parent}")
        print(f"State: {project.state}")
        print(f"Created: {project.create_time}")
        if project.labels:
            print(f"Labels: {project.labels}")
        if project.tags:
            print(f"Tags: {project.tags}")


@pytest.mark.integration
@pytest.mark.skipif(
    "GCPOTO_CREATE_RESOURCES" not in os.environ,
    reason="Creation tests skipped unless GCPOTO_CREATE_RESOURCES is set"
)
class TestResourceManagerCreation:
    """Tests for creating and managing projects and folders.
    
    These tests are skipped by default because they create actual GCP resources
    which can lead to costs and require elevated permissions.
    
    To run these tests, set GCPOTO_CREATE_RESOURCES=1 along with other required
    environment variables.
    """
    
    def test_create_update_delete_project(self, resource_manager_service: ResourceManagerService, 
                                         test_project_name: str, 
                                         organization_id: str,
                                         common_tags: Dict[str, str],
                                         resource_tracker: ResourceTracker):
        """Test creating, updating, and then deleting a project."""
        # Skip this test unless specifically enabled - it requires org admin permissions
        if not os.environ.get("GCPOTO_TEST_CREATE_PROJECT"):
            pytest.skip("Project creation test skipped. Set GCPOTO_TEST_CREATE_PROJECT=1 to enable.")
        
        # Create custom tags for tracking this test
        custom_tags = {
            **common_tags,
            "test-type": "project-lifecycle",
            "created-at": time.strftime("%Y-%m-%d")
        }
        
        # Use the context manager to ensure cleanup even in case of test failure
        with register_resource_for_cleanup(resource_tracker, 'project', project_id=test_project_name):
            # Create a project
            project = resource_manager_service.create_project(
                project_id=test_project_name,
                display_name=f"Test Project {test_project_name}",
                parent=f"organizations/{organization_id}",
                labels={"purpose": "integration-testing", "environment": "test"},
                tags=custom_tags
            )
            
            # Register the project for cleanup
            resource_tracker.register_project(test_project_name)
            
            # Verify the project was created
            assert project.project_id == test_project_name
            assert project.display_name == f"Test Project {test_project_name}"
            assert project.parent == f"organizations/{organization_id}"
            
            # Verify tags were applied
            assert project.tags is not None
            for key, value in custom_tags.items():
                assert project.tags.get(key) == value
            
            print(f"Created project: {project.project_id}")
            
            # Get the project to verify it exists
            retrieved_project = resource_manager_service.get_project(test_project_name)
            assert retrieved_project.project_id == test_project_name
            assert retrieved_project.display_name == f"Test Project {test_project_name}"
            
            # Wait briefly before updating to make sure it's fully created
            time.sleep(5)
            
            # Update the project display name and labels
            updated_project = resource_manager_service.update_project(
                project_id=test_project_name,
                display_name=f"Updated Project {test_project_name}",
                labels={"purpose": "integration-testing", "environment": "staging"},
                tags={**custom_tags, "updated": "true"}
            )
            
            # Verify the update
            assert updated_project.display_name == f"Updated Project {test_project_name}"
            assert updated_project.tags.get("updated") == "true"
            assert updated_project.labels.get("environment") == "staging"
            
            print(f"Updated project: {updated_project.display_name}")
            
            # Wait briefly before deleting to ensure update is processed
            time.sleep(5)
            
            # Delete the project
            success = resource_manager_service.delete_project(test_project_name)
            assert success
            
            # Remove from the resource tracker since we deleted it manually
            resource_tracker.resource_manager_projects.remove(test_project_name)
            print(f"Deleted project: {test_project_name}")
    
    def test_create_update_delete_folder(self, resource_manager_service: ResourceManagerService,
                                        test_folder_name: str,
                                        organization_id: str,
                                        common_tags: Dict[str, str]):
        """Test creating, updating, and deleting a folder."""
        # Skip this test unless specifically enabled - it requires org admin permissions
        if not os.environ.get("GCPOTO_TEST_CREATE_FOLDER"):
            pytest.skip("Folder creation test skipped. Set GCPOTO_TEST_CREATE_FOLDER=1 to enable.")
        
        folder_id = None
        try:
            custom_tags = {
                **common_tags,
                "test-type": "folder-lifecycle",
                "created-at": time.strftime("%Y-%m-%d")
            }
            
            # Create a folder
            folder = resource_manager_service.create_folder(
                display_name=test_folder_name,
                parent=f"organizations/{organization_id}",
                tags=custom_tags
            )
            
            # Store folder ID for cleanup
            folder_id = folder.folder_id
            
            # Verify the folder was created
            assert folder.display_name == test_folder_name
            assert folder.parent == f"organizations/{organization_id}"
            
            print(f"Created folder: {folder.name} (ID: {folder.folder_id})")
            
            # Get the folder to verify it exists
            retrieved_folder = resource_manager_service.get_folder(folder.folder_id)
            assert retrieved_folder.folder_id == folder.folder_id
            assert retrieved_folder.display_name == test_folder_name
            
            # Update the folder
            updated_name = f"{test_folder_name} Updated"
            updated_folder = resource_manager_service.update_folder(
                folder_id=folder.folder_id,
                display_name=updated_name
            )
            
            # Verify the update
            assert updated_folder.display_name == updated_name
            print(f"Updated folder name to: {updated_folder.display_name}")
            
            # Verify update by getting the folder again
            retrieved_updated_folder = resource_manager_service.get_folder(folder.folder_id)
            assert retrieved_updated_folder.display_name == updated_name
            
            # Wait briefly before deleting
            time.sleep(2)
            
            # Delete the folder
            success = resource_manager_service.delete_folder(folder.folder_id)
            assert success
            print(f"Deleted folder: {folder.name}")
            
            # Verify the folder was deleted by checking the list
            current_folders = resource_manager_service.list_folders(parent=f"organizations/{organization_id}")
            assert not any(f.folder_id == folder.folder_id for f in current_folders)
            
        except Exception as e:
            # Make sure to attempt cleanup if something goes wrong
            print(f"Error in folder lifecycle test: {e}")
            if folder_id:
                try:
                    resource_manager_service.delete_folder(folder_id)
                    print(f"Cleaned up folder after error: {folder_id}")
                except Exception as cleanup_error:
                    print(f"Failed to clean up folder: {cleanup_error}")
            raise
    
    def test_create_subfolder_hierarchy(self, resource_manager_service: ResourceManagerService,
                                      test_folder_name: str,
                                      organization_id: str,
                                      common_tags: Dict[str, str]):
        """Test creating a hierarchy of folders (parent and child)."""
        # Skip this test unless specifically enabled - it requires org admin permissions
        if not os.environ.get("GCPOTO_TEST_CREATE_FOLDER"):
            pytest.skip("Folder hierarchy test skipped. Set GCPOTO_TEST_CREATE_FOLDER=1 to enable.")
            
        parent_folder_id = None
        child_folder_id = None
        
        try:
            # Create a parent folder
            parent_folder = resource_manager_service.create_folder(
                display_name=f"{test_folder_name}-parent",
                parent=f"organizations/{organization_id}",
                tags={**common_tags, "level": "parent"}
            )
            
            parent_folder_id = parent_folder.folder_id
            print(f"Created parent folder: {parent_folder.name}")
            
            # Create a child folder under the parent
            child_folder = resource_manager_service.create_folder(
                display_name=f"{test_folder_name}-child",
                parent=f"folders/{parent_folder_id}",
                tags={**common_tags, "level": "child"}
            )
            
            child_folder_id = child_folder.folder_id
            print(f"Created child folder: {child_folder.name}")
            
            # Verify the hierarchy
            assert child_folder.parent == f"folders/{parent_folder_id}"
            
            # List the child folders of the parent
            child_folders = resource_manager_service.list_folders(f"folders/{parent_folder_id}")
            assert len(child_folders) >= 1
            assert any(f.folder_id == child_folder_id for f in child_folders)
            
            # Clean up - delete in reverse order (child first)
            success = resource_manager_service.delete_folder(child_folder_id)
            assert success
            print(f"Deleted child folder: {child_folder.name}")
            
            success = resource_manager_service.delete_folder(parent_folder_id)
            assert success
            print(f"Deleted parent folder: {parent_folder.name}")
            
        except Exception as e:
            # Make sure to attempt cleanup if something goes wrong
            print(f"Error in folder hierarchy test: {e}")
            try:
                if child_folder_id:
                    resource_manager_service.delete_folder(child_folder_id)
                    print(f"Cleaned up child folder after error: {child_folder_id}")
                if parent_folder_id:
                    resource_manager_service.delete_folder(parent_folder_id)
                    print(f"Cleaned up parent folder after error: {parent_folder_id}")
            except Exception as cleanup_error:
                print(f"Failed to clean up folders: {cleanup_error}")
            raise
            
    def test_move_project_between_folders(self, resource_manager_service: ResourceManagerService,
                                        test_project_name: str,
                                        test_folder_name: str,
                                        organization_id: str,
                                        common_tags: Dict[str, str]):
        """Test moving a project between folders."""
        # Skip this test unless specifically enabled - requires admin permissions
        if not os.environ.get("GCPOTO_TEST_CREATE_PROJECT") or not os.environ.get("GCPOTO_TEST_CREATE_FOLDER"):
            pytest.skip("Project move test skipped. Set both GCPOTO_TEST_CREATE_PROJECT=1 and GCPOTO_TEST_CREATE_FOLDER=1 to enable.")
            
        project_id = f"{test_project_name}-move"
        folder1_id = None
        folder2_id = None
        
        try:
            # Create two folders
            folder1 = resource_manager_service.create_folder(
                display_name=f"{test_folder_name}-source",
                parent=f"organizations/{organization_id}",
                tags={**common_tags, "purpose": "source"}
            )
            folder1_id = folder1.folder_id
            print(f"Created source folder: {folder1.name}")
            
            folder2 = resource_manager_service.create_folder(
                display_name=f"{test_folder_name}-destination",
                parent=f"organizations/{organization_id}",
                tags={**common_tags, "purpose": "destination"}
            )
            folder2_id = folder2.folder_id
            print(f"Created destination folder: {folder2.name}")
            
            # Create a project in the first folder
            project = resource_manager_service.create_project(
                project_id=project_id,
                display_name=f"Move Test Project",
                parent=f"folders/{folder1_id}",
                tags={**common_tags, "purpose": "move-test"}
            )
            print(f"Created project in source folder: {project.project_id}")
            
            # Verify initial placement
            assert project.parent == f"folders/{folder1_id}"
            
            # Wait briefly before moving to ensure project is fully created
            time.sleep(10)
            
            # Move the project to the second folder
            moved_project = resource_manager_service.move_project(
                project_id=project_id,
                new_parent=f"folders/{folder2_id}"
            )
            print(f"Moved project to destination folder")
            
            # Verify the move
            assert moved_project.parent == f"folders/{folder2_id}"
            
            # Wait briefly before cleanup
            time.sleep(5)
            
            # Clean up - delete in proper order
            success = resource_manager_service.delete_project(project_id)
            assert success
            print(f"Deleted project: {project_id}")
            
            success = resource_manager_service.delete_folder(folder1_id)
            assert success
            print(f"Deleted source folder: {folder1.name}")
            
            success = resource_manager_service.delete_folder(folder2_id)
            assert success
            print(f"Deleted destination folder: {folder2.name}")
            
        except Exception as e:
            # Make sure to attempt cleanup if something goes wrong
            print(f"Error in project move test: {e}")
            try:
                # Try to clean up all resources
                resource_manager_service.delete_project(project_id)
                if folder1_id:
                    resource_manager_service.delete_folder(folder1_id)
                if folder2_id:
                    resource_manager_service.delete_folder(folder2_id)
                print("Cleaned up resources after error")
            except Exception as cleanup_error:
                print(f"Failed to clean up resources: {cleanup_error}")
            raise
    
    def test_list_folders_in_organization(self, resource_manager_service: ResourceManagerService,
                                          organization_id: str):
        """Test listing folders in an organization."""
        # List folders in the organization
        folders = resource_manager_service.list_folders(parent=f"organizations/{organization_id}")
        
        # Verify we can get a list without error
        assert isinstance(folders, list)
        assert all(isinstance(f, Folder) for f in folders)
        
        # Print some info for debugging
        print(f"Found {len(folders)} folders in organization {organization_id}")
        for folder in folders[:5]:  # Just print first 5 to avoid too much output
            print(f"- {folder.display_name} ({folder.name})")
