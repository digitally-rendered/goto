"""Service implementation for Google Cloud Pub/Sub Lite."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.pubsub_lite import LiteTopic, LiteSubscription

logger = logging.getLogger(__name__)

class PubSubLiteService(GCPService[LiteTopic]):
    """Service for interacting with Google Cloud Pub/Sub Lite."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Pub/Sub Lite service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="pubsublite",
            version="v1/admin",
            credentials_file=credentials_file,
            resource_model=LiteTopic,
            **kwargs,
        )

    def list_topics(self, location: str) -> List[LiteTopic]:
        """List Pub/Sub Lite topics in a location.

        Args:
            location: The GCP location (e.g. 'us-central1-a')

        Returns:
            A list of LiteTopic instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        request = (
            self.service.projects()
            .locations()
            .topics()
            .list(parent=parent)
        )

        topics = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("topics", []):
                topics.append(
                    LiteTopic.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .topics()
                .list_next(request, response)
            )

        logger.debug("Listed %s topics in %s", len(topics), location)
        return topics

    def get_topic(self, location: str, topic_id: str) -> LiteTopic:
        """Get a specific Pub/Sub Lite topic.

        Args:
            location: The GCP location (e.g. 'us-central1-a')
            topic_id: The ID of the topic

        Returns:
            A LiteTopic instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/topics/{topic_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .topics()
            .get(name=name)
        )
        response = self._execute(request, "topic", topic_id)
        logger.debug("Retrieved topic %s", topic_id)
        return LiteTopic.from_api_response(response, self.project_id)

    def create_topic(
        self,
        location: str,
        topic_id: str,
        partition_config: Dict[str, Any],
        retention_config: Dict[str, Any],
        reservation_config: Optional[Dict[str, Any]] = None,
    ) -> LiteTopic:
        """Create a new Pub/Sub Lite topic.

        Args:
            location: The GCP location (e.g. 'us-central1-a')
            topic_id: The ID for the new topic
            partition_config: Partition configuration
            retention_config: Retention configuration
            reservation_config: Optional reservation configuration

        Returns:
            The created LiteTopic instance
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        body: Dict[str, Any] = {
            "partitionConfig": partition_config,
            "retentionConfig": retention_config,
        }

        if reservation_config is not None:
            body["reservationConfig"] = reservation_config

        request = (
            self.service.projects()
            .locations()
            .topics()
            .create(
                parent=parent,
                topicId=topic_id,
                body=body,
            )
        )
        response = self._execute(request)
        logger.debug("Created topic %s in %s", topic_id, location)
        return LiteTopic.from_api_response(response, self.project_id)

    def update_topic(
        self,
        location: str,
        topic_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> LiteTopic:
        """Update a Pub/Sub Lite topic.

        Args:
            location: The GCP location (e.g. 'us-central1-a')
            topic_id: The ID of the topic to update
            update_mask: Comma-separated list of fields to update
            update_fields: The fields to update

        Returns:
            The updated LiteTopic instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/topics/{topic_id}"
        )
        body = {"name": name}
        body.update(update_fields)

        request = (
            self.service.projects()
            .locations()
            .topics()
            .patch(
                name=name,
                updateMask=update_mask,
                body=body,
            )
        )
        response = self._execute(request, "topic", topic_id)
        logger.debug("Updated topic %s", topic_id)
        return LiteTopic.from_api_response(response, self.project_id)

    def delete_topic(self, location: str, topic_id: str) -> bool:
        """Delete a Pub/Sub Lite topic.

        Args:
            location: The GCP location (e.g. 'us-central1-a')
            topic_id: The ID of the topic to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/topics/{topic_id}"
        )
        request = self.service.projects().locations().topics().delete(
            name=name
        )
        self._execute(request)
        logger.debug("Deleted topic %s", topic_id)
        return True

    def list_subscriptions(
        self, location: str
    ) -> List[LiteSubscription]:
        """List Pub/Sub Lite subscriptions in a location.

        Args:
            location: The GCP location (e.g. 'us-central1-a')

        Returns:
            A list of LiteSubscription instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        request = (
            self.service.projects()
            .locations()
            .subscriptions()
            .list(parent=parent)
        )

        subscriptions = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("subscriptions", []):
                subscriptions.append(
                    LiteSubscription.from_api_response(
                        item, self.project_id
                    )
                )
            request = (
                self.service.projects()
                .locations()
                .subscriptions()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s subscriptions in %s", len(subscriptions), location
        )
        return subscriptions

    def get_subscription(
        self, location: str, subscription_id: str
    ) -> LiteSubscription:
        """Get a specific Pub/Sub Lite subscription.

        Args:
            location: The GCP location (e.g. 'us-central1-a')
            subscription_id: The ID of the subscription

        Returns:
            A LiteSubscription instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/subscriptions/{subscription_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .subscriptions()
            .get(name=name)
        )
        response = self._execute(request, "subscription", subscription_id)
        logger.debug("Retrieved subscription %s", subscription_id)
        return LiteSubscription.from_api_response(
            response, self.project_id
        )

    def create_subscription(
        self,
        location: str,
        subscription_id: str,
        topic: str,
        delivery_config: Optional[Dict[str, Any]] = None,
    ) -> LiteSubscription:
        """Create a new Pub/Sub Lite subscription.

        Args:
            location: The GCP location (e.g. 'us-central1-a')
            subscription_id: The ID for the new subscription
            topic: The full resource name of the topic to subscribe to
            delivery_config: Optional delivery configuration

        Returns:
            The created LiteSubscription instance
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        body: Dict[str, Any] = {"topic": topic}

        if delivery_config is not None:
            body["deliveryConfig"] = delivery_config

        request = (
            self.service.projects()
            .locations()
            .subscriptions()
            .create(
                parent=parent,
                subscriptionId=subscription_id,
                body=body,
            )
        )
        response = self._execute(request)
        logger.debug(
            "Created subscription %s in %s", subscription_id, location
        )
        return LiteSubscription.from_api_response(
            response, self.project_id
        )

    def update_subscription(
        self,
        location: str,
        subscription_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> LiteSubscription:
        """Update a Pub/Sub Lite subscription.

        Args:
            location: The GCP location (e.g. 'us-central1-a')
            subscription_id: The ID of the subscription to update
            update_mask: Comma-separated list of fields to update
            update_fields: The fields to update

        Returns:
            The updated LiteSubscription instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/subscriptions/{subscription_id}"
        )
        body = {"name": name}
        body.update(update_fields)

        request = (
            self.service.projects()
            .locations()
            .subscriptions()
            .patch(
                name=name,
                updateMask=update_mask,
                body=body,
            )
        )
        response = self._execute(request, "subscription", subscription_id)
        logger.debug("Updated subscription %s", subscription_id)
        return LiteSubscription.from_api_response(
            response, self.project_id
        )

    def delete_subscription(
        self, location: str, subscription_id: str
    ) -> bool:
        """Delete a Pub/Sub Lite subscription.

        Args:
            location: The GCP location (e.g. 'us-central1-a')
            subscription_id: The ID of the subscription to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/subscriptions/{subscription_id}"
        )
        request = self.service.projects().locations().subscriptions().delete(
            name=name
        )
        self._execute(request)
        logger.debug("Deleted subscription %s", subscription_id)
        return True
