"""Service implementation for Google Cloud Natural Language."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.natural_language import NLResult

logger = logging.getLogger(__name__)

class NaturalLanguageService(GCPService[NLResult]):
    """Service for interacting with Google Cloud Natural Language."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Natural Language service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="language",
            version="v1",
            credentials_file=credentials_file,
            resource_model=NLResult,
            **kwargs,
        )

    def _build_document(
        self,
        content: str,
        content_type: str = "PLAIN_TEXT",
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build the document object for a Natural Language request.

        Args:
            content: The text content to analyze
            content_type: The type of content ("PLAIN_TEXT" or "HTML")
            language: Optional BCP-47 language code

        Returns:
            A dictionary representing the document
        """
        document: Dict[str, Any] = {
            "type": content_type,
            "content": content,
        }
        if language is not None:
            document["language"] = language
        return document

    def analyze_sentiment(
        self,
        content: str,
        content_type: str = "PLAIN_TEXT",
        language: Optional[str] = None,
    ) -> NLResult:
        """Analyze the sentiment of the provided text.

        Args:
            content: The text content to analyze
            content_type: The type of content ("PLAIN_TEXT" or "HTML")
            language: Optional BCP-47 language code

        Returns:
            An NLResult instance with sentiment analysis
        """
        logger.debug(
            "Analyzing sentiment for project %s", self.project_id
        )

        document = self._build_document(content, content_type, language)
        body = {"document": document}

        request = self.service.documents().analyzeSentiment(body=body)
        response = self._execute(request)
        return NLResult.from_api_response(response)
    def analyze_entities(
        self,
        content: str,
        content_type: str = "PLAIN_TEXT",
        language: Optional[str] = None,
    ) -> NLResult:
        """Analyze the entities in the provided text.

        Args:
            content: The text content to analyze
            content_type: The type of content ("PLAIN_TEXT" or "HTML")
            language: Optional BCP-47 language code

        Returns:
            An NLResult instance with entity analysis
        """
        logger.debug(
            "Analyzing entities for project %s", self.project_id
        )

        document = self._build_document(content, content_type, language)
        body = {"document": document}

        request = self.service.documents().analyzeEntities(body=body)
        response = self._execute(request)
        return NLResult.from_api_response(response)
    def analyze_syntax(
        self,
        content: str,
        content_type: str = "PLAIN_TEXT",
        language: Optional[str] = None,
    ) -> NLResult:
        """Analyze the syntax of the provided text.

        Args:
            content: The text content to analyze
            content_type: The type of content ("PLAIN_TEXT" or "HTML")
            language: Optional BCP-47 language code

        Returns:
            An NLResult instance with syntax analysis
        """
        logger.debug(
            "Analyzing syntax for project %s", self.project_id
        )

        document = self._build_document(content, content_type, language)
        body = {"document": document}

        request = self.service.documents().analyzeSyntax(body=body)
        response = self._execute(request)
        return NLResult.from_api_response(response)
    def classify_text(
        self,
        content: str,
        content_type: str = "PLAIN_TEXT",
    ) -> NLResult:
        """Classify the provided text into categories.

        Args:
            content: The text content to classify
            content_type: The type of content ("PLAIN_TEXT" or "HTML")

        Returns:
            An NLResult instance with text classification
        """
        logger.debug(
            "Classifying text for project %s", self.project_id
        )

        document = self._build_document(content, content_type)
        body = {"document": document}

        request = self.service.documents().classifyText(body=body)
        response = self._execute(request)
        return NLResult.from_api_response(response)
    def annotate_text(
        self,
        content: str,
        features: Dict[str, bool],
        content_type: str = "PLAIN_TEXT",
        language: Optional[str] = None,
    ) -> NLResult:
        """Annotate the provided text with multiple analysis features.

        Args:
            content: The text content to annotate
            features: Dictionary of features to enable
                (e.g., {"extractSyntax": True, "extractEntities": True})
            content_type: The type of content ("PLAIN_TEXT" or "HTML")
            language: Optional BCP-47 language code

        Returns:
            An NLResult instance with the requested annotations
        """
        logger.debug(
            "Annotating text for project %s", self.project_id
        )

        document = self._build_document(content, content_type, language)
        body = {
            "document": document,
            "features": features,
        }

        request = self.service.documents().annotateText(body=body)
        response = self._execute(request)
        return NLResult.from_api_response(response)