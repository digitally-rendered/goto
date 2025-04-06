"""Base service class for GCP interactions."""

from typing import Dict, List, Any, Optional, Type, Generic, TypeVar
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient import discovery

from gcpoto.models.base import GCPResource

# Type variable for generic resource types
T = TypeVar('T', bound=GCPResource)


class GCPService(Generic[T]):
    """Base service class for interacting with Google Cloud Platform resources."""

    def __init__(
        self,
        project_id: str,
        service_name: str,
        version: str = 'v1',
        credentials_file: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        resource_model: Type[T] = GCPResource,
    ):
        """Initialize the GCP service.
        
        Args:
            project_id: The GCP project ID
            service_name: The name of the GCP service (e.g., 'compute', 'storage')
            version: The API version to use
            credentials_file: Path to service account credentials file
            scopes: Authentication scopes to use
            resource_model: The model class for this resource type
        """
        self.project_id = project_id
        self.service_name = service_name
        self.version = version
        self.credentials_file = credentials_file
        self.scopes = scopes or [f'https://www.googleapis.com/auth/{service_name}']
        self.resource_model = resource_model
        self.service = self._create_service()

    def _create_service(self):
        """Create and return an authenticated service client.
        
        Returns:
            An authenticated Google API client service
        """
        credentials = None
        if self.credentials_file:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.scopes
            )

        return discovery.build(
            self.service_name,
            self.version,
            credentials=credentials
        )

    def list_resources(self, **kwargs) -> List[T]:
        """List resources of this type in the project.
        
        Args:
            **kwargs: Additional parameters to pass to the list request
            
        Returns:
            A list of resource model instances
        """
        # This would be implemented by subclasses for specific resources
        raise NotImplementedError("Subclasses must implement this method")

    def get_resource(self, resource_id: str, **kwargs) -> T:
        """Get a specific resource by its ID.
        
        Args:
            resource_id: The ID of the resource to retrieve
            **kwargs: Additional parameters to pass to the get request
            
        Returns:
            A resource model instance
        """
        # This would be implemented by subclasses for specific resources
        raise NotImplementedError("Subclasses must implement this method")

    def create_resource(self, resource: T, **kwargs) -> T:
        """Create a new resource.
        
        Args:
            resource: The resource model to create
            **kwargs: Additional parameters to pass to the create request
            
        Returns:
            The created resource model instance
        """
        # This would be implemented by subclasses for specific resources
        raise NotImplementedError("Subclasses must implement this method")

    def update_resource(self, resource: T, **kwargs) -> T:
        """Update an existing resource.
        
        Args:
            resource: The resource model to update
            **kwargs: Additional parameters to pass to the update request
            
        Returns:
            The updated resource model instance
        """
        # This would be implemented by subclasses for specific resources
        raise NotImplementedError("Subclasses must implement this method")

    def delete_resource(self, resource_id: str, **kwargs) -> bool:
        """Delete a resource by its ID.
        
        Args:
            resource_id: The ID of the resource to delete
            **kwargs: Additional parameters to pass to the delete request
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        # This would be implemented by subclasses for specific resources
        raise NotImplementedError("Subclasses must implement this method")

    def _process_tags(self, body: Dict[str, Any], tags: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Process tags for a resource API request.
        
        This adds tags to the request body. Different GCP services handle tags differently:
        - Some services use 'tags' field directly
        - Some use 'labels' field
        - Some support both with different semantics
        
        This base implementation merges tags into the existing labels field.
        Service-specific implementations can override this method.
        
        Args:
            body: The request body dictionary
            tags: Optional dictionary of tags to apply
            
        Returns:
            The updated request body dictionary
        """
        if not tags:
            return body
            
        # If there are no labels yet, initialize them
        if 'labels' not in body or body['labels'] is None:
            body['labels'] = {}
            
        # Add tags to labels
        for key, value in tags.items():
            body['labels'][key] = value
            
        return body
        
    def _parse_response(self, response: Dict[str, Any]) -> T:
        """Parse an API response into a resource model.
        
        Args:
            response: The API response dictionary
            
        Returns:
            A resource model instance
        """
        return self.resource_model.from_api_response(response)
