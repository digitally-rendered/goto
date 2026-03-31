"""Service implementation for Google Cloud Firestore."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.firestore import (
    FirestoreDocument,
    FirestoreCollection,
    FirestoreIndex,
)
from gcpoto.exceptions import (
    APIError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


class FirestoreService(GCPService[FirestoreDocument]):
    """Service for interacting with Google Cloud Firestore."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Firestore service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="firestore",
            version="v1",
            credentials_file=credentials_file,
            resource_model=FirestoreDocument,
            **kwargs,
        )

    def _database_path(self) -> str:
        """Return the default database path.

        Returns:
            The fully-qualified database path.
        """
        return f"projects/{self.project_id}/databases/(default)"

    def _documents_path(self) -> str:
        """Return the documents root path.

        Returns:
            The fully-qualified documents root path.
        """
        return f"{self._database_path()}/documents"

    def _document_path(self, collection: str, document_id: str) -> str:
        """Return the full path to a specific document.

        Args:
            collection: The collection name.
            document_id: The document ID.

        Returns:
            The fully-qualified document resource path.
        """
        return f"{self._documents_path()}/{collection}/{document_id}"

    def get_document(
        self, collection: str, document_id: str
    ) -> FirestoreDocument:
        """Get a specific document from a collection.

        Args:
            collection: The collection name
            document_id: The document ID

        Returns:
            A FirestoreDocument instance

        Raises:
            ResourceNotFoundError: If the document does not exist
            APIError: If the API call fails
        """
        name = self._document_path(collection, document_id)
        logger.debug("Getting document %s", name)

        request = (
            self.service.projects()
            .databases()
            .documents()
            .get(name=name)
        )
        response = self._execute(request, "firestore.document", f)
        return FirestoreDocument.from_api_response(
            response, self.project_id
        )
    def create_document(
        self,
        collection: str,
        document_id: str,
        fields: Dict[str, Any],
    ) -> FirestoreDocument:
        """Create a new document in a collection.

        Args:
            collection: The collection name
            document_id: The document ID
            fields: The document fields

        Returns:
            The created FirestoreDocument instance

        Raises:
            APIError: If the API call fails
        """
        parent = self._documents_path()
        body = {"fields": fields}
        logger.debug(
            "Creating document %s/%s in project %s",
            collection,
            document_id,
            self.project_id,
        )

        request = (
            self.service.projects()
            .databases()
            .documents()
            .createDocument(
                parent=parent,
                collectionId=collection,
                documentId=document_id,
                body=body,
            )
        )
        response = self._execute(request)
        return FirestoreDocument.from_api_response(
            response, self.project_id
        )
    def update_document(
        self,
        collection: str,
        document_id: str,
        fields: Dict[str, Any],
        update_mask: Optional[List[str]] = None,
    ) -> FirestoreDocument:
        """Update an existing document.

        Args:
            collection: The collection name
            document_id: The document ID
            fields: The document fields to update
            update_mask: Optional list of field paths to update;
                if None, all fields in the body are updated

        Returns:
            The updated FirestoreDocument instance

        Raises:
            ResourceNotFoundError: If the document does not exist
            APIError: If the API call fails
        """
        name = self._document_path(collection, document_id)
        body = {"fields": fields}
        logger.debug("Updating document %s", name)

        kwargs: Dict[str, Any] = {"name": name, "body": body}
        if update_mask is not None:
            kwargs["updateMask_fieldPaths"] = update_mask

        request = (
            self.service.projects()
            .databases()
            .documents()
            .patch(**kwargs)
        )
        response = self._execute(request, "firestore.document", f)
        return FirestoreDocument.from_api_response(
            response, self.project_id
        )
    def delete_document(
        self, collection: str, document_id: str
    ) -> bool:
        """Delete a document from a collection.

        Args:
            collection: The collection name
            document_id: The document ID

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the document does not exist
            APIError: If the API call fails
        """
        name = self._document_path(collection, document_id)
        logger.debug("Deleting document %s", name)

        self.service.projects().databases().documents().delete(
            name=name
        ).execute()
        return True
    def list_documents(
        self,
        collection: str,
        page_size: int = 100,
        order_by: Optional[str] = None,
    ) -> List[FirestoreDocument]:
        """List documents in a collection.

        Args:
            collection: The collection name
            page_size: Maximum number of documents to return per page
            order_by: Optional field path to order results by

        Returns:
            A list of FirestoreDocument instances

        Raises:
            APIError: If the API call fails
        """
        parent = self._documents_path()
        logger.debug(
            "Listing documents in collection %s, project %s",
            collection,
            self.project_id,
        )

        kwargs: Dict[str, Any] = {
            "parent": parent,
            "collectionId": collection,
            "pageSize": page_size,
        }
        if order_by:
            kwargs["orderBy"] = order_by

        request = (
            self.service.projects()
            .databases()
            .documents()
            .list(**kwargs)
        )

        documents = []
        while request is not None:
            response = self._execute(request)
            for doc_data in response.get("documents", []):
                documents.append(
                    FirestoreDocument.from_api_response(
                        doc_data, self.project_id
                    )
                )
            request = (
                self.service.projects()
                .databases()
                .documents()
                .list_next(request, response)
            )

        return documents
    def query_documents(
        self,
        collection: str,
        field_filters: Optional[List[Dict[str, Any]]] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        limit: Optional[int] = None,
    ) -> List[FirestoreDocument]:
        """Query documents in a collection using structured queries.

        Args:
            collection: The collection name to query
            field_filters: Optional list of field filter dicts, each with
                keys "field", "op", and "value"
            order_by: Optional list of order-by dicts, each with
                keys "field" and "direction"
            limit: Optional maximum number of results

        Returns:
            A list of matching FirestoreDocument instances

        Raises:
            APIError: If the API call fails
        """
        parent = self._documents_path()
        logger.debug(
            "Querying documents in collection %s, project %s",
            collection,
            self.project_id,
        )

        structured_query: Dict[str, Any] = {
            "from": [{"collectionId": collection}],
        }

        if field_filters:
            if len(field_filters) == 1:
                f = field_filters[0]
                structured_query["where"] = {
                    "fieldFilter": {
                        "field": {"fieldPath": f["field"]},
                        "op": f["op"],
                        "value": f["value"],
                    }
                }
            else:
                filters = []
                for f in field_filters:
                    filters.append(
                        {
                            "fieldFilter": {
                                "field": {"fieldPath": f["field"]},
                                "op": f["op"],
                                "value": f["value"],
                            }
                        }
                    )
                structured_query["where"] = {
                    "compositeFilter": {
                        "op": "AND",
                        "filters": filters,
                    }
                }

        if order_by:
            structured_query["orderBy"] = [
                {
                    "field": {"fieldPath": o["field"]},
                    "direction": o.get("direction", "ASCENDING"),
                }
                for o in order_by
            ]

        if limit is not None:
            structured_query["limit"] = limit

        body = {"structuredQuery": structured_query}

        request = (
            self.service.projects()
            .databases()
            .documents()
            .runQuery(parent=parent, body=body)
        )
        response = self._execute(request)

        documents = []
        if isinstance(response, list):
            for result in response:
                doc = result.get("document")
                if doc:
                    documents.append(
                        FirestoreDocument.from_api_response(
                            doc, self.project_id
                        )
                    )

        return documents
    def list_collection_ids(
        self, parent: Optional[str] = None
    ) -> List[FirestoreCollection]:
        """List collection IDs under a parent document or the database root.

        Args:
            parent: Optional parent document path; defaults to database root

        Returns:
            A list of FirestoreCollection instances

        Raises:
            APIError: If the API call fails
        """
        if parent is None:
            parent = self._documents_path()
        logger.debug("Listing collection IDs under %s", parent)

        request = (
            self.service.projects()
            .databases()
            .documents()
            .listCollectionIds(parent=parent, body={})
        )
        response = self._execute(request)

        collections = []
        for cid in response.get("collectionIds", []):
            collections.append(
                FirestoreCollection.from_api_response(
                    cid, self.project_id
                )
            )

        return collections
    def list_indexes(
        self, collection_group: Optional[str] = None
    ) -> List[FirestoreIndex]:
        """List indexes for the database or a specific collection group.

        Args:
            collection_group: Optional collection group to filter indexes;
                if None, uses "-" to list all indexes

        Returns:
            A list of FirestoreIndex instances

        Raises:
            APIError: If the API call fails
        """
        group = collection_group or "-"
        parent = (
            f"{self._database_path()}/collectionGroups/{group}"
        )
        logger.debug("Listing indexes under %s", parent)

        request = (
            self.service.projects()
            .databases()
            .collectionGroups()
            .indexes()
            .list(parent=parent)
        )
        response = self._execute(request)

        indexes = []
        for idx_data in response.get("indexes", []):
            indexes.append(
                FirestoreIndex.from_api_response(
                    idx_data, self.project_id
                )
            )

        return indexes
    def create_index(
        self,
        collection_group: str,
        fields_config: List[Dict],
        query_scope: str = "COLLECTION",
    ) -> FirestoreIndex:
        """Create a composite index for a collection group.

        Args:
            collection_group: The collection group to create the index for
            fields_config: List of field configuration dicts with
                "fieldPath" and "order" or "arrayConfig"
            query_scope: The query scope: "COLLECTION" or "COLLECTION_GROUP"

        Returns:
            The created FirestoreIndex instance (may be in CREATING state)

        Raises:
            APIError: If the API call fails
        """
        parent = (
            f"{self._database_path()}/collectionGroups/{collection_group}"
        )
        body = {
            "queryScope": query_scope,
            "fields": fields_config,
        }
        logger.debug(
            "Creating index on collection group %s in project %s",
            collection_group,
            self.project_id,
        )

        request = (
            self.service.projects()
            .databases()
            .collectionGroups()
            .indexes()
            .create(parent=parent, body=body)
        )
        response = self._execute(request)
        return FirestoreIndex.from_api_response(
            response, self.project_id
        )
    def delete_index(self, index_name: str) -> bool:
        """Delete an index by its full resource name.

        Args:
            index_name: The fully-qualified index resource name

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the index does not exist
            APIError: If the API call fails
        """
        logger.debug("Deleting index %s", index_name)

        self.service.projects().databases().collectionGroups().indexes().delete(
            name=index_name
        ).execute()
        return True
    def batch_get_documents(
        self, collection: str, document_ids: List[str]
    ) -> List[FirestoreDocument]:
        """Get multiple documents in a single request.

        Args:
            collection: The collection name
            document_ids: List of document IDs to retrieve

        Returns:
            A list of FirestoreDocument instances for found documents

        Raises:
            APIError: If the API call fails
        """
        database = self._database_path()
        document_names = [
            self._document_path(collection, doc_id)
            for doc_id in document_ids
        ]
        logger.debug(
            "Batch getting %d documents from collection %s",
            len(document_ids),
            collection,
        )

        body = {"documents": document_names}

        request = (
            self.service.projects()
            .databases()
            .documents()
            .batchGet(database=database, body=body)
        )
        response = self._execute(request)

        documents = []
        if isinstance(response, list):
            for result in response:
                doc = result.get("found", {}).get("document")
                if doc:
                    documents.append(
                        FirestoreDocument.from_api_response(
                            doc, self.project_id
                        )
                    )

        return documents