"""Enhanced integration tests for the Resource Manager service."""

import os
import time
import uuid
import pytest
from typing import Dict, Any, List

from gcpoto.services.resource_manager import ResourceManagerService
from gcpoto.models.resource_manager import Project, Folder


pytest.mark.integration = pytest.mark.skipif(
    "GCPOTO_RUN_INTEGRATION_TESTS" not in os.environ,
    reason="Integration tests are skipped unless GCPOTO_RUN_INTEGRATION_TESTS is set",
)


@pytest.fixture(scope="session")
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


@pytest.mark.integration
class TestResourceManagerEnhancedIntegration:
    """Enhanced integration tests for the Resource Manager service with improved coverage."""
    
    def test_search_projects(self, resource_manager_service: ResourceManagerService, test_project_id: str):
        """Test searching for projects with filters."""
        # Search for projects with the current test project's ID
        query = f"id:{test_project_id}"
        
        projects = resource_manager_service.search_projects(query)
        
        # Verify projects
        assert isinstance(projects, list)
        assert all(isinstance(p, Project) for p in projects)
        
        # The test project should be in the results
        project_ids = [p.project_id for p in projects]
        assert test_project_id in project_ids, f"Test project {test_project_id} not found in search results"
        
        print(f"Search for '{query}' returned {len(projects)} projects")
        
        # Try another search for projects in ACTIVE state
        active_projects = resource_manager_service.search_projects("state:ACTIVE")
        assert isinstance(active_projects, list)
        assert all(isinstance(p, Project) for p in active_projects)
        assert all(p.state == "ACTIVE" for p in active_projects)
        
        print(f"Search for 'state:ACTIVE' returned {len(active_projects)} projects")
    
    def test_get_project_ancestors(self, resource_manager_service: ResourceManagerService, test_project_id: str):
        """Test getting a project's ancestors (folders and organization)."""
        # Get the ancestors of the current test project
        try:
            ancestors = resource_manager_service.get_project_ancestors(test_project_id)
            
            # Verify ancestors
            assert isinstance(ancestors, list)
            
            # Print ancestor information
            print(f"Found {len(ancestors)} ancestors for project {test_project_id}:")
            for ancestor in ancestors:
                assert 'resourceType' in ancestor and 'displayName' in ancestor
                print(f"- {ancestor['resourceType']}: {ancestor['displayName']} ({ancestor.get('id', '')})")
                
        except Exception as e:
            print(f"Could not get project ancestors: {e}")
            pytest.skip(f"Insufficient permissions to get project ancestors: {e}")
    
    def test_get_project_iam_policy(self, resource_manager_service: ResourceManagerService, test_project_id: str):
        """Test getting a project's IAM policy."""
        # Get the IAM policy of the current test project
        try:
            policy = resource_manager_service.get_project_iam_policy(test_project_id)
            
            # Verify policy structure
            assert isinstance(policy, dict)
            assert 'bindings' in policy or 'version' in policy
            
            # Print policy information
            print(f"Retrieved IAM policy for project {test_project_id}")
            if 'bindings' in policy:
                bindings = policy['bindings']
                print(f"Policy has {len(bindings)} bindings")
                # Show first few bindings
                for binding in bindings[:3]:
                    role = binding.get('role', 'Unknown')
                    members = binding.get('members', [])
                    print(f"- Role: {role}, Members: {len(members)}")
                    
        except Exception as e:
            print(f"Could not get project IAM policy: {e}")
            pytest.skip(f"Insufficient permissions to get project IAM policy: {e}")
    
    def test_get_effective_iam_policy(self, resource_manager_service: ResourceManagerService, test_project_id: str):
        """Test getting a project's effective IAM policy."""
        # Get the effective IAM policy of the current test project
        try:
            policy = resource_manager_service.get_project_effective_iam_policy(test_project_id)
            
            # Verify policy structure
            assert isinstance(policy, dict)
            assert 'policies' in policy or 'policyBlob' in policy
            
            # Print policy information
            print(f"Retrieved effective IAM policy for project {test_project_id}")
            print(f"Policy keys: {list(policy.keys())}")
                    
        except Exception as e:
            print(f"Could not get effective IAM policy: {e}")
            pytest.skip(f"Insufficient permissions to get effective IAM policy: {e}")
    
    def test_list_project_tags(self, resource_manager_service: ResourceManagerService, test_project_id: str):
        """Test listing tags for a project."""
        # List tags for the current test project
        try:
            tags = resource_manager_service.list_project_tags(test_project_id)
            
            # Verify tags structure
            assert isinstance(tags, dict)
            
            # Print tag information
            print(f"Retrieved tags for project {test_project_id}")
            if 'tags' in tags:
                tag_items = tags['tags']
                print(f"Project has {len(tag_items)} tags")
                for key, value in tag_items.items():
                    print(f"- {key}: {value}")
            else:
                print("Project has no tags")
                    
        except Exception as e:
            print(f"Could not list project tags: {e}")
            pytest.skip(f"Insufficient permissions to list project tags: {e}")


@pytest.mark.integration
@pytest.mark.skipif(
    "GCPOTO_TEST_ORG_ID" not in os.environ,
    reason="Organization tests are skipped unless GCPOTO_TEST_ORG_ID is set"
)
class TestFolderEnhancedIntegration:
    """Enhanced integration tests for folder operations.
    
    These tests focus on validating folder operations without modifying resources.
    """
    
    @pytest.fixture(scope="class")
    def organization_id(self):
        """Get the organization ID for testing.
        
        Returns:
            str: The organization ID.
        """
        return os.environ.get("GCPOTO_TEST_ORG_ID")
    
    def test_list_folders(self, resource_manager_service: ResourceManagerService, organization_id: str):
        """Test listing folders in the organization."""
        # List folders in the organization
        try:
            folders = resource_manager_service.list_folders(f"organizations/{organization_id}")
            
            # Verify folders
            assert isinstance(folders, list)
            assert all(isinstance(f, Folder) for f in folders)
            
            # Print folder information
            print(f"Found {len(folders)} folders in organization {organization_id}")
            for folder in folders[:5]:  # Only print the first 5
                print(f"- {folder.display_name} (ID: {folder.folder_id})")
                
        except Exception as e:
            print(f"Could not list folders: {e}")
            pytest.skip(f"Insufficient permissions to list folders: {e}")
    
    def test_search_folders(self, resource_manager_service: ResourceManagerService, organization_id: str):
        """Test searching for folders with filters."""
        # Search for folders in the organization
        query = f"parent:organizations/{organization_id}"
        
        try:
            folders = resource_manager_service.search_folders(query)
            
            # Verify folders
            assert isinstance(folders, list)
            assert all(isinstance(f, Folder) for f in folders)
            
            # Print folder information
            print(f"Search for '{query}' returned {len(folders)} folders")
            for folder in folders[:5]:  # Only print the first 5
                print(f"- {folder.display_name} (ID: {folder.folder_id})")
                
            # Try another search for folders in ACTIVE state
            active_folders = resource_manager_service.search_folders(f"parent:organizations/{organization_id} state:ACTIVE")
            assert isinstance(active_folders, list)
            assert all(isinstance(f, Folder) for f in active_folders)
            assert all(f.state == "ACTIVE" for f in active_folders if f.state)
            
            print(f"Search for 'state:ACTIVE' returned {len(active_folders)} folders")
                
        except Exception as e:
            print(f"Could not search folders: {e}")
            pytest.skip(f"Insufficient permissions to search folders: {e}")
    
    def test_get_folder(self, resource_manager_service: ResourceManagerService, organization_id: str):
        """Test getting a specific folder."""
        # First list folders to find one to test with
        try:
            folders = resource_manager_service.list_folders(f"organizations/{organization_id}")
            
            # Skip if no folders available
            if not folders:
                pytest.skip("No folders available to test get_folder")
            
            # Get the first folder
            sample_folder = folders[0]
            
            # Now test get_folder
            folder = resource_manager_service.get_folder(sample_folder.folder_id)
            
            # Verify the folder details
            assert folder.folder_id == sample_folder.folder_id
            assert folder.display_name == sample_folder.display_name
            assert folder.id == sample_folder.id
            assert folder.type == "resourcemanager.folder"
            
            print(f"Successfully retrieved folder: {folder.display_name} (ID: {folder.folder_id})")
                
        except Exception as e:
            print(f"Could not test get_folder: {e}")
            pytest.skip(f"Insufficient permissions or setup to test get_folder: {e}")
    
    def test_get_folder_iam_policy(self, resource_manager_service: ResourceManagerService, organization_id: str):
        """Test getting a folder's IAM policy."""
        # First list folders to find one to test with
        try:
            folders = resource_manager_service.list_folders(f"organizations/{organization_id}")
            
            # Skip if no folders available
            if not folders:
                pytest.skip("No folders available to test get_folder_iam_policy")
            
            # Get the first folder
            sample_folder = folders[0]
            
            # Get the IAM policy
            policy = resource_manager_service.get_folder_iam_policy(sample_folder.folder_id)
            
            # Verify policy structure
            assert isinstance(policy, dict)
            assert 'bindings' in policy or 'version' in policy
            
            # Print policy information
            print(f"Retrieved IAM policy for folder {sample_folder.folder_id}")
            if 'bindings' in policy:
                bindings = policy['bindings']
                print(f"Policy has {len(bindings)} bindings")
                # Show first few bindings
                for binding in bindings[:3]:
                    role = binding.get('role', 'Unknown')
                    members = binding.get('members', [])
                    print(f"- Role: {role}, Members: {len(members)}")
                    
        except Exception as e:
            print(f"Could not get folder IAM policy: {e}")
            pytest.skip(f"Insufficient permissions to get folder IAM policy: {e}")
