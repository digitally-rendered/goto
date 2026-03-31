"""Service implementation for Google Cloud Storage."""

import os
import io
from typing import List, Optional, Dict, Any, Union, BinaryIO, cast

from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

from gcpoto.services.base import GCPService
from gcpoto.models.base import GCPResource
from gcpoto.models.storage_object import StorageObject


class StorageBucket(GCPResource):
    """Model for a Google Cloud Storage bucket."""

    location: str
    storage_class: str
    _tags: Optional[Dict[str, str]] = None

    # Instead of a property, implement a getter method that tests can call
    def get_tag(self, key: str, default: Any = None) -> Any:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        # First check explicit tags, then fall back to labels
        if self._tags and key in self._tags:
            return self._tags[key]
        elif self.labels and key in self.labels:
            return self.labels[key]
        else:
            return default

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "StorageBucket":
        """Create a bucket from API response.

        Args:
            response: The API response dictionary

        Returns:
            A new StorageBucket instance
        """
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="storage.bucket",
            project=response.get("projectNumber", ""),
            location=response.get("location", ""),
            storage_class=response.get("storageClass", ""),
            labels=response.get("labels", {}),
            created=response.get("timeCreated"),
            updated=response.get("updated"),
        )

        # Initialize _tags from metadata if present
        if response.get("metadata"):
            instance._tags = response["metadata"]

        return instance


class StorageService(GCPService[StorageBucket]):
    """Service for interacting with Google Cloud Storage."""

    def list_objects(
        self, bucket_name: str, prefix: Optional[str] = None, **kwargs
    ) -> List[StorageObject]:
        """List objects in a bucket.

        Args:
            bucket_name: The name of the bucket to list objects from
            prefix: Optional prefix to filter objects by
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of StorageObject instances
        """
        params = {"bucket": bucket_name}

        if prefix:
            params["prefix"] = prefix

        if kwargs:
            params.update(kwargs)

        request = self.service.objects().list(**params)
        objects = []

        # Handle pagination automatically
        while request is not None:
            response = self._execute(request)

            for item in response.get("items", []):
                # Add bucket name to each object since it's not always included
                item["bucket"] = bucket_name
                objects.append(StorageObject.from_api_response(item))

            # Get the next page of results
            request = self.service.objects().list_next(request, response)

        return objects

    def create_bucket(
        self,
        bucket_name: str,
        location: str = "us",
        storage_class: str = "STANDARD",
        labels: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> StorageBucket:
        """Create a new storage bucket.

        Args:
            bucket_name: Name for the new bucket (must be globally unique)
            location: Geographic location for the bucket (default: 'us')
            storage_class: Storage class (default: 'STANDARD')
            labels: Optional labels to apply to the bucket
            **kwargs: Additional parameters to pass to the API

        Returns:
            The newly created StorageBucket
        """
        # Prepare the request body
        body = {
            "name": bucket_name,
            "location": location,
            "storageClass": storage_class,
        }

        # Add labels if provided
        if labels:
            body["labels"] = labels

        # Add tags as labels if provided (for compatibility with tests)
        if tags:
            if "labels" not in body:
                body["labels"] = {}
            # Merge tags into labels
            body["labels"].update(tags)

        # Add any additional parameters
        if kwargs:
            body.update(kwargs)

        request = self.service.buckets().insert(project=self.project_id, body=body)
        response = self._execute(request)

        return StorageBucket.from_api_response(response)

    def upload(
        self,
        bucket_name: str,
        source_file: Optional[str] = None,
        file_path: Optional[str] = None,
        destination_blob_name: Optional[str] = None,
        object_name: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> StorageObject:
        """Upload a file to a bucket.

        Args:
            file_path: Path to the file to upload
            bucket_name: Name of the bucket to upload to
            object_name: Name to give the uploaded object (default: filename)
            content_type: Content type of the file (default: auto-detect)
            metadata: Optional metadata to attach to the object
            **kwargs: Additional parameters to pass to the API

        Returns:
            The StorageObject representing the uploaded file
        """
        # Handle different parameter name combinations for compatibility
        actual_file_path = source_file or file_path
        if not actual_file_path:
            raise ValueError("Either source_file or file_path must be provided")

        # Use the appropriate object name parameter
        actual_object_name = destination_blob_name or object_name
        if not actual_object_name:
            actual_object_name = os.path.basename(actual_file_path)

        # Determine content type if not provided
        if not content_type:
            import mimetypes

            # Only guess from file_path if it's available
            if file_path:
                content_type, _ = mimetypes.guess_type(file_path)
            # If we couldn't determine a content type, use a default
            if not content_type:
                content_type = "application/octet-stream"

        # Prepare media body and metadata
        with open(actual_file_path, "rb") as f:
            file_content = f.read()

        # Build the media upload request
        media = MediaIoBaseUpload(
            io.BytesIO(file_content), mimetype=content_type, resumable=True
        )

        # Prepare the object metadata
        body = {
            "name": actual_object_name,
            "contentType": content_type,
        }

        # Add tags to metadata if provided
        if tags:
            if not metadata:
                metadata = {}
            # Convert tags to metadata format
            for key, value in tags.items():
                metadata[key] = value

        # Add custom metadata if provided
        if metadata:
            body["metadata"] = metadata

        # Add any additional parameters
        if kwargs:
            body.update(kwargs)

        # Execute the upload
        request = self.service.objects().insert(
            bucket=bucket_name, body=body, media_body=media
        )
        response = self._execute(request)

        # Add bucket name if not included
        if "bucket" not in response:
            response["bucket"] = bucket_name

        return StorageObject.from_api_response(response)

    def download(
        self, bucket_name: str, object_name: str, destination_file: str, **kwargs
    ) -> None:
        """Download an object from a bucket to a local file.

        Args:
            bucket_name: The name of the bucket containing the object
            object_name: The name of the object to download
            destination_file: Path where the downloaded file will be saved
            **kwargs: Additional parameters to pass to the API

        Returns:
            None
        """
        request = self.service.objects().get_media(
            bucket=bucket_name, object=object_name, **kwargs
        )

        # Stream the download to the destination file
        with open(destination_file, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

    def delete_bucket(self, bucket_name: str, **kwargs) -> None:
        """Delete a bucket.

        Args:
            bucket_name: Name of the bucket to delete
            **kwargs: Additional parameters to pass to the API

        Returns:
            None
        """
        # First ensure the bucket is empty
        objects = self.list_objects(bucket_name=bucket_name)
        if objects:
            print(
                f"Warning: Bucket {bucket_name} is not empty. Deleting {len(objects)} objects first."
            )
            for obj in objects:
                self.delete_object(bucket_name=bucket_name, object_name=obj.name)

        request = self.service.buckets().delete(bucket=bucket_name, **kwargs)
        self._execute(request)

    def get_object(self, bucket_name: str, object_name: str, **kwargs) -> StorageObject:
        """Get a specific object by name.

        Args:
            bucket_name: The name of the bucket containing the object
            object_name: The name of the object to retrieve
            **kwargs: Additional parameters to pass to the get request

        Returns:
            A StorageObject instance
        """
        params = {"bucket": bucket_name, "object": object_name}

        if kwargs:
            params.update(kwargs)

        request = self.service.objects().get(**params)
        response = self._execute(request)

        # Add bucket name if not included
        if "bucket" not in response:
            response["bucket"] = bucket_name

        # Add bucket name to response if not present
        if "bucket" not in response:
            response["bucket"] = bucket_name

        return StorageObject.from_api_response(response)

    def download_object(
        self,
        bucket_name: str,
        object_name: str,
        destination: Optional[Union[str, BinaryIO]] = None,
        **kwargs,
    ) -> Union[bytes, str]:
        """Download an object from a bucket.

        Args:
            bucket_name: The name of the bucket containing the object
            object_name: The name of the object to download
            destination: Optional file path or file-like object to write the content to
            **kwargs: Additional parameters to pass to the get_media request

        Returns:
            The object content as bytes if no destination is provided,
            or the destination path as a string if a path was provided
        """
        params = {"bucket": bucket_name, "object": object_name}

        if kwargs:
            params.update(kwargs)

        request = self.service.objects().get_media(**params)

        # Create a bytes buffer to store the content
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        # Reset buffer position for reading
        buffer.seek(0)

        if destination is None:
            # Return the bytes directly
            return buffer.read()
        elif isinstance(destination, str):
            # Write to the specified file path
            os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
            with open(destination, "wb") as f:
                f.write(buffer.read())
            return destination
        else:
            # Write to the provided file-like object
            cast(BinaryIO, destination).write(buffer.read())
            return destination

    def upload_object(
        self,
        bucket_name: str,
        object_name: str,
        content: Union[bytes, str, BinaryIO],
        content_type: Optional[str] = None,
        **kwargs,
    ) -> StorageObject:
        """Upload an object to a bucket.

        Args:
            bucket_name: The name of the bucket to upload to
            object_name: The name of the object to create
            content: The content to upload (bytes, string, or file-like object)
            content_type: The content type of the object
            **kwargs: Additional parameters to pass to the insert request

        Returns:
            A StorageObject instance representing the uploaded object
        """
        from googleapiclient.http import MediaInMemoryUpload, MediaFileUpload

        # Create the base object metadata
        body = {"name": object_name}

        if content_type:
            body["contentType"] = content_type

        # Add any additional metadata from kwargs
        for key, value in kwargs.items():
            if key not in ["media_body", "bucket", "media"]:
                body[key] = value

        # Prepare the media content for upload
        if isinstance(content, bytes):
            media = MediaInMemoryUpload(
                content, mimetype=content_type or "application/octet-stream"
            )
        elif isinstance(content, str):
            # Check if it's a file path or a string content
            if os.path.isfile(content):
                media = MediaFileUpload(content, mimetype=content_type)
            else:
                # It's string content
                media = MediaInMemoryUpload(
                    content.encode("utf-8"), mimetype=content_type or "text/plain"
                )
        else:
            # It's a file-like object
            content_bytes = content.read()
            if isinstance(content_bytes, str):
                content_bytes = content_bytes.encode("utf-8")
            media = MediaInMemoryUpload(
                content_bytes, mimetype=content_type or "application/octet-stream"
            )

        request = self.service.objects().insert(
            bucket=bucket_name, body=body, media_body=media
        )
        response = self._execute(request)

        # Add bucket name to response if not present
        if "bucket" not in response:
            response["bucket"] = bucket_name

        return StorageObject.from_api_response(response)

    def delete_object(self, bucket_name: str, object_name: str, **kwargs) -> bool:
        """Delete an object from a bucket.

        Args:
            bucket_name: The name of the bucket containing the object
            object_name: The name of the object to delete
            **kwargs: Additional parameters to pass to the delete request

        Returns:
            True if the deletion was successful
        """
        params = {"bucket": bucket_name, "object": object_name}

        if kwargs:
            params.update(kwargs)

        request = self.service.objects().delete(**params)
        self._execute(request)

        return True

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the storage service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="storage",
            version="v1",
            credentials_file=credentials_file,
            resource_model=StorageBucket,
        )

    def list_resources(self, **kwargs) -> List[StorageBucket]:
        """List storage buckets in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of StorageBucket instances
        """
        request = self.service.buckets().list(project=self.project_id, **kwargs)
        response = self._execute(request)

        buckets = []
        for item in response.get("items", []):
            buckets.append(self._parse_response(item))

        return buckets

    def get_resource(self, resource_id: str, **kwargs) -> StorageBucket:
        """Get a specific bucket by name.

        Args:
            resource_id: The name of the bucket to retrieve
            **kwargs: Additional parameters to pass to the get request

        Returns:
            A StorageBucket instance
        """
        request = self.service.buckets().get(bucket=resource_id, **kwargs)
        response = self._execute(request)

        return self._parse_response(response)

    def create_resource(self, resource: StorageBucket, **kwargs) -> StorageBucket:
        """Create a new storage bucket.

        Args:
            resource: The bucket model to create
            **kwargs: Additional parameters to pass to the create request

        Returns:
            The created StorageBucket instance
        """
        body = {
            "name": resource.name,
            "location": resource.location,
            "storageClass": resource.storage_class,
        }

        if resource.labels:
            body["labels"] = resource.labels

        request = self.service.buckets().insert(
            project=self.project_id, body=body, **kwargs
        )
        response = self._execute(request)

        return self._parse_response(response)

    def delete_resource(self, resource_id: str, **kwargs) -> bool:
        """Delete a bucket by name.

        Args:
            resource_id: The name of the bucket to delete
            **kwargs: Additional parameters to pass to the delete request

        Returns:
            True if the deletion was successful
        """
        request = self.service.buckets().delete(bucket=resource_id, **kwargs)
        self._execute(request)

        return True
