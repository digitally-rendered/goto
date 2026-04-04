"""Service implementation for Google Cloud Pub/Sub."""

from typing import List, Optional, Dict, Any, Union

from google.cloud import pubsub_v1
from google.oauth2 import service_account

from gcpoto.services.base import GCPService
from gcpoto.models.pubsub import PubSubTopic, PubSubSubscription

from gcpoto.utils import format_topic_path, format_subscription_path, extract_name_from_path

class PubSubService(GCPService[PubSubTopic]):
    """Service for interacting with Google Cloud Pub/Sub."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        credentials: Optional[Any] = None,
        **kwargs,
    ):
        """Initialize the Pub/Sub service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            credentials: Optional credentials object to use instead of a file
            **kwargs: Additional arguments to pass to the service constructor
        """
        # Pass service-specific parameters to the base class
        super().__init__(
            project_id=project_id,
            service_name="pubsub",
            credentials_file=credentials_file,
            resource_model=PubSubTopic,
            **kwargs,
        )

        # Initialize the Google Cloud Pub/Sub clients
        # Get credentials instance for publisher/subscriber
        pub_credentials = None
        if credentials_file:
            pub_credentials = service_account.Credentials.from_service_account_file(
                credentials_file, scopes=["https://www.googleapis.com/auth/pubsub"]
            )
        elif credentials:
            pub_credentials = credentials

        self.publisher = pubsub_v1.PublisherClient(credentials=pub_credentials)
        self.subscriber = pubsub_v1.SubscriberClient(credentials=pub_credentials)

    def list_resources(self, **kwargs) -> List[PubSubTopic]:
        """List Pub/Sub topics in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of PubSubTopic instances
        """
        request = (
            self.service.projects()
            .topics()
            .list(project=f"projects/{self.project_id}", **kwargs)
        )

        topics = []
        while request is not None:
            response = self._execute(request)
            for topic_data in response.get("topics", []):
                topics.append(
                    PubSubTopic.from_api_response(topic_data, self.project_id)
                )

            # Get the next page of results
            request = self.service.projects().topics().list_next(request, response)

        return topics

    def get_topic(self, topic_name: str) -> PubSubTopic:
        """Get a specific Pub/Sub topic by name.

        Args:
            topic_name: The name of the topic to retrieve

        Returns:
            A PubSubTopic instance
        """
        full_topic_path = format_topic_path(self.project_id, topic_name)

        request = self.service.projects().topics().get(topic=full_topic_path)
        response = self._execute(request)

        return PubSubTopic.from_api_response(response, self.project_id)

    def create_topic(
        self,
        topic_name: str,
        labels: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
        kms_key_name: Optional[str] = None,
        message_storage_policy: Optional[Dict[str, List[str]]] = None,
        schema_settings: Optional[Dict[str, str]] = None,
        message_retention_duration: Optional[str] = None,
        **kwargs,
    ) -> PubSubTopic:
        """Create a new Pub/Sub topic.

        Args:
            topic_name: The name of the topic to create
            labels: Optional labels to apply to the topic
            tags: Optional tags to apply to the topic
            kms_key_name: Optional KMS key to use for message protection
            message_storage_policy: Optional policy for where messages can be stored
            schema_settings: Optional schema validation settings
            message_retention_duration: Optional message retention duration
            **kwargs: Additional parameters to pass to the create request

        Returns:
            A PubSubTopic instance for the newly created topic
        """
        full_topic_path = format_topic_path(self.project_id, topic_name)
        # Extract the short name for error messages
        topic_name = extract_name_from_path(full_topic_path)

        # Prepare the request body
        body = {}

        if labels:
            body["labels"] = labels

        # Process tags (will be added to labels for Pub/Sub)
        body = self._process_tags(body, tags)

        if kms_key_name:
            body["kmsKeyName"] = kms_key_name

        if message_storage_policy:
            body["messageStoragePolicy"] = message_storage_policy

        if schema_settings:
            body["schemaSettings"] = schema_settings

        if message_retention_duration:
            body["messageRetentionDuration"] = message_retention_duration

        # Add any additional kwargs to the body
        for key, value in kwargs.items():
            if key not in ["topic"]:
                body[key] = value

        request = (
            self.service.projects().topics().create(name=full_topic_path, body=body)
        )
        response = self._execute(request)

        # Create the topic object and add the tags explicitly
        topic = PubSubTopic.from_api_response(response, self.project_id)
        if tags:
            topic.tags = tags
        return topic
    def delete_topic(self, topic_name: str) -> bool:
        """Delete a Pub/Sub topic.

        Args:
            topic_name: The name of the topic to delete

        Returns:
            True if the deletion was successful
        """
        full_topic_path = format_topic_path(self.project_id, topic_name)

        request = self.service.projects().topics().delete(topic=full_topic_path)
        self._execute(request)

        return True

    def publish_message(
        self,
        topic_name: str,
        data: Union[str, bytes],
        attributes: Optional[Dict[str, str]] = None,
    ) -> str:
        """Publish a message to a Pub/Sub topic.

        Args:
            topic_name: The name of the topic to publish to
            data: The message data to publish (string or bytes)
            attributes: Optional attributes to include with the message

        Returns:
            The published message ID
        """
        full_topic_path = format_topic_path(self.project_id, topic_name)

        # Convert string data to bytes if needed
        if isinstance(data, str):
            data = data.encode("utf-8")

        # Publish the message
        future = self.publisher.publish(full_topic_path, data, **(attributes or {}))
        message_id = future.result()

        return message_id

    def list_subscriptions(
        self, topic_name: Optional[str] = None, **kwargs
    ) -> List[PubSubSubscription]:
        """List Pub/Sub subscriptions in the project, optionally filtered by topic.

        Args:
            topic_name: Optional topic name to filter subscriptions by
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of PubSubSubscription instances
        """
        if topic_name:
            full_topic_path = format_topic_path(self.project_id, topic_name)

            request = (
                self.service.projects()
                .topics()
                .subscriptions()
                .list(topic=full_topic_path, **kwargs)
            )
        else:
            request = (
                self.service.projects()
                .subscriptions()
                .list(project=f"projects/{self.project_id}", **kwargs)
            )

        subscriptions = []

        while request is not None:
            response = self._execute(request)

            # The response format differs depending on whether we list by topic or by project
            if topic_name:
                # For topic subscriptions, the response contains just subscription names
                for subscription_path in response.get("subscriptions", []):
                    # Get the full subscription details
                    sub_request = (
                        self.service.projects()
                        .subscriptions()
                        .get(subscription=subscription_path)
                    )
                    sub_response = self._execute(sub_request)
                    subscriptions.append(
                        PubSubSubscription.from_api_response(
                            sub_response, self.project_id
                        )
                    )
            else:
                # For project subscriptions, the response contains the full subscription details
                for subscription_data in response.get("subscriptions", []):
                    subscriptions.append(
                        PubSubSubscription.from_api_response(
                            subscription_data, self.project_id
                        )
                    )

            # Get the next page of results
            if topic_name:
                request = (
                    self.service.projects()
                    .topics()
                    .subscriptions()
                    .list_next(request, response)
                )
            else:
                request = (
                    self.service.projects().subscriptions().list_next(request, response)
                )

        return subscriptions

    def get_subscription(self, subscription_name: str) -> PubSubSubscription:
        """Get a specific Pub/Sub subscription by name.

        Args:
            subscription_name: The name of the subscription to retrieve

        Returns:
            A PubSubSubscription instance
        """
        full_subscription_path = format_subscription_path(self.project_id, subscription_name)

        request = (
            self.service.projects()
            .subscriptions()
            .get(subscription=full_subscription_path)
        )
        response = self._execute(request)

        return PubSubSubscription.from_api_response(response, self.project_id)

    def create_subscription(
        self,
        subscription_name: str,
        topic_name: str,
        ack_deadline_seconds: Optional[int] = None,
        push_config: Optional[Dict[str, Any]] = None,
        retain_acked_messages: Optional[bool] = None,
        message_retention_duration: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
        enable_message_ordering: Optional[bool] = None,
        expiration_policy: Optional[Dict[str, str]] = None,
        filter_expr: Optional[str] = None,
        dead_letter_policy: Optional[Dict[str, Any]] = None,
        retry_policy: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> PubSubSubscription:
        """Create a new Pub/Sub subscription.

        Args:
            subscription_name: The name of the subscription to create
            topic_name: The name of the topic the subscription is for
            ack_deadline_seconds: Optional acknowledgement deadline in seconds
            push_config: Optional push delivery configuration
            retain_acked_messages: Optional flag to retain acknowledged messages
            message_retention_duration: Optional retention duration for unacknowledged messages
            labels: Optional labels to apply to the subscription
            tags: Optional tags to apply to the subscription
            enable_message_ordering: Optional flag to enable message ordering
            expiration_policy: Optional policy for subscription expiration
            filter_expr: Optional filter expression for the subscription
            dead_letter_policy: Optional dead letter policy
            retry_policy: Optional retry policy
            **kwargs: Additional parameters to pass to the create request

        Returns:
            A PubSubSubscription instance for the newly created subscription
        """
        # Process subscription name
        full_subscription_path = format_subscription_path(self.project_id, subscription_name)
        # Extract the short name for error messages
        subscription_name = extract_name_from_path(full_subscription_path)

        # Process topic name
        full_topic_path = format_topic_path(self.project_id, topic_name)

        # Prepare the request body
        body = {"topic": full_topic_path}

        if ack_deadline_seconds is not None:
            body["ackDeadlineSeconds"] = ack_deadline_seconds

        if push_config is not None:
            body["pushConfig"] = push_config

        if retain_acked_messages is not None:
            body["retainAckedMessages"] = retain_acked_messages

        if message_retention_duration is not None:
            body["messageRetentionDuration"] = message_retention_duration

        if labels is not None:
            body["labels"] = labels

        # Process tags (will be added to labels for Pub/Sub)
        body = self._process_tags(body, tags)

        if enable_message_ordering is not None:
            body["enableMessageOrdering"] = enable_message_ordering

        if expiration_policy is not None:
            body["expirationPolicy"] = expiration_policy

        if filter_expr is not None:
            body["filter"] = filter_expr

        if dead_letter_policy is not None:
            body["deadLetterPolicy"] = dead_letter_policy

        if retry_policy is not None:
            body["retryPolicy"] = retry_policy

        # Add any additional kwargs to the body
        for key, value in kwargs.items():
            if key not in ["name", "subscription"]:
                body[key] = value

        request = (
            self.service.projects()
            .subscriptions()
            .create(name=full_subscription_path, body=body)
        )
        response = self._execute(request)

        # Create the subscription object and add the tags explicitly
        subscription = PubSubSubscription.from_api_response(
            response, self.project_id
        )
        if tags:
            subscription.tags = tags
        return subscription
    def delete_subscription(self, subscription_name: str) -> bool:
        """Delete a Pub/Sub subscription.

        Args:
            subscription_name: The name of the subscription to delete

        Returns:
            True if the deletion was successful
        """
        full_subscription_path = format_subscription_path(self.project_id, subscription_name)

        request = (
            self.service.projects()
            .subscriptions()
            .delete(subscription=full_subscription_path)
        )
        self._execute(request)

        return True

    def pull_messages(
        self,
        subscription_name: str,
        max_messages: int = 10,
        return_immediately: bool = False,
    ) -> List[Dict[str, Any]]:
        """Pull messages from a Pub/Sub subscription.

        Args:
            subscription_name: The name of the subscription to pull messages from
            max_messages: Maximum number of messages to pull (default: 10)
            return_immediately: Whether to return immediately if no messages are available

        Returns:
            A list of received messages
        """
        full_subscription_path = format_subscription_path(self.project_id, subscription_name)

        request = (
            self.service.projects()
            .subscriptions()
            .pull(
                subscription=full_subscription_path,
                body={
                    "maxMessages": max_messages,
                    "returnImmediately": return_immediately,
                },
            )
        )
        response = self._execute(request)

        return response.get("receivedMessages", [])

    def acknowledge_messages(self, subscription_name: str, ack_ids: List[str]) -> bool:
        """Acknowledge messages from a Pub/Sub subscription.

        Args:
            subscription_name: The name of the subscription to acknowledge messages for
            ack_ids: List of acknowledgement IDs to acknowledge

        Returns:
            True if the acknowledgement was successful
        """
        full_subscription_path = format_subscription_path(self.project_id, subscription_name)

        request = (
            self.service.projects()
            .subscriptions()
            .acknowledge(subscription=full_subscription_path, body={"ackIds": ack_ids})
        )
        self._execute(request)

        return True
