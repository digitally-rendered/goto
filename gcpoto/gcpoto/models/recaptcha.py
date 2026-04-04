"""Models for Google Cloud reCAPTCHA Enterprise resources."""

from typing import Dict, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.recaptcha import get_schema


class RecaptchaKey(GCPResource):
    """Model for a reCAPTCHA Enterprise Key."""

    display_name: str = Field("", description="Human-readable display name")
    web_settings: Optional[Dict] = Field(
        None, description="Settings for keys that can be used by websites"
    )
    android_settings: Optional[Dict] = Field(
        None, description="Settings for keys that can be used by Android apps"
    )
    ios_settings: Optional[Dict] = Field(
        None, description="Settings for keys that can be used by iOS apps"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("recaptcha_key")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "RecaptchaKey":
        """Create a RecaptchaKey from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new RecaptchaKey instance
        """
        name = response.get("name", "")
        # Extract the key ID from the full resource name
        # Format: projects/{project}/keys/{key_id}
        key_id = name.rsplit("/", 1)[-1] if "/" in name else name

        instance = cls(
            id=key_id,
            name=name,
            type="recaptcha.key",
            project=response.get("project", ""),
            display_name=response.get("displayName", ""),
            web_settings=response.get("webSettings"),
            android_settings=response.get("androidSettings"),
            ios_settings=response.get("iosSettings"),
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default


class Assessment(GCPResource):
    """Model for a reCAPTCHA Enterprise Assessment."""

    token_properties: Optional[Dict] = Field(
        None, description="Properties of the token provided"
    )
    risk_analysis: Optional[Dict] = Field(
        None, description="The risk analysis result for the event"
    )
    event: Optional[Dict] = Field(
        None, description="The event being assessed"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("assessment")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Assessment":
        """Create an Assessment from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Assessment instance
        """
        name = response.get("name", "")
        # Extract the assessment ID from the full resource name
        # Format: projects/{project}/assessments/{assessment_id}
        assessment_id = name.rsplit("/", 1)[-1] if "/" in name else name

        return cls(
            id=assessment_id,
            name=name,
            type="recaptcha.assessment",
            project=response.get("project", ""),
            token_properties=response.get("tokenProperties"),
            risk_analysis=response.get("riskAnalysis"),
            event=response.get("event"),
        )
