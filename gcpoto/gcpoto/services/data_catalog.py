"""Service implementation for Google Cloud Data Catalog."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.data_catalog import EntryGroup, Entry, Tag
from gcpoto.exceptions import ResourceNotFoundError, APIError

logger = logging.getLogger(__name__)


class DataCatalogService(GCPService[EntryGroup]):
    """Service for interacting with Google Cloud Data Catalog."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Data Catalog service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="datacatalog",
            version="v1",
            credentials_file=credentials_file,
            resource_model=EntryGroup,
            **kwargs,
        )

    def list_entry_groups(
        self, location: str
    ) -> List[EntryGroup]:
        """List entry groups in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            A list of EntryGroup instances
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
        )
        request = (
            self.service.projects()
            .locations()
            .entryGroups()
            .list(parent=parent)
        )

        entry_groups = []
        while request is not None:
            response = request.execute()
            for item in response.get("entryGroups", []):
                entry_groups.append(
                    EntryGroup.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .entryGroups()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s entry groups in %s", len(entry_groups), location
        )
        return entry_groups

    def get_entry_group(
        self, location: str, entry_group_id: str
    ) -> EntryGroup:
        """Get a specific entry group.

        Args:
            location: The GCP location (e.g. 'us-central1')
            entry_group_id: The ID of the entry group

        Returns:
            An EntryGroup instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/entryGroups/{entry_group_id}"
        )
        try:
            request = (
                self.service.projects()
                .locations()
                .entryGroups()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("entry_group", entry_group_id)
            raise

        logger.debug("Retrieved entry group %s", entry_group_id)
        return EntryGroup.from_api_response(response, self.project_id)

    def create_entry_group(
        self,
        location: str,
        entry_group_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> EntryGroup:
        """Create a new entry group.

        Args:
            location: The GCP location (e.g. 'us-central1')
            entry_group_id: The ID for the new entry group
            display_name: Optional display name
            description: Optional description

        Returns:
            The created EntryGroup instance
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
        )
        body: Dict[str, Any] = {}
        if display_name is not None:
            body["displayName"] = display_name
        if description is not None:
            body["description"] = description

        try:
            request = (
                self.service.projects()
                .locations()
                .entryGroups()
                .create(
                    parent=parent,
                    entryGroupId=entry_group_id,
                    body=body,
                )
            )
            response = request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

        logger.debug("Created entry group %s in %s", entry_group_id, location)
        return EntryGroup.from_api_response(response, self.project_id)

    def delete_entry_group(
        self, location: str, entry_group_id: str
    ) -> bool:
        """Delete an entry group.

        Args:
            location: The GCP location (e.g. 'us-central1')
            entry_group_id: The ID of the entry group to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/entryGroups/{entry_group_id}"
        )
        try:
            self.service.projects().locations().entryGroups().delete(
                name=name
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("entry_group", entry_group_id)
            raise

        logger.debug("Deleted entry group %s", entry_group_id)
        return True

    def list_entries(
        self, location: str, entry_group_id: str
    ) -> List[Entry]:
        """List entries in an entry group.

        Args:
            location: The GCP location (e.g. 'us-central1')
            entry_group_id: The ID of the entry group

        Returns:
            A list of Entry instances
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/entryGroups/{entry_group_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .entryGroups()
            .entries()
            .list(parent=parent)
        )

        entries = []
        while request is not None:
            response = request.execute()
            for item in response.get("entries", []):
                entries.append(
                    Entry.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .entryGroups()
                .entries()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s entries in entry group %s",
            len(entries),
            entry_group_id,
        )
        return entries

    def get_entry(
        self, location: str, entry_group_id: str, entry_id: str
    ) -> Entry:
        """Get a specific entry.

        Args:
            location: The GCP location (e.g. 'us-central1')
            entry_group_id: The ID of the entry group
            entry_id: The ID of the entry

        Returns:
            An Entry instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/entryGroups/{entry_group_id}/entries/{entry_id}"
        )
        try:
            request = (
                self.service.projects()
                .locations()
                .entryGroups()
                .entries()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("entry", entry_id)
            raise

        logger.debug("Retrieved entry %s", entry_id)
        return Entry.from_api_response(response, self.project_id)

    def create_entry(
        self,
        location: str,
        entry_group_id: str,
        entry_id: str,
        entry_type: str,
        linked_resource: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Entry:
        """Create a new entry.

        Args:
            location: The GCP location (e.g. 'us-central1')
            entry_group_id: The ID of the entry group
            entry_id: The ID for the new entry
            entry_type: The type of the entry
            linked_resource: Optional linked resource URI
            schema: Optional schema definition

        Returns:
            The created Entry instance
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/entryGroups/{entry_group_id}"
        )
        body: Dict[str, Any] = {"userSpecifiedType": entry_type}
        if linked_resource is not None:
            body["linkedResource"] = linked_resource
        if schema is not None:
            body["schema"] = schema

        try:
            request = (
                self.service.projects()
                .locations()
                .entryGroups()
                .entries()
                .create(
                    parent=parent,
                    entryId=entry_id,
                    body=body,
                )
            )
            response = request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

        logger.debug(
            "Created entry %s in entry group %s",
            entry_id,
            entry_group_id,
        )
        return Entry.from_api_response(response, self.project_id)

    def delete_entry(
        self, location: str, entry_group_id: str, entry_id: str
    ) -> bool:
        """Delete an entry.

        Args:
            location: The GCP location (e.g. 'us-central1')
            entry_group_id: The ID of the entry group
            entry_id: The ID of the entry to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/entryGroups/{entry_group_id}/entries/{entry_id}"
        )
        try:
            self.service.projects().locations().entryGroups().entries().delete(
                name=name
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("entry", entry_id)
            raise

        logger.debug("Deleted entry %s", entry_id)
        return True

    def search_catalog(
        self, scope: Dict[str, Any], query: str
    ) -> List[Dict[str, Any]]:
        """Search the catalog.

        Args:
            scope: The scope of the search (e.g. {"includeProjectIds": [...]})
            query: The search query string

        Returns:
            A list of search result dictionaries
        """
        body = {"scope": scope, "query": query}

        try:
            request = self.service.catalog().search(body=body)
            response = request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e))

        results = response.get("results", [])
        logger.debug("Search returned %s results for query: %s", len(results), query)
        return results
