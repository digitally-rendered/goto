"""Service implementation for Google Cloud Translation."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.translation import Translation, DetectedLanguage
from gcpoto.exceptions import APIError

logger = logging.getLogger(__name__)


class TranslationService(GCPService[Translation]):
    """Service for interacting with Google Cloud Translation."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Translation service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="translate",
            version="v3",
            credentials_file=credentials_file,
            resource_model=Translation,
            **kwargs,
        )

    def _format_parent(self) -> str:
        """Format the parent path for Translation API requests.

        Returns:
            The formatted parent path
        """
        return f"projects/{self.project_id}/locations/global"

    def translate_text(
        self,
        contents: List[str],
        target_language: str,
        source_language: Optional[str] = None,
        model: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> List[Translation]:
        """Translate text to a target language.

        Args:
            contents: List of text strings to translate
            target_language: The BCP-47 language code to translate to
            source_language: Optional BCP-47 language code of the source
            model: Optional model to use for translation
            mime_type: Optional MIME type of the content ("text/plain" or "text/html")

        Returns:
            A list of Translation instances
        """
        logger.debug(
            "Translating text to %s for project %s",
            target_language,
            self.project_id,
        )

        parent = self._format_parent()
        body: Dict[str, Any] = {
            "contents": contents,
            "targetLanguageCode": target_language,
        }

        if source_language is not None:
            body["sourceLanguageCode"] = source_language
        if model is not None:
            body["model"] = model
        if mime_type is not None:
            body["mimeType"] = mime_type

        try:
            request = (
                self.service.projects()
                .locations()
                .translateText(parent=parent, body=body)
            )
            response = request.execute()
            translations = response.get("translations", [])
            return [Translation.from_api_response(t) for t in translations]
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

    def detect_language(
        self,
        content: str,
    ) -> List[DetectedLanguage]:
        """Detect the language of the provided text.

        Args:
            content: The text content to detect the language of

        Returns:
            A list of DetectedLanguage instances
        """
        logger.debug(
            "Detecting language for project %s", self.project_id
        )

        parent = self._format_parent()
        body: Dict[str, Any] = {
            "content": content,
        }

        try:
            request = (
                self.service.projects()
                .locations()
                .detectLanguage(parent=parent, body=body)
            )
            response = request.execute()
            languages = response.get("languages", [])
            return [
                DetectedLanguage.from_api_response(lang)
                for lang in languages
            ]
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

    def get_supported_languages(
        self,
        display_language_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get the list of supported languages for translation.

        Args:
            display_language_code: Optional BCP-47 language code for display names

        Returns:
            A dictionary containing the supported languages
        """
        logger.debug(
            "Getting supported languages for project %s", self.project_id
        )

        parent = self._format_parent()
        kwargs: Dict[str, Any] = {"parent": parent}

        if display_language_code is not None:
            kwargs["displayLanguageCode"] = display_language_code

        try:
            request = (
                self.service.projects()
                .locations()
                .getSupportedLanguages(**kwargs)
            )
            response = request.execute()
            return response
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

    def batch_translate_text(
        self,
        source_language: str,
        target_languages: List[str],
        input_configs: List[Dict[str, Any]],
        output_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Start a batch translation operation.

        Args:
            source_language: The BCP-47 language code of the source text
            target_languages: List of BCP-47 language codes to translate to
            input_configs: List of input configuration dicts
            output_config: Output configuration dict

        Returns:
            A dictionary representing the long-running operation
        """
        logger.debug(
            "Starting batch translation for project %s", self.project_id
        )

        parent = self._format_parent()
        body: Dict[str, Any] = {
            "sourceLanguageCode": source_language,
            "targetLanguageCodes": target_languages,
            "inputConfigs": input_configs,
            "outputConfig": output_config,
        }

        try:
            request = (
                self.service.projects()
                .locations()
                .batchTranslateText(parent=parent, body=body)
            )
            response = request.execute()
            return response
        except HttpError as e:
            raise APIError(e.resp.status, str(e))
