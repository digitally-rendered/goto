"""Service implementation for Google Cloud SQL."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.cloud_sql import SQLInstance, SQLDatabase, SQLUser, SQLBackupRun
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
)

logger = logging.getLogger(__name__)


class CloudSQLService(GCPService[SQLInstance]):
    """Service for interacting with Google Cloud SQL."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
    ):
        """Initialize the Cloud SQL service.

        Args:
            project_id: The GCP project ID
            credentials_file: Path to service account credentials file
        """
        super().__init__(
            project_id=project_id,
            service_name="sqladmin",
            version="v1",
            credentials_file=credentials_file,
            resource_model=SQLInstance,
        )

    # --- Instance methods ---

    def list_instances(self, **kwargs) -> List[SQLInstance]:
        """List Cloud SQL instances in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of SQLInstance instances
        """
        try:
            request = self.service.instances().list(
                project=self.project_id, **kwargs
            )
            response = request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e))
        return [
            SQLInstance.from_api_response(item)
            for item in response.get("items", [])
        ]

    def get_instance(self, instance_name: str) -> SQLInstance:
        """Get a specific Cloud SQL instance by name.

        Args:
            instance_name: The name of the instance to retrieve

        Returns:
            An SQLInstance instance
        """
        try:
            request = self.service.instances().get(
                project=self.project_id, instance=instance_name
            )
            response = request.execute()
            return SQLInstance.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SQLInstance", instance_name)
            raise APIError(e.resp.status, str(e))

    def create_instance(
        self,
        instance_name: str,
        database_version: str,
        tier: str,
        region: str,
        settings: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> SQLInstance:
        """Create a new Cloud SQL instance.

        Args:
            instance_name: The name for the new instance
            database_version: The database version (e.g. MYSQL_8_0, POSTGRES_15)
            tier: The machine tier (e.g. db-n1-standard-1)
            region: The GCP region for the instance
            settings: Additional settings for the instance
            labels: Labels to apply to the instance

        Returns:
            The created SQLInstance
        """
        body = {
            "name": instance_name,
            "databaseVersion": database_version,
            "region": region,
            "settings": {
                "tier": tier,
                **(settings or {}),
            },
        }

        if labels:
            body["settings"]["userLabels"] = labels

        try:
            request = self.service.instances().insert(
                project=self.project_id, body=body
            )
            response = request.execute()
            return SQLInstance.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"SQLInstance '{instance_name}' already exists"
                )
            raise APIError(e.resp.status, str(e))

    def delete_instance(self, instance_name: str) -> bool:
        """Delete a Cloud SQL instance.

        Args:
            instance_name: The name of the instance to delete

        Returns:
            True if the deletion was successful
        """
        try:
            request = self.service.instances().delete(
                project=self.project_id, instance=instance_name
            )
            request.execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SQLInstance", instance_name)
            raise APIError(e.resp.status, str(e))

    def restart_instance(self, instance_name: str) -> Dict:
        """Restart a Cloud SQL instance.

        Args:
            instance_name: The name of the instance to restart

        Returns:
            The operation response dictionary
        """
        try:
            request = self.service.instances().restart(
                project=self.project_id, instance=instance_name
            )
            return request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SQLInstance", instance_name)
            raise APIError(e.resp.status, str(e))

    # --- Database methods ---

    def list_databases(self, instance_name: str) -> List[SQLDatabase]:
        """List databases in a Cloud SQL instance.

        Args:
            instance_name: The name of the instance

        Returns:
            A list of SQLDatabase instances
        """
        try:
            request = self.service.databases().list(
                project=self.project_id, instance=instance_name
            )
            response = request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e))
        return [
            SQLDatabase.from_api_response(item)
            for item in response.get("items", [])
        ]

    def get_database(
        self, instance_name: str, database_name: str
    ) -> SQLDatabase:
        """Get a specific database by name.

        Args:
            instance_name: The name of the instance
            database_name: The name of the database

        Returns:
            An SQLDatabase instance
        """
        try:
            request = self.service.databases().get(
                project=self.project_id,
                instance=instance_name,
                database=database_name,
            )
            response = request.execute()
            return SQLDatabase.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SQLDatabase", database_name)
            raise APIError(e.resp.status, str(e))

    def create_database(
        self,
        instance_name: str,
        database_name: str,
        charset: str = "UTF8",
        collation: str = "",
    ) -> SQLDatabase:
        """Create a new database in a Cloud SQL instance.

        Args:
            instance_name: The name of the instance
            database_name: The name for the new database
            charset: The character set (default UTF8)
            collation: The collation for the database

        Returns:
            The created SQLDatabase
        """
        body = {
            "name": database_name,
            "instance": instance_name,
            "charset": charset,
            "collation": collation,
        }

        try:
            request = self.service.databases().insert(
                project=self.project_id, instance=instance_name, body=body
            )
            response = request.execute()
            return SQLDatabase.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"SQLDatabase '{database_name}' already exists"
                )
            raise APIError(e.resp.status, str(e))

    def delete_database(
        self, instance_name: str, database_name: str
    ) -> bool:
        """Delete a database from a Cloud SQL instance.

        Args:
            instance_name: The name of the instance
            database_name: The name of the database to delete

        Returns:
            True if the deletion was successful
        """
        try:
            request = self.service.databases().delete(
                project=self.project_id,
                instance=instance_name,
                database=database_name,
            )
            request.execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SQLDatabase", database_name)
            raise APIError(e.resp.status, str(e))

    # --- User methods ---

    def list_users(self, instance_name: str) -> List[SQLUser]:
        """List users in a Cloud SQL instance.

        Args:
            instance_name: The name of the instance

        Returns:
            A list of SQLUser instances
        """
        try:
            request = self.service.users().list(
                project=self.project_id, instance=instance_name
            )
            response = request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e))
        return [
            SQLUser.from_api_response(item)
            for item in response.get("items", [])
        ]

    def create_user(
        self,
        instance_name: str,
        username: str,
        password: str,
        host: str = "%",
    ) -> SQLUser:
        """Create a new user in a Cloud SQL instance.

        Args:
            instance_name: The name of the instance
            username: The username for the new user
            password: The password for the new user
            host: The host from which the user can connect (default %)

        Returns:
            The created SQLUser
        """
        body = {
            "name": username,
            "instance": instance_name,
            "password": password,
            "host": host,
        }

        try:
            request = self.service.users().insert(
                project=self.project_id, instance=instance_name, body=body
            )
            response = request.execute()
            return SQLUser.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"SQLUser '{username}' already exists"
                )
            raise APIError(e.resp.status, str(e))

    def delete_user(
        self,
        instance_name: str,
        username: str,
        host: str = "%",
    ) -> bool:
        """Delete a user from a Cloud SQL instance.

        Args:
            instance_name: The name of the instance
            username: The username to delete
            host: The host of the user to delete (default %)

        Returns:
            True if the deletion was successful
        """
        try:
            request = self.service.users().delete(
                project=self.project_id,
                instance=instance_name,
                name=username,
                host=host,
            )
            request.execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("SQLUser", username)
            raise APIError(e.resp.status, str(e))

    # --- Backup methods ---

    def list_backup_runs(self, instance_name: str) -> List[SQLBackupRun]:
        """List backup runs for a Cloud SQL instance.

        Args:
            instance_name: The name of the instance

        Returns:
            A list of SQLBackupRun instances
        """
        try:
            request = self.service.backupRuns().list(
                project=self.project_id, instance=instance_name
            )
            response = request.execute()
        except HttpError as e:
            raise APIError(e.resp.status, str(e))
        return [
            SQLBackupRun.from_api_response(item)
            for item in response.get("items", [])
        ]
