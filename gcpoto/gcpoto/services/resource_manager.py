"""Service for interacting with Google Cloud Platform Resource Manager."""

import time
from typing import Dict, List, Optional, Any, Union

from google.cloud import resourcemanager_v3
from google.iam.v1 import iam_policy_pb2, policy_pb2
from google.longrunning import operations_pb2

from gcpoto.models.resource_manager import Project, Folder
from gcpoto.services.base import GCPService


class ResourceManagerService(GCPService):
    """Service for managing GCP Resource Manager resources (projects, folders)."""

    def __init__(self, project_id: Optional[str] = None, credentials_file: Optional[str] = None):
        """Initialize the Resource Manager service.
        
        Args:
            project_id: The GCP project ID.
            credentials_file: Path to credentials file. If not provided, will use the
                default credentials from the environment.
        """
        # Don't use the base class discovery mechanism as resource manager API doesn't work well with it
        # Instead just store the parameters we need directly
        self.project_id = project_id
        self.credentials_file = credentials_file
        self.service_name = "cloudresourcemanager"
        self.version = "v3"
        
        # Set up credentials for the clients
        self.credentials = self._get_credentials()
        self.projects_client = resourcemanager_v3.ProjectsClient(credentials=self.credentials)
        self.folders_client = resourcemanager_v3.FoldersClient(credentials=self.credentials)
    
    def _get_credentials(self):
        """Get credentials for API requests.
        
        Returns:
            google.auth.credentials.Credentials: The credentials to use for API requests.
        """
        if self.credentials_file:
            from google.oauth2 import service_account
            return service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        else:
            # Use application default credentials
            from google.auth import default
            credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            return credentials
    
    def list_projects(self, parent: Optional[str] = None) -> List[Project]:
        """List all accessible projects.
        
        Args:
            parent: Optional parent resource name (organization or folder)
                    in the format 'organizations/{org_id}' or 'folders/{folder_id}'.
        
        Returns:
            List[Project]: List of Project objects.
        """
        request = resourcemanager_v3.ListProjectsRequest()
        if parent:
            request.parent = parent
            
        projects = []
        for project in self.projects_client.list_projects(request=request):
            projects.append(Project.from_api_response({
                'name': project.name,
                'projectId': project.project_id,
                'projectNumber': project.project_number,
                'displayName': project.display_name,
                'parent': project.parent,
                'state': resourcemanager_v3.Project.State(project.state).name,
                'createTime': project.create_time,
                'updateTime': project.update_time,
                'deleteTime': project.delete_time,
                'etag': project.etag,
                'labels': dict(project.labels) if project.labels else None
            }))
        
        return projects
    
    def search_projects(self, query: str) -> List[Project]:
        """Search for projects using a filter query.
        
        Args:
            query: Query string to filter projects. Examples:
                  "id:my-project-id" for project ID
                  "state:ACTIVE" for project state
                  "parent:organizations/123" for projects under an org
        
        Returns:
            List[Project]: List of matching Project objects.
        """
        # The resource manager v3 API doesn't have a direct search_projects method,
        # so we'll implement it by listing all projects and filtering client-side
        try:
            all_projects = self.list_projects()
            if not query or not all_projects:
                return all_projects
                
            # Parse the query
            if ":" not in query:
                # If no specific filter given, do partial string match on any field
                return [p for p in all_projects if query.lower() in str(p).lower()]
                
            key, value = query.split(":", 1)
            
            # Handle specific filters
            if key == "id":
                return [p for p in all_projects if value.lower() in p.project_id.lower()]
            elif key == "state":
                return [p for p in all_projects if p.state == value]
            elif key == "parent":
                return [p for p in all_projects if p.parent == value]
            elif key == "displayName" or key == "display_name":
                return [p for p in all_projects if p.display_name and value.lower() in p.display_name.lower()]
            else:
                # For any other field, attempt to do a partial string match
                return [p for p in all_projects if hasattr(p, key) and value.lower() in str(getattr(p, key)).lower()]
        except Exception as e:
            # Log the error and return an empty list
            print(f"Error searching projects: {e}")
            return []
            
    def get_project(self, project_id: str) -> Project:
        """Get a project by ID.
        
        Args:
            project_id: The project ID (not the numeric ID).
        
        Returns:
            Project: The requested project.
            
        Raises:
            Exception: If the project does not exist or cannot be accessed.
        """
        try:
            # Format the name if not already formatted
            name = project_id if project_id.startswith('projects/') else f'projects/{project_id}'
            project = self.projects_client.get_project(name=name)
            
            # Convert to our model
            return Project.from_api_response({
                'name': project.name,
                'projectId': project.project_id,
                'projectNumber': project.project_number,
                'displayName': project.display_name,
                'parent': project.parent,
                'state': resourcemanager_v3.Project.State(project.state).name,
                'createTime': project.create_time,
                'updateTime': project.update_time,
                'deleteTime': project.delete_time,
                'etag': project.etag,
                'labels': dict(project.labels) if project.labels else None
            })
        except Exception as e:
            raise Exception(f"Failed to get project: {e}")
    
    def create_project(self, project_id: str, display_name: str, 
                     parent: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                     tags: Optional[Dict[str, str]] = None) -> Project:
        """Create a new GCP project.
        
        Args:
            project_id: The desired project ID (must be globally unique).
            display_name: The user-friendly name for the project.
            parent: The resource name of the parent folder or organization.
                   Format: 'folders/{folder_id}' or 'organizations/{org_id}'.
            labels: Labels to apply to the project.
            tags: Tags to apply to the project (merged into labels).
        
        Returns:
            Project: The newly created project.
            
        Raises:
            Exception: If project creation fails.
        """
        try:
            # Create the project request
            project = resourcemanager_v3.Project()
            project.project_id = project_id
            project.display_name = display_name
            
            if parent:
                project.parent = parent
                
            # Process labels
            if labels:
                for key, value in labels.items():
                    project.labels[key] = value
                    
            # Process tags (merge into labels)
            if tags:
                for key, value in tags.items():
                    project.labels[key] = value
            
            # Create the project
            operation = self.projects_client.create_project(request=resourcemanager_v3.CreateProjectRequest(
                project=project
            ))
            
            # Wait for the operation to complete
            result = self._wait_for_operation(operation)
            
            # Get the created project
            return self.get_project(project_id)
            
        except Exception as e:
            raise Exception(f"Failed to create project: {e}")
    
    def update_project(self, project_id: str, display_name: Optional[str] = None,
                      labels: Optional[Dict[str, str]] = None, 
                      tags: Optional[Dict[str, str]] = None) -> Project:
        """Update a GCP project.
        
        Args:
            project_id: The project ID to update.
            display_name: New display name for the project.
            labels: New labels for the project.
            tags: New tags for the project (merged into labels).
        
        Returns:
            Project: The updated project.
            
        Raises:
            Exception: If project update fails.
        """
        try:
            # Get the current project
            name = project_id if project_id.startswith('projects/') else f'projects/{project_id}'
            current_project = self.projects_client.get_project(name=name)
            
            # Create update mask
            update_mask = []
            
            # Update display name if provided
            if display_name is not None:
                current_project.display_name = display_name
                update_mask.append('display_name')
            
            # Update labels if provided
            if labels is not None:
                current_project.labels.clear()
                for key, value in labels.items():
                    current_project.labels[key] = value
                update_mask.append('labels')
                
            # Process tags if provided (merge into labels)
            if tags is not None and update_mask:
                for key, value in tags.items():
                    current_project.labels[key] = value
                # Labels are already in update_mask from above
            
            # Update the project if there are changes
            if update_mask:
                operation = self.projects_client.update_project(
                    request=resourcemanager_v3.UpdateProjectRequest(
                        project=current_project,
                        update_mask=','.join(update_mask)
                    )
                )
                
                # Wait for the operation to complete
                result = self._wait_for_operation(operation)
            
            # Return the updated project
            return self.get_project(project_id)
            
        except Exception as e:
            raise Exception(f"Failed to update project: {e}")
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a GCP project.
        
        This marks the project for deletion, which is finalized after a grace period
        (typically 30 days). During this period, the project can be restored.
        
        Args:
            project_id: The project ID to delete.
        
        Returns:
            bool: True if delete request was successful.
            
        Raises:
            Exception: If project deletion fails.
        """
        try:
            # Format the name if not already formatted
            name = project_id if project_id.startswith('projects/') else f'projects/{project_id}'
            
            # Delete the project
            operation = self.projects_client.delete_project(name=name)
            
            # Wait for the operation to complete
            result = self._wait_for_operation(operation)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to delete project: {e}")
    
    def undelete_project(self, project_id: str) -> Project:
        """Undelete a GCP project that was recently deleted.
        
        Args:
            project_id: The project ID to undelete.
        
        Returns:
            Project: The undeleted project.
            
        Raises:
            Exception: If project undeletion fails.
        """
        try:
            # Format the name if not already formatted
            name = project_id if project_id.startswith('projects/') else f'projects/{project_id}'
            
            # Undelete the project
            operation = self.projects_client.undelete_project(name=name)
            
            # Wait for the operation to complete
            result = self._wait_for_operation(operation)
            
            # Get the undeleted project
            return self.get_project(project_id)
            
        except Exception as e:
            raise Exception(f"Failed to undelete project: {e}")
    
    def list_folders(self, parent: Optional[str] = None) -> List[Folder]:
        """List folders under a parent resource.
        
        Args:
            parent: Parent resource name (organization, folder, or project).
                   Format: 'organizations/{org_id}', 'folders/{folder_id}', or 'projects/{project_id}'.
                   If not provided, lists all accessible folders.
        
        Returns:
            List[Folder]: List of Folder objects.
        """
        request = resourcemanager_v3.ListFoldersRequest()
        if parent:
            request.parent = parent
            
        folders = []
        for folder in self.folders_client.list_folders(request=request):
            # Convert to our model
            folders.append(Folder.from_api_response({
                'name': folder.name,
                'displayName': folder.display_name,
                'parent': folder.parent,
                'state': resourcemanager_v3.Folder.State(folder.state).name,
                'createTime': folder.create_time,
                'updateTime': folder.update_time,
                'deleteTime': folder.delete_time,
                'etag': folder.etag
            }))
        
        return folders
    
    def get_folder(self, folder_id: str) -> Folder:
        """Get a folder by ID.
        
        Args:
            folder_id: The folder ID.
        
        Returns:
            Folder: The requested folder.
            
        Raises:
            Exception: If the folder does not exist or cannot be accessed.
        """
        try:
            # Format the name if not already formatted
            name = folder_id if folder_id.startswith('folders/') else f'folders/{folder_id}'
            folder = self.folders_client.get_folder(name=name)
            
            # Convert to our model
            return Folder.from_api_response({
                'name': folder.name,
                'displayName': folder.display_name,
                'parent': folder.parent,
                'state': resourcemanager_v3.Folder.State(folder.state).name,
                'createTime': folder.create_time,
                'updateTime': folder.update_time,
                'deleteTime': folder.delete_time,
                'etag': folder.etag
            })
        except Exception as e:
            raise Exception(f"Failed to get folder: {e}")
    
    def create_folder(self, display_name: str, parent: str, 
                     tags: Optional[Dict[str, str]] = None) -> Folder:
        """Create a new folder under a parent resource.
        
        Args:
            display_name: The user-friendly name for the folder.
            parent: The resource name of the parent folder or organization.
                   Format: 'folders/{folder_id}' or 'organizations/{org_id}'.
            tags: Tags to apply to the folder (for future use, currently not supported by GCP).
        
        Returns:
            Folder: The newly created folder.
            
        Raises:
            Exception: If folder creation fails.
        """
        try:
            # Create the folder request
            folder = resourcemanager_v3.Folder()
            folder.display_name = display_name
            folder.parent = parent
            
            # Create the folder
            operation = self.folders_client.create_folder(request=resourcemanager_v3.CreateFolderRequest(
                folder=folder,
                parent=parent
            ))
            
            # Wait for the operation to complete
            result = self._wait_for_operation(operation)
            
            # Parse the response to get the folder ID
            folder_id = result.name.split('/')[-1] if result and hasattr(result, 'name') else ''
            
            # Get the created folder
            return self.get_folder(folder_id)
            
        except Exception as e:
            raise Exception(f"Failed to create folder: {e}")
    
    def update_folder(self, folder_id: str, display_name: str) -> Folder:
        """Update a folder's display name.
        
        Args:
            folder_id: The folder ID to update.
            display_name: New display name for the folder.
        
        Returns:
            Folder: The updated folder.
            
        Raises:
            Exception: If folder update fails.
        """
        try:
            # Get the current folder
            name = folder_id if folder_id.startswith('folders/') else f'folders/{folder_id}'
            folder = self.folders_client.get_folder(name=name)
            
            # Update display name
            folder.display_name = display_name
            
            # Update the folder
            operation = self.folders_client.update_folder(
                request=resourcemanager_v3.UpdateFolderRequest(
                    folder=folder,
                    update_mask='display_name'
                )
            )
            
            # Wait for the operation to complete
            result = self._wait_for_operation(operation)
            
            # Return the updated folder
            return self.get_folder(folder_id)
            
        except Exception as e:
            raise Exception(f"Failed to update folder: {e}")
    
    def delete_folder(self, folder_id: str) -> bool:
        """Delete a folder.
        
        The folder must be empty (no projects or subfolders).
        
        Args:
            folder_id: The folder ID to delete.
        
        Returns:
            bool: True if delete request was successful.
            
        Raises:
            Exception: If folder deletion fails.
        """
        try:
            # Format the name if not already formatted
            name = folder_id if folder_id.startswith('folders/') else f'folders/{folder_id}'
            
            # Delete the folder
            operation = self.folders_client.delete_folder(name=name)
            
            # Wait for the operation to complete
            result = self._wait_for_operation(operation)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to delete folder: {e}")
    
    def undelete_folder(self, folder_id: str) -> Folder:
        """Undelete a folder that was recently deleted.
        
        Args:
            folder_id: The folder ID to undelete.
        
        Returns:
            Folder: The undeleted folder.
            
        Raises:
            Exception: If folder undeletion fails.
        """
        try:
            # Format the name if not already formatted
            name = folder_id if folder_id.startswith('folders/') else f'folders/{folder_id}'
            
            # Undelete the folder
            operation = self.folders_client.undelete_folder(name=name)
            
            # Wait for the operation to complete
            result = self._wait_for_operation(operation)
            
            # Get the undeleted folder
            return self.get_folder(folder_id)
            
        except Exception as e:
            raise Exception(f"Failed to undelete folder: {e}")
    
    def move_folder(self, folder_id: str, new_parent: str) -> Folder:
        """Move a folder to a new parent.
        
        Args:
            folder_id: The folder ID to move.
            new_parent: The new parent resource name.
                       Format: 'folders/{folder_id}' or 'organizations/{org_id}'.
        
        Returns:
            Folder: The moved folder.
            
        Raises:
            Exception: If folder move fails.
        """
        try:
            # Format the name if not already formatted
            name = folder_id if folder_id.startswith('folders/') else f'folders/{folder_id}'
            
            # Move the folder
            operation = self.folders_client.move_folder(
                request=resourcemanager_v3.MoveFolderRequest(
                    name=name,
                    destination_parent=new_parent
                )
            )
            
            # Wait for the operation to complete
            result = self._wait_for_operation(operation)
            
            # Get the moved folder
            return self.get_folder(folder_id)
            
        except Exception as e:
            raise Exception(f"Failed to move folder: {e}")
    
    def move_project(self, project_id: str, new_parent: str) -> Project:
        """Move a project to a new parent folder or organization.
        
        Args:
            project_id: The project ID to move.
            new_parent: The new parent resource name.
                       Format: 'folders/{folder_id}' or 'organizations/{org_id}'.
        
        Returns:
            Project: The moved project.
            
        Raises:
            Exception: If project move fails.
        """
        try:
            # Format the name if not already formatted
            name = project_id if project_id.startswith('projects/') else f'projects/{project_id}'
            
            # Move the project
            operation = self.projects_client.move_project(
                request=resourcemanager_v3.MoveProjectRequest(
                    name=name,
                    destination_parent=new_parent
                )
            )
            
            # Wait for the operation to complete
            result = self._wait_for_operation(operation)
            
            # Get the moved project
            return self.get_project(project_id)
            
        except Exception as e:
            raise Exception(f"Failed to move project: {e}")
    
    def _wait_for_operation(self, operation: operations_pb2.Operation) -> Any:
        """Wait for a long-running operation to complete.
        
        Args:
            operation: The operation to wait for.
            
        Returns:
            Any: The operation result.
            
        Raises:
            Exception: If the operation fails or times out.
        """
        operation_name = operation.name
        done = False
        timeout = 300  # 5 minutes timeout
        start_time = time.time()
        
        while not done:
            if time.time() - start_time > timeout:
                raise Exception(f"Operation {operation_name} timed out after {timeout} seconds")
            
            # Check operation status
            operation = self.projects_client.transport.operations_client.get_operation(name=operation_name)
            
            if operation.done:
                if operation.HasField('error'):
                    raise Exception(f"Operation {operation_name} failed: {operation.error.message}")
                else:
                    # Operation completed successfully
                    if operation.HasField('response'):
                        return operation.response
                    return None
            
            # Wait before checking again
            time.sleep(2)
    
    def list_resources(self, filter_str: Optional[str] = None) -> List[Project]:
        """Implementation of base class method to list resources (projects).
        
        Args:
            filter_str: Optional filter string (not used in Resource Manager).
            
        Returns:
            List[Project]: List of projects.
        """
        return self.list_projects()
    
    def get_resource(self, resource_id: str) -> Project:
        """Implementation of base class method to get a resource (project).
        
        Args:
            resource_id: The project ID.
            
        Returns:
            Project: The requested project.
        """
        return self.get_project(resource_id)
    
    def create_resource(self, resource: Project) -> Project:
        """Implementation of base class method to create a resource (project).
        
        Args:
            resource: The project to create.
            
        Returns:
            Project: The created project.
        """
        return self.create_project(
            project_id=resource.project_id,
            display_name=resource.display_name,
            parent=resource.parent,
            labels=resource.labels,
            tags=resource.tags
        )
    
    def update_resource(self, resource: Project) -> Project:
        """Implementation of base class method to update a resource (project).
        
        Args:
            resource: The project to update.
            
        Returns:
            Project: The updated project.
        """
        return self.update_project(
            project_id=resource.project_id,
            display_name=resource.display_name,
            labels=resource.labels,
            tags=resource.tags
        )
    
    def delete_resource(self, resource_id: str) -> bool:
        """Implementation of base class method to delete a resource (project).
        
        Args:
            resource_id: The project ID.
            
        Returns:
            bool: True if delete was successful.
        """
        return self.delete_project(resource_id)
