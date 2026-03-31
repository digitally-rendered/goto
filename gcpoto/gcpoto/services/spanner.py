"""Service implementation for Google Cloud Spanner."""

import logging
from typing import List, Optional, Dict, Any

from gcpoto.services.base import GCPService
from gcpoto.models.spanner import SpannerInstance, SpannerDatabase

logger = logging.getLogger(__name__)

class SpannerService(GCPService[SpannerInstance]):
    """Service for interacting with Google Cloud Spanner."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the Spanner service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="spanner",
            version="v1",
            credentials_file=credentials_file,
            resource_model=SpannerInstance,
        )

    def _instance_path(self, instance_id: str) -> str:
        """Format a full instance resource path.

        Args:
            instance_id: The instance ID

        Returns:
            The fully-qualified instance path
        """
        return f"projects/{self.project_id}/instances/{instance_id}"

    def _database_path(self, instance_id: str, database_name: str) -> str:
        """Format a full database resource path.

        Args:
            instance_id: The instance ID
            database_name: The database name

        Returns:
            The fully-qualified database path
        """
        return (
            f"projects/{self.project_id}/instances/{instance_id}"
            f"/databases/{database_name}"
        )

    # --- Instance methods ---

    def list_instances(self, **kwargs) -> List[SpannerInstance]:
        """List Spanner instances in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of SpannerInstance instances
        """
        parent = f"projects/{self.project_id}"
        logger.debug("Listing Spanner instances in %s", parent)
        all_instances = []
        request = self.service.projects().instances().list(
            parent=parent, **kwargs
        )
        while request is not None:
            response = self._execute(request)
            instances = response.get("instances", [])
            all_instances.extend(
                SpannerInstance.from_api_response(item) for item in instances
            )
            request = (
                self.service.projects()
                .instances()
                .list_next(request, response)
            )
        return all_instances

    def get_instance(self, instance_id: str) -> SpannerInstance:
        """Get a specific Spanner instance by ID.

        Args:
            instance_id: The instance ID

        Returns:
            A SpannerInstance instance
        """
        name = self._instance_path(instance_id)
        logger.debug("Getting Spanner instance %s", name)
        request = self.service.projects().instances().get(name=name)
        response = self._execute(request)
        return SpannerInstance.from_api_response(response)

    def create_instance(
        self,
        instance_id: str,
        display_name: str,
        config: str,
        node_count: int = 1,
        processing_units: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> SpannerInstance:
        """Create a new Spanner instance.

        Args:
            instance_id: The ID for the new instance
            display_name: A descriptive name for the instance
            config: The instance configuration
                (e.g. projects/{project}/instanceConfigs/regional-us-central1)
            node_count: The number of nodes (default 1)
            processing_units: The number of processing units (overrides node_count)
            labels: Labels to apply to the instance

        Returns:
            The created SpannerInstance
        """
        parent = f"projects/{self.project_id}"
        logger.info(
            "Creating Spanner instance %s in %s", instance_id, parent
        )

        body = {
            "instanceId": instance_id,
            "instance": {
                "displayName": display_name,
                "config": config,
                "nodeCount": node_count,
            },
        }

        if processing_units is not None:
            body["instance"]["processingUnits"] = processing_units
            # When processing_units is set, remove nodeCount
            body["instance"].pop("nodeCount", None)

        if labels:
            body["instance"]["labels"] = labels

        request = self.service.projects().instances().create(
            parent=parent, body=body
        )
        response = self._execute(request)
        return SpannerInstance.from_api_response(response)

    def update_instance(
        self,
        instance_id: str,
        display_name: Optional[str] = None,
        node_count: Optional[int] = None,
        processing_units: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> SpannerInstance:
        """Update an existing Spanner instance.

        Args:
            instance_id: The ID of the instance to update
            display_name: New display name for the instance
            node_count: New number of nodes
            processing_units: New number of processing units
            labels: New labels for the instance

        Returns:
            The updated SpannerInstance
        """
        name = self._instance_path(instance_id)
        logger.info("Updating Spanner instance %s", name)

        instance_body = {"name": name}
        field_mask_paths = []

        if display_name is not None:
            instance_body["displayName"] = display_name
            field_mask_paths.append("displayName")

        if node_count is not None:
            instance_body["nodeCount"] = node_count
            field_mask_paths.append("nodeCount")

        if processing_units is not None:
            instance_body["processingUnits"] = processing_units
            field_mask_paths.append("processingUnits")

        if labels is not None:
            instance_body["labels"] = labels
            field_mask_paths.append("labels")

        body = {
            "instance": instance_body,
            "fieldMask": ",".join(field_mask_paths),
        }

        request = self.service.projects().instances().patch(
            name=name, body=body
        )
        response = self._execute(request)
        return SpannerInstance.from_api_response(response)

    def delete_instance(self, instance_id: str) -> bool:
        """Delete a Spanner instance.

        Args:
            instance_id: The ID of the instance to delete

        Returns:
            True if the deletion was successful
        """
        name = self._instance_path(instance_id)
        logger.info("Deleting Spanner instance %s", name)
        request = self.service.projects().instances().delete(name=name)
        self._execute(request)
        return True

    # --- Database methods ---

    def list_databases(self, instance_id: str) -> List[SpannerDatabase]:
        """List databases in a Spanner instance.

        Args:
            instance_id: The instance ID

        Returns:
            A list of SpannerDatabase instances
        """
        parent = self._instance_path(instance_id)
        logger.debug("Listing databases in Spanner instance %s", parent)
        all_databases = []
        request = (
            self.service.projects()
            .instances()
            .databases()
            .list(parent=parent)
        )
        while request is not None:
            response = self._execute(request)
            databases = response.get("databases", [])
            all_databases.extend(
                SpannerDatabase.from_api_response(item) for item in databases
            )
            request = (
                self.service.projects()
                .instances()
                .databases()
                .list_next(request, response)
            )
        return all_databases

    def get_database(
        self, instance_id: str, database_name: str
    ) -> SpannerDatabase:
        """Get a specific database by name.

        Args:
            instance_id: The instance ID
            database_name: The name of the database

        Returns:
            A SpannerDatabase instance
        """
        name = self._database_path(instance_id, database_name)
        logger.debug("Getting Spanner database %s", name)
        request = (
            self.service.projects()
            .instances()
            .databases()
            .get(name=name)
        )
        response = self._execute(request)
        return SpannerDatabase.from_api_response(response)

    def create_database(
        self,
        instance_id: str,
        database_name: str,
        extra_statements: Optional[List[str]] = None,
    ) -> SpannerDatabase:
        """Create a new database in a Spanner instance.

        Args:
            instance_id: The instance ID
            database_name: The name for the new database
            extra_statements: Additional DDL statements to execute after
                creating the database

        Returns:
            The created SpannerDatabase
        """
        parent = self._instance_path(instance_id)
        logger.info(
            "Creating database %s in Spanner instance %s",
            database_name,
            parent,
        )

        body = {
            "createStatement": f"CREATE DATABASE `{database_name}`",
        }
        if extra_statements:
            body["extraStatements"] = extra_statements

        request = (
            self.service.projects()
            .instances()
            .databases()
            .create(parent=parent, body=body)
        )
        response = self._execute(request)
        return SpannerDatabase.from_api_response(response)

    def drop_database(
        self, instance_id: str, database_name: str
    ) -> bool:
        """Drop a database from a Spanner instance.

        Args:
            instance_id: The instance ID
            database_name: The name of the database to drop

        Returns:
            True if the deletion was successful
        """
        name = self._database_path(instance_id, database_name)
        logger.info("Dropping Spanner database %s", name)
        request = (
            self.service.projects()
            .instances()
            .databases()
            .dropDatabase(database=name)
        )
        self._execute(request)
        return True

    def get_database_ddl(
        self, instance_id: str, database_name: str
    ) -> List[str]:
        """Get the DDL statements for a database.

        Args:
            instance_id: The instance ID
            database_name: The name of the database

        Returns:
            A list of DDL statements
        """
        name = self._database_path(instance_id, database_name)
        logger.debug("Getting DDL for Spanner database %s", name)
        request = (
            self.service.projects()
            .instances()
            .databases()
            .getDdl(database=name)
        )
        response = self._execute(request)
        return response.get("statements", [])

    def update_database_ddl(
        self,
        instance_id: str,
        database_name: str,
        statements: List[str],
    ) -> Dict[str, Any]:
        """Update the DDL for a database.

        Args:
            instance_id: The instance ID
            database_name: The name of the database
            statements: The DDL statements to execute

        Returns:
            The operation response dictionary
        """
        name = self._database_path(instance_id, database_name)
        logger.info("Updating DDL for Spanner database %s", name)

        body = {
            "statements": statements,
        }

        request = (
            self.service.projects()
            .instances()
            .databases()
            .updateDdl(database=name, body=body)
        )
        return request.execute()

    def execute_sql(
        self,
        instance_id: str,
        database_name: str,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a SQL statement against a Spanner database.

        This creates a single-use read-only transaction for queries,
        or a read-write transaction for DML statements.

        Args:
            instance_id: The instance ID
            database_name: The name of the database
            sql: The SQL statement to execute
            params: Optional parameters for the SQL statement

        Returns:
            The query result as a dictionary
        """
        session_name = self._database_path(instance_id, database_name)
        logger.debug(
            "Executing SQL on Spanner database %s", session_name
        )

        # Create a session
        create_request = (
            self.service.projects()
            .instances()
            .databases()
            .sessions()
            .create(database=session_name, body={})
        )
        session = self._execute(create_request)
        session_path = session["name"]

        try:
            # Execute SQL using the session
            body = {
                "sql": sql,
                "transaction": {
                    "singleUse": {"readOnly": {"strong": True}},
                },
            }

            if params:
                body["params"] = params

            sql_request = (
                self.service.projects()
                .instances()
                .databases()
                .sessions()
                .executeSql(session=session_path, body=body)
            )
            return sql_request.execute()
        finally:
            # Clean up the session
            try:
                self.service.projects().instances().databases().sessions().delete(
                    name=session_path
                ).execute()
            except Exception:
                logger.warning(
                    "Failed to delete session %s", session_path
                )
