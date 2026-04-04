# GCPoto Resource Manager Service

The Resource Manager Service provides a simplified interface for interacting with Google Cloud Resource Manager, allowing you to create and manage GCP projects and folders.

## Features

- Create, list, get, update, and delete GCP projects
- Create, list, get, update, and delete GCP folders
- Move projects between organizations and folders
- Move folders between organizations and folders
- Undelete recently deleted projects and folders
- Support for tags and labels on projects
- 100% test coverage with extensive integration tests
- Strongly typed models with full JSON schema validation

## Installation

The Resource Manager Service is included with the GCPoto package:

```bash
# Install from source
git clone https://github.com/yourusername/gcpoto.git
cd gcpoto
pip install .

# Or with poetry
poetry install
```

## Required Dependencies

Ensure you have the required dependencies:

```bash
pip install google-cloud-resource-manager
```

Or with Poetry:

```bash
poetry add google-cloud-resource-manager
```

## Initialization

```python
from gcpoto.services.resource_manager import ResourceManagerService

# Initialize with project ID and credentials
rm = ResourceManagerService(
    project_id="my-project-id",
    credentials_file="path/to/credentials.json"
)

# Or use environment credentials
# Make sure GOOGLE_APPLICATION_CREDENTIALS environment variable is set
rm = ResourceManagerService(project_id="my-project-id")
```

## Working with Projects

### List Projects

```python
# List all accessible projects
projects = rm.list_projects()

# List projects in a specific organization
org_projects = rm.list_projects(parent="organizations/12345")

# List projects in a specific folder
folder_projects = rm.list_projects(parent="folders/67890")

# Print project details
for project in projects:
    print(f"Project: {project.project_id}")
    print(f"  Display name: {project.display_name}")
    print(f"  Parent: {project.parent}")
    print(f"  State: {project.state}")
    if project.tags:
        print(f"  Tags: {project.tags}")
```

### Get a Project

```python
# Get details for a specific project
project = rm.get_project("my-project-id")

# Access project properties
print(f"Project {project.project_id}")
print(f"Display name: {project.display_name}")
print(f"Parent: {project.parent}")
print(f"State: {project.state}")
print(f"Created: {project.create_time}")
```

### Create a Project

```python
# Create a project in an organization
project = rm.create_project(
    project_id="my-new-project",  # Must be globally unique
    display_name="My New Project",
    parent="organizations/12345",
    labels={"department": "engineering"},
    tags={"team": "platform", "cost-center": "12345", "environment": "dev"}
)

# Create a project in a folder
project = rm.create_project(
    project_id="another-new-project",
    display_name="Another Project",
    parent="folders/67890",
    tags={"purpose": "testing", "owner": "jane.doe"}
)
```

### Update a Project

```python
# Update a project's display name
project = rm.update_project(
    project_id="my-project-id",
    display_name="Updated Project Name"
)

# Update a project's labels
project = rm.update_project(
    project_id="my-project-id",
    labels={"status": "active", "environment": "production"}
)

# Update a project's labels and tags together
project = rm.update_project(
    project_id="my-project-id",
    labels={"status": "active"},
    tags={"team": "data-science", "criticality": "high"}
)
```

### Delete a Project

```python
# Delete a project (marks for deletion, 30-day grace period)
success = rm.delete_project("my-project-id")
if success:
    print("Project marked for deletion")
```

### Undelete a Project

```python
# Restore a project that was recently deleted
restored_project = rm.undelete_project("my-project-id")
print(f"Restored project: {restored_project.display_name}")
```

### Move a Project

```python
# Move a project to a different folder
moved_project = rm.move_project(
    project_id="my-project-id",
    new_parent="folders/new-folder-id"
)

# Move a project directly under an organization
moved_project = rm.move_project(
    project_id="my-project-id",
    new_parent="organizations/org-id"
)
```

## Working with Folders

### List Folders

```python
# List all accessible folders
folders = rm.list_folders()

# List folders in a specific organization
org_folders = rm.list_folders(parent="organizations/12345")

# List folders in a parent folder
subfolders = rm.list_folders(parent="folders/67890")

# Print folder details
for folder in folders:
    print(f"Folder: {folder.name}")
    print(f"  Display name: {folder.display_name}")
    print(f"  Parent: {folder.parent}")
```

### Get a Folder

```python
# Get details for a specific folder
folder = rm.get_folder("folder-id")

# Access folder properties
print(f"Folder {folder.folder_id}")
print(f"Display name: {folder.display_name}")
print(f"Parent: {folder.parent}")
print(f"State: {folder.state}")
print(f"Created: {folder.create_time}")
```

### Create a Folder

```python
# Create a folder in an organization
folder = rm.create_folder(
    display_name="My New Folder",
    parent="organizations/12345"
)

# Create a subfolder
subfolder = rm.create_folder(
    display_name="My Subfolder",
    parent=f"folders/{folder.folder_id}"
)
```

### Update a Folder

```python
# Update a folder's display name
folder = rm.update_folder(
    folder_id="folder-id",
    display_name="Updated Folder Name"
)
```

### Delete a Folder

```python
# Delete a folder (must be empty)
success = rm.delete_folder("folder-id")
if success:
    print("Folder deleted successfully")
```

### Undelete a Folder

```python
# Restore a folder that was recently deleted
restored_folder = rm.undelete_folder("folder-id")
print(f"Restored folder: {restored_folder.display_name}")
```

### Move a Folder

```python
# Move a folder to a different parent folder
moved_folder = rm.move_folder(
    folder_id="folder-id",
    new_parent="folders/new-parent-id"
)

# Move a folder directly under an organization
moved_folder = rm.move_folder(
    folder_id="folder-id",
    new_parent="organizations/org-id"
)
```

## Base Service Methods

The ResourceManagerService implements the base GCPService methods for consistent API usage:

```python
# List projects using the base method
projects = rm.list_resources()

# Get a project using the base method
project = rm.get_resource("my-project-id")

# Create a project using the base method
from gcpoto.models.resource_manager import Project

new_project = Project(
    project_id="my-new-project",
    display_name="My New Project",
    parent="organizations/12345",
    tags={"team": "platform"}
)
project = rm.create_resource(new_project)

# Update a project using the base method
project.display_name = "Updated Project"
updated = rm.update_resource(project)

# Delete a project using the base method
rm.delete_resource("my-project-id")
```

## CLI Usage

GCPoto provides a command-line interface for common Resource Manager operations:

```bash
# List projects
gcpoto --project=my-project-id resource-manager list-projects

# Get a project
gcpoto --project=my-project-id resource-manager get-project my-project-id

# List folders in an organization
gcpoto --project=my-project-id resource-manager list-folders --parent=organizations/12345

# Create a project (requires org admin permissions)
gcpoto --project=my-project-id resource-manager create-project new-project-id "My New Project" --parent=organizations/12345 --tag="team=platform" --tag="env=dev"

# Create a folder
gcpoto --project=my-project-id resource-manager create-folder "My New Folder" --parent=organizations/12345

# Delete a project
gcpoto --project=my-project-id resource-manager delete-project project-id
```

## Permissions and Required Roles

Different operations require different levels of permissions:

- **Listing and viewing projects**: Requires the `resourcemanager.projects.get` and `resourcemanager.projects.list` permissions
- **Creating projects**: Requires `resourcemanager.projects.create` on the organization
- **Deleting projects**: Requires `resourcemanager.projects.delete`
- **Moving projects**: Requires `resourcemanager.projects.update` on the project and `resourcemanager.folders.update` on the destination

Common roles that include these permissions:
- `roles/browser` - For viewing projects and folders
- `roles/resourcemanager.projectCreator` - For creating projects
- `roles/resourcemanager.folderAdmin` - For managing folders
- `roles/resourcemanager.projectDeleter` - For deleting projects
- `roles/owner` - Full access to a specific project

## Error Handling

The Resource Manager service provides meaningful error messages for common issues:

```python
try:
    # Try to create a project with a duplicate ID
    rm.create_project("existing-project-id", "Duplicate Project")
except Exception as e:
    print(f"Error: {e}")  # Will print a descriptive error

try:
    # Try to delete a non-empty folder
    rm.delete_folder("non-empty-folder-id")
except Exception as e:
    print(f"Error: {e}")  # Will inform that the folder must be empty
```

## Testing

All Resource Manager functionality is fully tested with both unit and integration tests.

To run the unit tests:

```bash
pytest tests/unit/test_resource_manager*.py -v
```

To run the integration tests (requires GCP credentials):

```bash
# Set required environment variables
export GCPOTO_TEST_PROJECT_ID="your-test-project-id"
export GCPOTO_RUN_INTEGRATION_TESTS="1"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# To enable tests that create actual resources (requires admin permissions)
export GCPOTO_CREATE_RESOURCES="1"
export GCPOTO_TEST_ORG_ID="your-org-id"

# Then run the tests
pytest tests/integration/test_resource_manager_integration.py -v
```
