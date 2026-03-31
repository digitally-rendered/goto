"""Service implementation for Google Cloud Datastore."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.datastore import Entity, EntityResult
from gcpoto.exceptions import APIError

logger = logging.getLogger(__name__)


class DatastoreService(GCPService[Entity]):
    """Service for interacting with Google Cloud Datastore."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Datastore service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="datastore",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Entity,
            **kwargs,
        )

    def lookup(self, keys: List[Dict[str, Any]]) -> List[EntityResult]:
        """Look up entities by key.

        Args:
            keys: List of entity key dicts to look up

        Returns:
            A list of EntityResult instances for found entities

        Raises:
            APIError: If the API call fails
        """
        logger.debug("Looking up %d keys in project %s", len(keys), self.project_id)

        body = {"keys": keys}

        request = self.service.projects().lookup(
            projectId=self.project_id, body=body
        )
        response = self._execute(request)

        results = []
        for entity_result in response.get("found", []):
            results.append(
                EntityResult.from_api_response(entity_result, self.project_id)
            )

        return results
    def run_query(
        self,
        kind: str,
        filters: Optional[List[Dict[str, Any]]] = None,
        order: Optional[List[Dict[str, str]]] = None,
        limit: Optional[int] = None,
    ) -> List[EntityResult]:
        """Run a query against Datastore.

        Args:
            kind: The entity kind to query
            filters: Optional list of property filter dicts
            order: Optional list of order dicts with "property" and "direction"
            limit: Optional maximum number of results

        Returns:
            A list of EntityResult instances

        Raises:
            APIError: If the API call fails
        """
        logger.debug(
            "Running query on kind %s in project %s", kind, self.project_id
        )

        query: Dict[str, Any] = {
            "kind": [{"name": kind}],
        }

        if filters:
            if len(filters) == 1:
                query["filter"] = {
                    "propertyFilter": filters[0],
                }
            else:
                query["filter"] = {
                    "compositeFilter": {
                        "op": "AND",
                        "filters": [
                            {"propertyFilter": f} for f in filters
                        ],
                    },
                }

        if order:
            query["order"] = [
                {
                    "property": {"name": o["property"]},
                    "direction": o.get("direction", "ASCENDING"),
                }
                for o in order
            ]

        if limit is not None:
            query["limit"] = limit

        body = {"query": query}

        request = self.service.projects().runQuery(
            projectId=self.project_id, body=body
        )
        response = self._execute(request)

        results = []
        batch = response.get("batch", {})
        for entity_result in batch.get("entityResults", []):
            results.append(
                EntityResult.from_api_response(entity_result, self.project_id)
            )

        return results
    def upsert(self, entities: List[Dict[str, Any]]) -> List[Entity]:
        """Upsert entities into Datastore.

        Args:
            entities: List of entity dicts to upsert

        Returns:
            A list of Entity instances with updated keys

        Raises:
            APIError: If the API call fails
        """
        logger.debug(
            "Upserting %d entities in project %s",
            len(entities),
            self.project_id,
        )

        mutations = [{"upsert": entity} for entity in entities]
        body = {"mutations": mutations}

        request = self.service.projects().commit(
            projectId=self.project_id, body=body
        )
        response = self._execute(request)

        results = []
        for mutation_result in response.get("mutationResults", []):
            key = mutation_result.get("key", {})
            results.append(
                Entity.from_api_response(
                    {"key": key, "properties": {}}, self.project_id
                )
            )

        return results
    def delete(self, keys: List[Dict[str, Any]]) -> bool:
        """Delete entities by key.

        Args:
            keys: List of entity key dicts to delete

        Returns:
            True if the deletion was successful

        Raises:
            APIError: If the API call fails
        """
        logger.debug(
            "Deleting %d entities in project %s", len(keys), self.project_id
        )

        mutations = [{"delete": key} for key in keys]
        body = {"mutations": mutations}

        self.service.projects().commit(
            projectId=self.project_id, body=body
        ).execute()
        return True
    def allocate_ids(self, kind: str, count: int) -> List[Dict[str, Any]]:
        """Allocate IDs for incomplete keys.

        Args:
            kind: The entity kind to allocate IDs for
            count: The number of IDs to allocate

        Returns:
            A list of allocated key dicts

        Raises:
            APIError: If the API call fails
        """
        logger.debug(
            "Allocating %d IDs for kind %s in project %s",
            count,
            kind,
            self.project_id,
        )

        keys = [
            {
                "partitionId": {"projectId": self.project_id},
                "path": [{"kind": kind}],
            }
            for _ in range(count)
        ]

        body = {"keys": keys}

        request = self.service.projects().allocateIds(
            projectId=self.project_id, body=body
        )
        response = self._execute(request)
        return response.get("keys", [])
    def begin_transaction(self) -> str:
        """Begin a new transaction.

        Returns:
            The transaction identifier string

        Raises:
            APIError: If the API call fails
        """
        logger.debug("Beginning transaction in project %s", self.project_id)

        request = self.service.projects().beginTransaction(
            projectId=self.project_id, body={}
        )
        response = self._execute(request)
        return response.get("transaction", "")
    def commit(
        self,
        mutations: List[Dict[str, Any]],
        transaction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Commit mutations, optionally within a transaction.

        Args:
            mutations: List of mutation dicts (upsert, delete, insert, update)
            transaction: Optional transaction identifier

        Returns:
            The commit response dict

        Raises:
            APIError: If the API call fails
        """
        logger.debug(
            "Committing %d mutations in project %s",
            len(mutations),
            self.project_id,
        )

        body: Dict[str, Any] = {"mutations": mutations}
        if transaction is not None:
            body["transaction"] = transaction
        else:
            body["mode"] = "NON_TRANSACTIONAL"

        request = self.service.projects().commit(
            projectId=self.project_id, body=body
        )
        return self._execute(request)
    def rollback(self, transaction: str) -> bool:
        """Roll back a transaction.

        Args:
            transaction: The transaction identifier to roll back

        Returns:
            True if the rollback was successful

        Raises:
            APIError: If the API call fails
        """
        logger.debug("Rolling back transaction in project %s", self.project_id)

        body = {"transaction": transaction}

        self.service.projects().rollback(
            projectId=self.project_id, body=body
        ).execute()
        return True