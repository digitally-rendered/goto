"""Models for Google Cloud Recommendations AI resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.recommendations_ai import get_schema


class CatalogItem(GCPResource):
    """Model for a Recommendations AI Catalog Item."""

    category_hierarchies: Optional[List[Dict[str, Any]]] = Field(
        None, description="Category hierarchies for the catalog item"
    )
    title: str = Field("", description="The catalog item title")
    description: Optional[str] = Field(
        None, description="The catalog item description"
    )
    item_attributes: Optional[Dict[str, Any]] = Field(
        None, description="Extra catalog item attributes"
    )
    language_code: Optional[str] = Field(
        None, description="Language code (BCP-47)"
    )
    product_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Product metadata for retail items"
    )
    _tags: Optional[Dict[str, str]] = None

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

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("catalog_item")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "CatalogItem":
        """Create a CatalogItem from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new CatalogItem instance
        """
        item_id = response.get("id", "")
        full_name = response.get("name", "")

        if not project_id and full_name:
            parts = full_name.split("/")
            if len(parts) >= 2:
                project_id = parts[1]

        instance = cls(
            id=item_id,
            name=full_name or item_id,
            type="recommendationengine.catalogItem",
            project=project_id,
            title=response.get("title", ""),
            category_hierarchies=response.get("categoryHierarchies"),
            description=response.get("description"),
            item_attributes=response.get("itemAttributes"),
            language_code=response.get("languageCode"),
            product_metadata=response.get("productMetadata"),
        )

        return instance


class PredictionResult(GCPResource):
    """Model for a Recommendations AI Prediction Result."""

    results: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of recommended items"
    )
    attribution_token: Optional[str] = Field(
        None, description="Attribution token for tracking"
    )
    missing_ids: Optional[List[str]] = Field(
        None, description="IDs of items that were missing from the catalog"
    )
    _tags: Optional[Dict[str, str]] = None

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

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("prediction_result")}

    @classmethod
    def from_api_response(
        cls, response: Dict[str, Any], project_id: str = ""
    ) -> "PredictionResult":
        """Create a PredictionResult from an API response.

        Args:
            response: The API response dictionary
            project_id: The GCP project ID

        Returns:
            A new PredictionResult instance
        """
        attribution_token = response.get("attributionToken", "")

        instance = cls(
            id=attribution_token or "prediction",
            name="prediction",
            type="recommendationengine.predictionResult",
            project=project_id,
            results=response.get("results", []),
            attribution_token=response.get("attributionToken"),
            missing_ids=response.get("missingIds"),
        )

        return instance
