"""Service implementation for Google Cloud Speech-to-Text."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.speech import RecognitionResult, RecognitionConfig

logger = logging.getLogger(__name__)

class SpeechService(GCPService[RecognitionResult]):
    """Service for interacting with Google Cloud Speech-to-Text."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Speech-to-Text service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="speech",
            version="v1",
            credentials_file=credentials_file,
            resource_model=RecognitionResult,
            **kwargs,
        )

    def _build_audio(
        self,
        audio_uri: Optional[str] = None,
        audio_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build the audio object for a recognition request.

        Args:
            audio_uri: URI of the audio file (GCS URI)
            audio_content: Base64-encoded audio content

        Returns:
            A dictionary representing the audio source
        """
        audio: Dict[str, Any] = {}
        if audio_uri is not None:
            audio["uri"] = audio_uri
        if audio_content is not None:
            audio["content"] = audio_content
        return audio

    def _build_config(
        self,
        config: Optional[RecognitionConfig] = None,
        encoding: str = "LINEAR16",
        sample_rate_hertz: int = 16000,
        language_code: str = "en-US",
    ) -> Dict[str, Any]:
        """Build the recognition config for a request.

        Args:
            config: Optional RecognitionConfig object
            encoding: Audio encoding format (used if config is None)
            sample_rate_hertz: Sample rate in Hertz (used if config is None)
            language_code: BCP-47 language code (used if config is None)

        Returns:
            A dictionary representing the recognition configuration
        """
        if config is not None:
            cfg: Dict[str, Any] = {
                "encoding": config.encoding,
                "sampleRateHertz": config.sample_rate_hertz,
                "languageCode": config.language_code,
                "useEnhanced": config.use_enhanced,
            }
            if config.model is not None:
                cfg["model"] = config.model
            return cfg

        return {
            "encoding": encoding,
            "sampleRateHertz": sample_rate_hertz,
            "languageCode": language_code,
        }

    def recognize(
        self,
        audio_uri: Optional[str] = None,
        audio_content: Optional[str] = None,
        config: Optional[RecognitionConfig] = None,
        encoding: str = "LINEAR16",
        sample_rate_hertz: int = 16000,
        language_code: str = "en-US",
    ) -> List[RecognitionResult]:
        """Perform synchronous speech recognition.

        Args:
            audio_uri: URI of the audio file (GCS URI)
            audio_content: Base64-encoded audio content
            config: Optional RecognitionConfig object
            encoding: Audio encoding format (used if config is None)
            sample_rate_hertz: Sample rate in Hertz (used if config is None)
            language_code: BCP-47 language code (used if config is None)

        Returns:
            A list of RecognitionResult instances
        """
        logger.debug(
            "Performing speech recognition for project %s", self.project_id
        )

        audio = self._build_audio(audio_uri, audio_content)
        recognition_config = self._build_config(
            config, encoding, sample_rate_hertz, language_code
        )

        body = {
            "audio": audio,
            "config": recognition_config,
        }

        request = self.service.speech().recognize(body=body)
        response = self._execute(request)
        results = response.get("results", [])
        return [
            RecognitionResult.from_api_response(r) for r in results
        ]
    def long_running_recognize(
        self,
        audio_uri: Optional[str] = None,
        audio_content: Optional[str] = None,
        config: Optional[RecognitionConfig] = None,
        encoding: str = "LINEAR16",
        sample_rate_hertz: int = 16000,
        language_code: str = "en-US",
    ) -> Dict[str, Any]:
        """Perform asynchronous (long-running) speech recognition.

        Args:
            audio_uri: URI of the audio file (GCS URI)
            audio_content: Base64-encoded audio content
            config: Optional RecognitionConfig object
            encoding: Audio encoding format (used if config is None)
            sample_rate_hertz: Sample rate in Hertz (used if config is None)
            language_code: BCP-47 language code (used if config is None)

        Returns:
            A dictionary representing the long-running operation
        """
        logger.debug(
            "Performing long-running speech recognition for project %s",
            self.project_id,
        )

        audio = self._build_audio(audio_uri, audio_content)
        recognition_config = self._build_config(
            config, encoding, sample_rate_hertz, language_code
        )

        body = {
            "audio": audio,
            "config": recognition_config,
        }

        request = self.service.speech().longrunningrecognize(body=body)
        response = self._execute(request)
        return response