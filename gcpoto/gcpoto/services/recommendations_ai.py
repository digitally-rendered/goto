"""Service implementation for Google Cloud Recommendations AI."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.recommendations_ai import CatalogItem, PredictionResult
from gcpoto.exceptions import (
    APIError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


class RecommendationsAIService(GCPService[CatalogItem]):
    """Service for interacting with Google Cloud Recommendations AI."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Recommendations AI service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="recommendationengine",
            version="v1beta1",
            credentials_file=credentials_file,
            resource_model=CatalogItem,
            **kwargs,
        )

    def _catalog_path(self, location: str, catalog: str) -> str:
        """Return the catalog resource path.

        Args:
            location: The GCP location (e.g. "global")
            catalog: The catalog name

        Returns:
            The fully-qualified catalog path
        """
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/catalogs/{catalog}"
        )

    def _catalog_items_path(self, location: str, catalog: str) -> str:
        """Return the catalog items parent path.

        Args:
            location: The GCP location
            catalog: The catalog name

        Returns:
            The fully-qualified catalog items parent path
        """
        return f"{self._catalog_path(location, catalog)}/catalogItems"

    def _catalog_item_path(
        self, location: str, catalog: str, item_id: str
    ) -> str:
        """Return a specific catalog item path.

        Args:
            location: The GCP location
            catalog: The catalog name
            item_id: The catalog item ID

        Returns:
            The fully-qualified catalog item path
        """
        return f"{self._catalog_items_path(location, catalog)}/{item_id}"

    def list_catalog_items(
        self,
        location: str,
        catalog: str = "default_catalog",
    ) -> List[CatalogItem]:
        """List catalog items.

        Args:
            location: The GCP location (e.g. "global")
            catalog: The catalog name

        Returns:
            A list of CatalogItem instances

        Raises:
            APIError: If the API call fails
        """
        parent = self._catalog_items_path(location, catalog)
        logger.debug("Listing catalog items under %s", parent)

        request = (
            self.service.projects()
            .locations()
            .catalogs()
            .catalogItems()
            .list(parent=parent)
        )
        response = self._execute(request)

        items = []
        for item_data in response.get("catalogItems", []):
            items.append(
                CatalogItem.from_api_response(item_data, self.project_id)
            )

        return items
    def get_catalog_item(
        self, location: str, catalog: str, item_id: str
    ) -> CatalogItem:
        """Get a specific catalog item.

        Args:
            location: The GCP location
            catalog: The catalog name
            item_id: The catalog item ID

        Returns:
            A CatalogItem instance

        Raises:
            ResourceNotFoundError: If the item does not exist
            APIError: If the API call fails
        """
        name = self._catalog_item_path(location, catalog, item_id)
        logger.debug("Getting catalog item %s", name)

        request = (
            self.service.projects()
            .locations()
            .catalogs()
            .catalogItems()
            .get(name=name)
        )
        response = self._execute(request, "recommendationengine.catalogItem", item_id)
        return CatalogItem.from_api_response(response, self.project_id)
    def create_catalog_item(
        self,
        location: str,
        catalog: str,
        item_id: str,
        title: str,
        category_hierarchies: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
    ) -> CatalogItem:
        """Create a new catalog item.

        Args:
            location: The GCP location
            catalog: The catalog name
            item_id: The catalog item ID
            title: The item title
            category_hierarchies: Optional category hierarchies
            description: Optional item description

        Returns:
            The created CatalogItem instance

        Raises:
            APIError: If the API call fails
        """
        parent = self._catalog_items_path(location, catalog)
        logger.debug(
            "Creating catalog item %s under %s", item_id, parent
        )

        body: Dict[str, Any] = {
            "id": item_id,
            "title": title,
        }
        if category_hierarchies is not None:
            body["categoryHierarchies"] = category_hierarchies
        if description is not None:
            body["description"] = description

        request = (
            self.service.projects()
            .locations()
            .catalogs()
            .catalogItems()
            .create(parent=parent, body=body)
        )
        response = self._execute(request)
        return CatalogItem.from_api_response(response, self.project_id)
    def update_catalog_item(
        self,
        location: str,
        catalog: str,
        item_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> CatalogItem:
        """Update an existing catalog item.

        Args:
            location: The GCP location
            catalog: The catalog name
            item_id: The catalog item ID
            update_mask: Comma-separated field paths to update
            update_fields: Dict of fields to update

        Returns:
            The updated CatalogItem instance

        Raises:
            ResourceNotFoundError: If the item does not exist
            APIError: If the API call fails
        """
        name = self._catalog_item_path(location, catalog, item_id)
        logger.debug("Updating catalog item %s", name)

        request = (
            self.service.projects()
            .locations()
            .catalogs()
            .catalogItems()
            .patch(name=name, updateMask=update_mask, body=update_fields)
        )
        response = self._execute(request, "recommendationengine.catalogItem", item_id)
        return CatalogItem.from_api_response(response, self.project_id)
    def delete_catalog_item(
        self, location: str, catalog: str, item_id: str
    ) -> bool:
        """Delete a catalog item.

        Args:
            location: The GCP location
            catalog: The catalog name
            item_id: The catalog item ID

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the item does not exist
            APIError: If the API call fails
        """
        name = self._catalog_item_path(location, catalog, item_id)
        logger.debug("Deleting catalog item %s", name)

        (
            self.service.projects()
            .locations()
            .catalogs()
            .catalogItems()
            .delete(name=name)
        ).execute()
        return True
    def import_catalog_items(
        self,
        location: str,
        catalog: str,
        input_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Import catalog items in bulk.

        Args:
            location: The GCP location
            catalog: The catalog name
            input_config: The input configuration dict specifying data source

        Returns:
            The long-running operation response dict

        Raises:
            APIError: If the API call fails
        """
        parent = self._catalog_items_path(location, catalog)
        logger.debug("Importing catalog items under %s", parent)

        body = {"inputConfig": input_config}

        request = (
            self.service.projects()
            .locations()
            .catalogs()
            .catalogItems()
            .import_(parent=parent, body=body)
        )
        return self._execute(request)
    def predict(
        self,
        location: str,
        catalog: str,
        placement_id: str,
        user_event: Dict[str, Any],
        page_size: Optional[int] = None,
        filter_str: Optional[str] = None,
    ) -> PredictionResult:
        """Get recommendations for a user event.

        Args:
            location: The GCP location
            catalog: The catalog name
            placement_id: The placement ID for the prediction
            user_event: The user event dict to base predictions on
            page_size: Optional maximum number of results
            filter_str: Optional filter expression

        Returns:
            A PredictionResult instance

        Raises:
            APIError: If the API call fails
        """
        name = (
            f"{self._catalog_path(location, catalog)}"
            f"/placements/{placement_id}"
        )
        logger.debug("Predicting with placement %s", name)

        body: Dict[str, Any] = {"userEvent": user_event}
        if page_size is not None:
            body["pageSize"] = page_size
        if filter_str is not None:
            body["filter"] = filter_str

        request = (
            self.service.projects()
            .locations()
            .catalogs()
            .placements()
            .predict(name=name, body=body)
        )
        response = self._execute(request)
        return PredictionResult.from_api_response(
            response, self.project_id
        )