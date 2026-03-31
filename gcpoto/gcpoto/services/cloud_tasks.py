"""Service implementation for Google Cloud Tasks."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.cloud_tasks import TaskQueue, Task
from gcpoto.exceptions import (
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class CloudTasksService(GCPService[TaskQueue]):
    """Service for interacting with Google Cloud Tasks."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Tasks service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="cloudtasks",
            version="v2",
            credentials_file=credentials_file,
            resource_model=TaskQueue,
            **kwargs,
        )

    def _format_queue_path(self, location: str, queue_name: str) -> str:
        """Format a fully qualified queue path.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The queue name or full path

        Returns:
            The fully qualified queue resource path
        """
        if "/" in queue_name:
            return queue_name
        return (
            f"projects/{self.project_id}/locations/{location}"
            f"/queues/{queue_name}"
        )

    def _format_task_path(
        self, location: str, queue_name: str, task_name: str
    ) -> str:
        """Format a fully qualified task path.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The queue name
            task_name: The task name or full path

        Returns:
            The fully qualified task resource path
        """
        if "/" in task_name:
            return task_name
        queue_path = self._format_queue_path(location, queue_name)
        return f"{queue_path}/tasks/{task_name}"

    def _format_location_path(self, location: str) -> str:
        """Format a fully qualified location path.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            The fully qualified location resource path
        """
        return f"projects/{self.project_id}/locations/{location}"

    def list_queues(self, location: str, **kwargs) -> List[TaskQueue]:
        """List Cloud Tasks queues in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of TaskQueue instances
        """
        parent = self._format_location_path(location)

        request = (
            self.service.projects()
            .locations()
            .queues()
            .list(parent=parent, **kwargs)
        )

        queues = []
        while request is not None:
            response = request.execute()
            for queue_data in response.get("queues", []):
                queues.append(
                    TaskQueue.from_api_response(queue_data, self.project_id)
                )

            request = (
                self.service.projects()
                .locations()
                .queues()
                .list_next(request, response)
            )

        logger.debug("Listed %s queues in %s", len(queues), location)
        return queues

    def get_queue(self, location: str, queue_name: str) -> TaskQueue:
        """Get a specific Cloud Tasks queue.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue to retrieve

        Returns:
            A TaskQueue instance
        """
        name = self._format_queue_path(location, queue_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .queues()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("queue", queue_name)
            raise

        logger.debug("Retrieved queue %s", queue_name)
        return TaskQueue.from_api_response(response, self.project_id)

    def create_queue(
        self,
        location: str,
        queue_name: str,
        rate_limits: Optional[Dict[str, Any]] = None,
        retry_config: Optional[Dict[str, Any]] = None,
    ) -> TaskQueue:
        """Create a new Cloud Tasks queue.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue to create
            rate_limits: Optional rate limits configuration
            retry_config: Optional retry configuration

        Returns:
            A TaskQueue instance for the newly created queue
        """
        parent = self._format_location_path(location)
        queue_path = self._format_queue_path(location, queue_name)

        body = {"name": queue_path}

        if rate_limits is not None:
            body["rateLimits"] = rate_limits

        if retry_config is not None:
            body["retryConfig"] = retry_config

        try:
            request = (
                self.service.projects()
                .locations()
                .queues()
                .create(parent=parent, body=body)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"Queue '{queue_name}' already exists"
                )
            raise

        logger.debug("Created queue %s in %s", queue_name, location)
        return TaskQueue.from_api_response(response, self.project_id)

    def update_queue(
        self,
        location: str,
        queue_name: str,
        update_fields: Dict[str, Any],
    ) -> TaskQueue:
        """Update an existing Cloud Tasks queue.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue to update
            update_fields: Dictionary of fields to update

        Returns:
            The updated TaskQueue instance
        """
        name = self._format_queue_path(location, queue_name)

        body = {"name": name}
        body.update(update_fields)

        update_mask = ",".join(update_fields.keys())

        try:
            request = (
                self.service.projects()
                .locations()
                .queues()
                .patch(name=name, body=body, updateMask=update_mask)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("queue", queue_name)
            raise

        logger.debug("Updated queue %s in %s", queue_name, location)
        return TaskQueue.from_api_response(response, self.project_id)

    def delete_queue(self, location: str, queue_name: str) -> bool:
        """Delete a Cloud Tasks queue.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue to delete

        Returns:
            True if the deletion was successful
        """
        name = self._format_queue_path(location, queue_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .queues()
                .delete(name=name)
            )
            request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("queue", queue_name)
            raise

        logger.debug("Deleted queue %s in %s", queue_name, location)
        return True

    def pause_queue(self, location: str, queue_name: str) -> TaskQueue:
        """Pause a Cloud Tasks queue.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue to pause

        Returns:
            The paused TaskQueue instance
        """
        name = self._format_queue_path(location, queue_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .queues()
                .pause(name=name, body={})
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("queue", queue_name)
            raise

        logger.debug("Paused queue %s in %s", queue_name, location)
        return TaskQueue.from_api_response(response, self.project_id)

    def resume_queue(self, location: str, queue_name: str) -> TaskQueue:
        """Resume a paused Cloud Tasks queue.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue to resume

        Returns:
            The resumed TaskQueue instance
        """
        name = self._format_queue_path(location, queue_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .queues()
                .resume(name=name, body={})
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("queue", queue_name)
            raise

        logger.debug("Resumed queue %s in %s", queue_name, location)
        return TaskQueue.from_api_response(response, self.project_id)

    def purge_queue(self, location: str, queue_name: str) -> TaskQueue:
        """Purge all tasks from a Cloud Tasks queue.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue to purge

        Returns:
            The purged TaskQueue instance
        """
        name = self._format_queue_path(location, queue_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .queues()
                .purge(name=name, body={})
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("queue", queue_name)
            raise

        logger.debug("Purged queue %s in %s", queue_name, location)
        return TaskQueue.from_api_response(response, self.project_id)

    def list_tasks(
        self, location: str, queue_name: str, **kwargs
    ) -> List[Task]:
        """List tasks in a Cloud Tasks queue.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue to list tasks from
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of Task instances
        """
        parent = self._format_queue_path(location, queue_name)

        request = (
            self.service.projects()
            .locations()
            .queues()
            .tasks()
            .list(parent=parent, **kwargs)
        )

        tasks = []
        while request is not None:
            response = request.execute()
            for task_data in response.get("tasks", []):
                tasks.append(
                    Task.from_api_response(task_data, self.project_id)
                )

            request = (
                self.service.projects()
                .locations()
                .queues()
                .tasks()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s tasks in queue %s", len(tasks), queue_name
        )
        return tasks

    def get_task(
        self, location: str, queue_name: str, task_name: str
    ) -> Task:
        """Get a specific task from a Cloud Tasks queue.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue
            task_name: The name of the task to retrieve

        Returns:
            A Task instance
        """
        name = self._format_task_path(location, queue_name, task_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .queues()
                .tasks()
                .get(name=name)
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("task", task_name)
            raise

        logger.debug("Retrieved task %s from queue %s", task_name, queue_name)
        return Task.from_api_response(response, self.project_id)

    def create_task(
        self,
        location: str,
        queue_name: str,
        http_request: Optional[Dict[str, Any]] = None,
        schedule_time: Optional[str] = None,
    ) -> Task:
        """Create a new task in a Cloud Tasks queue.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue to create the task in
            http_request: Optional HTTP request configuration for the task
            schedule_time: Optional schedule time for the task (RFC3339 format)

        Returns:
            A Task instance for the newly created task
        """
        parent = self._format_queue_path(location, queue_name)

        task_body: Dict[str, Any] = {}

        if http_request is not None:
            task_body["httpRequest"] = http_request

        if schedule_time is not None:
            task_body["scheduleTime"] = schedule_time

        body = {"task": task_body}

        request = (
            self.service.projects()
            .locations()
            .queues()
            .tasks()
            .create(parent=parent, body=body)
        )
        response = request.execute()

        logger.debug("Created task in queue %s", queue_name)
        return Task.from_api_response(response, self.project_id)

    def delete_task(
        self, location: str, queue_name: str, task_name: str
    ) -> bool:
        """Delete a task from a Cloud Tasks queue.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue
            task_name: The name of the task to delete

        Returns:
            True if the deletion was successful
        """
        name = self._format_task_path(location, queue_name, task_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .queues()
                .tasks()
                .delete(name=name)
            )
            request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("task", task_name)
            raise

        logger.debug(
            "Deleted task %s from queue %s", task_name, queue_name
        )
        return True

    def run_task(
        self, location: str, queue_name: str, task_name: str
    ) -> Task:
        """Force run a task immediately.

        Args:
            location: The GCP location (e.g. 'us-central1')
            queue_name: The name of the queue
            task_name: The name of the task to run

        Returns:
            A Task instance for the run task
        """
        name = self._format_task_path(location, queue_name, task_name)

        try:
            request = (
                self.service.projects()
                .locations()
                .queues()
                .tasks()
                .run(name=name, body={})
            )
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("task", task_name)
            raise

        logger.debug(
            "Ran task %s in queue %s", task_name, queue_name
        )
        return Task.from_api_response(response, self.project_id)
