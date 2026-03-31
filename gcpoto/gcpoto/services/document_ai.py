"""Service implementation for Google Cloud Document AI."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.document_ai import Processor, ProcessorVersion, ProcessResult

logger = logging.getLogger(__name__)

class DocumentAIService(GCPService[Processor]):
    """Service for interacting with Google Cloud Document AI."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Document AI service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="documentai",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Processor,
            **kwargs,
        )

    def _format_parent(self, location: str) -> str:
        """Format the parent path for Document AI resources.

        Args:
            location: The GCP location/region

        Returns:
            The formatted parent path
        """
        return f"projects/{self.project_id}/locations/{location}"

    def _format_processor_name(
        self, location: str, processor_id: str
    ) -> str:
        """Format the full processor resource name.

        Args:
            location: The GCP location/region
            processor_id: The processor ID or full resource path

        Returns:
            The fully qualified processor resource name
        """
        if "/" in processor_id:
            return processor_id
        return f"projects/{self.project_id}/locations/{location}/processors/{processor_id}"

    # ---- Processor methods ----

    def list_processors(self, location: str, **kwargs) -> List[Processor]:
        """List Document AI processors in a location.

        Args:
            location: The GCP location/region
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of Processor instances
        """
        logger.debug(
            "Listing processors in %s for project %s",
            location,
            self.project_id,
        )

        parent = self._format_parent(location)
        processors = []
        request = (
            self.service.projects()
            .locations()
            .processors()
            .list(parent=parent, **kwargs)
        )

        while request is not None:
            response = self._execute(request)
            for item in response.get("processors", []):
                processors.append(Processor.from_api_response(item))
            request = (
                self.service.projects()
                .locations()
                .processors()
                .list_next(request, response)
            )

        logger.debug("Found %s processors", len(processors))
        return processors

    def get_processor(
        self, location: str, processor_id: str
    ) -> Processor:
        """Get a specific Document AI processor.

        Args:
            location: The GCP location/region
            processor_id: The ID of the processor to retrieve

        Returns:
            A Processor instance
        """
        logger.debug(
            "Getting processor %s in %s for project %s",
            processor_id,
            location,
            self.project_id,
        )

        name = self._format_processor_name(location, processor_id)
        request = (
            self.service.projects()
            .locations()
            .processors()
            .get(name=name)
        )
        response = self._execute(request, "processor", processor_id)
        return Processor.from_api_response(response)
    def create_processor(
        self,
        location: str,
        display_name: str,
        processor_type: str,
    ) -> Processor:
        """Create a new Document AI processor.

        Args:
            location: The GCP location/region
            display_name: The display name of the processor
            processor_type: The type of processor to create

        Returns:
            A Processor instance for the newly created processor
        """
        logger.info(
            "Creating processor %s in %s for project %s",
            display_name,
            location,
            self.project_id,
        )

        parent = self._format_parent(location)
        body: Dict[str, Any] = {
            "displayName": display_name,
            "type": processor_type,
        }

        request = (
            self.service.projects()
            .locations()
            .processors()
            .create(parent=parent, body=body)
        )
        response = self._execute(request)
        return Processor.from_api_response(response)
    def delete_processor(
        self, location: str, processor_id: str
    ) -> bool:
        """Delete a Document AI processor.

        Args:
            location: The GCP location/region
            processor_id: The ID of the processor to delete

        Returns:
            True if the deletion was successful
        """
        logger.info(
            "Deleting processor %s in %s for project %s",
            processor_id,
            location,
            self.project_id,
        )

        name = self._format_processor_name(location, processor_id)
        self.service.projects().locations().processors().delete(
            name=name
        ).execute()
        return True
    def enable_processor(
        self, location: str, processor_id: str
    ) -> Dict[str, Any]:
        """Enable a Document AI processor.

        Args:
            location: The GCP location/region
            processor_id: The ID of the processor to enable

        Returns:
            The operation response
        """
        logger.info(
            "Enabling processor %s in %s for project %s",
            processor_id,
            location,
            self.project_id,
        )

        name = self._format_processor_name(location, processor_id)
        request = (
            self.service.projects()
            .locations()
            .processors()
            .enable(name=name, body={})
        )
        response = self._execute(request, "processor", processor_id)
        return response
    def disable_processor(
        self, location: str, processor_id: str
    ) -> Dict[str, Any]:
        """Disable a Document AI processor.

        Args:
            location: The GCP location/region
            processor_id: The ID of the processor to disable

        Returns:
            The operation response
        """
        logger.info(
            "Disabling processor %s in %s for project %s",
            processor_id,
            location,
            self.project_id,
        )

        name = self._format_processor_name(location, processor_id)
        request = (
            self.service.projects()
            .locations()
            .processors()
            .disable(name=name, body={})
        )
        response = self._execute(request, "processor", processor_id)
        return response
    def process_document(
        self,
        location: str,
        processor_id: str,
        raw_document: Optional[Dict[str, Any]] = None,
        gcs_document: Optional[Dict[str, Any]] = None,
        skip_human_review: bool = False,
    ) -> ProcessResult:
        """Process a document using a Document AI processor.

        Args:
            location: The GCP location/region
            processor_id: The ID of the processor to use
            raw_document: Optional raw document with content and mimeType
            gcs_document: Optional GCS document with gcsUri and mimeType
            skip_human_review: Whether to skip human review

        Returns:
            A ProcessResult instance
        """
        logger.info(
            "Processing document with processor %s in %s for project %s",
            processor_id,
            location,
            self.project_id,
        )

        name = self._format_processor_name(location, processor_id)
        body: Dict[str, Any] = {
            "skipHumanReview": skip_human_review,
        }

        if raw_document is not None:
            body["rawDocument"] = raw_document

        if gcs_document is not None:
            body["gcsDocument"] = gcs_document

        request = (
            self.service.projects()
            .locations()
            .processors()
            .process(name=name, body=body)
        )
        response = self._execute(request, "processor", processor_id)
        return ProcessResult.from_api_response(response)
    def batch_process_documents(
        self,
        location: str,
        processor_id: str,
        input_documents: Dict[str, Any],
        output_gcs_destination: str,
    ) -> Dict[str, Any]:
        """Batch process documents using a Document AI processor.

        Args:
            location: The GCP location/region
            processor_id: The ID of the processor to use
            input_documents: The input documents configuration
            output_gcs_destination: The GCS output destination URI

        Returns:
            The long-running operation response
        """
        logger.info(
            "Batch processing documents with processor %s in %s for project %s",
            processor_id,
            location,
            self.project_id,
        )

        name = self._format_processor_name(location, processor_id)
        body: Dict[str, Any] = {
            "inputDocuments": input_documents,
            "documentOutputConfig": {
                "gcsOutputConfig": {
                    "gcsUri": output_gcs_destination,
                },
            },
        }

        request = (
            self.service.projects()
            .locations()
            .processors()
            .batchProcess(name=name, body=body)
        )
        response = self._execute(request, "processor", processor_id)
        return response
    def list_processor_versions(
        self, location: str, processor_id: str, **kwargs
    ) -> List[ProcessorVersion]:
        """List versions of a Document AI processor.

        Args:
            location: The GCP location/region
            processor_id: The ID of the processor
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of ProcessorVersion instances
        """
        logger.debug(
            "Listing processor versions for %s in %s for project %s",
            processor_id,
            location,
            self.project_id,
        )

        parent = self._format_processor_name(location, processor_id)
        versions = []
        request = (
            self.service.projects()
            .locations()
            .processors()
            .processorVersions()
            .list(parent=parent, **kwargs)
        )

        while request is not None:
            response = self._execute(request)
            for item in response.get("processorVersions", []):
                versions.append(ProcessorVersion.from_api_response(item))
            request = (
                self.service.projects()
                .locations()
                .processors()
                .processorVersions()
                .list_next(request, response)
            )

        logger.debug("Found %s processor versions", len(versions))
        return versions
