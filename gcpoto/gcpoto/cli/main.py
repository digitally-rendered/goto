"""Command-line interface for gcpoto."""

import os
import json
import click
from typing import Optional, List

from gcpoto import __version__
from gcpoto.services.storage import StorageService
from gcpoto.services.compute import ComputeService
from gcpoto.models.base import GCPResource


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--project",
    envvar="GCP_PROJECT_ID",
    help="GCP Project ID. Can also be set via GCP_PROJECT_ID environment variable.",
)
@click.option(
    "--credentials",
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
    help="Path to service account credentials file. Can also be set via GOOGLE_APPLICATION_CREDENTIALS environment variable.",
)
@click.option("--region", help="GCP region to use for regional resources.")
@click.option("--zone", help="GCP zone to use for zonal resources.")
@click.option("--output", type=click.Choice(["json", "text", "table"]), default="json", help="Output format")
@click.pass_context
def cli(ctx, project, credentials, region, zone, output):
    """GCPoto: A boto-like CLI for Google Cloud Platform."""
    ctx.ensure_object(dict)
    ctx.obj["project_id"] = project
    ctx.obj["credentials_file"] = credentials
    ctx.obj["region"] = region
    ctx.obj["zone"] = zone
    ctx.obj["output"] = output

 
@cli.group()
@click.pass_context
def storage(ctx): 
    """Commands for interacting with Google Cloud Storage."""
    pass


@storage.command("list-buckets")
@click.pass_context
def list_buckets(ctx):
    """List storage buckets in the project."""
    from gcpoto.services.storage import StorageService
    
    project_id = ctx.obj.get("project_id")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = StorageService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials_file")
    )
    
    buckets = service.list_resources()
    _output_result(buckets, ctx.obj.get("output", "json"))


@storage.command("list-objects")
@click.argument("bucket")
@click.option("--prefix", help="Filter objects by prefix")
@click.pass_context
def list_objects(ctx, bucket, prefix):
    """List objects in a bucket."""
    from gcpoto.services.storage import StorageService
    
    project_id = ctx.obj.get("project_id")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = StorageService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials_file")
    )
    
    objects = service.list_objects(bucket, prefix)
    _output_result(objects, ctx.obj.get("output", "json"))


@storage.command("get-object")
@click.argument("bucket")
@click.argument("object_name")
@click.pass_context
def get_object(ctx, bucket, object_name):
    """Get object metadata from a bucket."""
    from gcpoto.services.storage import StorageService
    
    project_id = ctx.obj.get("project_id")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = StorageService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials_file")
    )
    
    obj = service.get_object(bucket, object_name)
    _output_result(obj, ctx.obj.get("output", "json"))


@storage.command("download")
@click.argument("bucket")
@click.argument("object_name")
@click.argument("destination", required=False)
@click.pass_context
def download_object(ctx, bucket, object_name, destination):
    """Download an object from a bucket."""
    from gcpoto.services.storage import StorageService
    
    project_id = ctx.obj.get("project_id")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = StorageService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials_file")
    )
    
    # If no destination is provided, use the object name in the current directory
    if not destination:
        destination = os.path.basename(object_name)
        
    result = service.download_object(bucket, object_name, destination)
    click.echo(f"Downloaded {object_name} to {destination}")


@storage.command("upload")
@click.argument("bucket")
@click.argument("source")
@click.option("--object-name", help="Name to give the object in the bucket (defaults to source filename)")
@click.option("--content-type", help="Content type of the object")
@click.pass_context
def upload_object(ctx, bucket, source, object_name, content_type):
    """Upload a file to a bucket."""
    from gcpoto.services.storage import StorageService
    
    project_id = ctx.obj.get("project_id")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    # If no object name is provided, use the source filename
    if not object_name:
        object_name = os.path.basename(source)
        
    service = StorageService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials_file")
    )
    
    obj = service.upload_object(bucket, object_name, source, content_type)
    click.echo(f"Uploaded {source} to {bucket}/{object_name}")
    _output_result(obj, ctx.obj.get("output", "json"))


@storage.command("delete-object")
@click.argument("bucket")
@click.argument("object_name")
@click.confirmation_option(prompt="Are you sure you want to delete this object?")
@click.pass_context
def delete_object(ctx, bucket, object_name):
    """Delete an object from a bucket."""
    from gcpoto.services.storage import StorageService
    
    project_id = ctx.obj.get("project_id")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = StorageService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials_file")
    )
    
    service.delete_object(bucket, object_name)
    click.echo(f"Deleted {bucket}/{object_name}")


@cli.group()
@click.pass_context
def pubsub(ctx):
    """Commands for interacting with Google Cloud Pub/Sub."""
    pass


@pubsub.command("list-topics")
@click.pass_context
def list_topics(ctx):
    """List Pub/Sub topics in the project."""
    from gcpoto.services.pubsub import PubSubService
    
    project_id = ctx.obj.get("project")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = PubSubService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials")
    )
    
    topics = service.list_resources()
    _output_result(topics, ctx.obj.get("output", "json"))


@pubsub.command("get-topic")
@click.argument("topic")
@click.pass_context
def get_topic(ctx, topic):
    """Get a specific Pub/Sub topic."""
    from gcpoto.services.pubsub import PubSubService
    
    project_id = ctx.obj.get("project")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = PubSubService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials")
    )
    
    topic_obj = service.get_topic(topic)
    _output_result(topic_obj, ctx.obj.get("output", "json"))


@pubsub.command("create-topic")
@click.argument("topic")
@click.option("--label", multiple=True, help="Labels to apply to the topic in the format key=value")
@click.option("--kms-key", help="KMS key to use for message protection")
@click.option("--message-retention", help="Duration for which messages are retained (e.g., 'P1D' for 1 day)")
@click.option("--region", multiple=True, help="Regions where messages can be stored")
@click.pass_context
def create_topic(ctx, topic, label, kms_key, message_retention, region):
    """Create a new Pub/Sub topic."""
    from gcpoto.services.pubsub import PubSubService
    
    project_id = ctx.obj.get("project")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    # Process labels into a dictionary
    labels = {}
    for lbl in label:
        if '=' in lbl:
            key, value = lbl.split('=', 1)
            labels[key] = value
        else:
            click.echo(f"Warning: Ignoring malformed label '{lbl}'. Use format key=value")
    
    # Process regions into a message storage policy if specified
    message_storage_policy = None
    if region:
        message_storage_policy = {
            "allowedPersistenceRegions": list(region)
        }
    
    service = PubSubService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials")
    )
    
    topic_obj = service.create_topic(
        topic_name=topic,
        labels=labels if labels else None,
        kms_key_name=kms_key,
        message_retention_duration=message_retention,
        message_storage_policy=message_storage_policy
    )
    
    click.echo(f"Created topic: {topic_obj.name}")
    _output_result(topic_obj, ctx.obj.get("output", "json"))


@pubsub.command("delete-topic")
@click.argument("topic")
@click.confirmation_option(prompt="Are you sure you want to delete this topic?")
@click.pass_context
def delete_topic(ctx, topic):
    """Delete a Pub/Sub topic."""
    from gcpoto.services.pubsub import PubSubService
    
    project_id = ctx.obj.get("project")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = PubSubService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials")
    )
    
    service.delete_topic(topic)
    click.echo(f"Deleted topic: {topic}")


@pubsub.command("publish")
@click.argument("topic")
@click.argument("message")
@click.option("--attribute", multiple=True, help="Message attributes in the format key=value")
@click.pass_context
def publish_message(ctx, topic, message, attribute):
    """Publish a message to a Pub/Sub topic."""
    from gcpoto.services.pubsub import PubSubService
    
    project_id = ctx.obj.get("project")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    # Process attributes into a dictionary
    attributes = {}
    for attr in attribute:
        if '=' in attr:
            key, value = attr.split('=', 1)
            attributes[key] = value
        else:
            click.echo(f"Warning: Ignoring malformed attribute '{attr}'. Use format key=value")
    
    service = PubSubService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials")
    )
    
    message_id = service.publish_message(
        topic_name=topic,
        data=message,
        attributes=attributes if attributes else None
    )
    
    click.echo(f"Published message with ID: {message_id}")


@pubsub.command("list-subscriptions")
@click.option("--topic", help="Optional topic to filter subscriptions by")
@click.pass_context
def list_subscriptions(ctx, topic):
    """List Pub/Sub subscriptions in the project."""
    from gcpoto.services.pubsub import PubSubService
    
    project_id = ctx.obj.get("project")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = PubSubService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials")
    )
    
    subscriptions = service.list_subscriptions(topic)
    _output_result(subscriptions, ctx.obj.get("output", "json"))


@pubsub.command("get-subscription")
@click.argument("subscription")
@click.pass_context
def get_subscription(ctx, subscription):
    """Get a specific Pub/Sub subscription."""
    from gcpoto.services.pubsub import PubSubService
    
    project_id = ctx.obj.get("project")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = PubSubService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials")
    )
    
    subscription_obj = service.get_subscription(subscription)
    _output_result(subscription_obj, ctx.obj.get("output", "json"))


@pubsub.command("create-subscription")
@click.argument("subscription")
@click.argument("topic")
@click.option("--ack-deadline", type=int, help="Acknowledgement deadline in seconds")
@click.option("--push-endpoint", help="URL to push messages to")
@click.option("--retain-acked", is_flag=True, help="Retain acknowledged messages")
@click.option("--message-retention", help="Duration to retain unacknowledged messages (e.g., 'P1D' for 1 day)")
@click.option("--label", multiple=True, help="Labels to apply to the subscription in the format key=value")
@click.option("--filter", help="Filter expression for the subscription")
@click.option("--enable-ordering", is_flag=True, help="Enable message ordering")
@click.pass_context
def create_subscription(ctx, subscription, topic, ack_deadline, push_endpoint, retain_acked,
                       message_retention, label, filter, enable_ordering):
    """Create a new Pub/Sub subscription."""
    from gcpoto.services.pubsub import PubSubService
    
    project_id = ctx.obj.get("project")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    # Process labels into a dictionary
    labels = {}
    for lbl in label:
        if '=' in lbl:
            key, value = lbl.split('=', 1)
            labels[key] = value
        else:
            click.echo(f"Warning: Ignoring malformed label '{lbl}'. Use format key=value")
    
    # Create push config if push endpoint is specified
    push_config = None
    if push_endpoint:
        push_config = {
            "pushEndpoint": push_endpoint
        }
    
    service = PubSubService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials")
    )
    
    subscription_obj = service.create_subscription(
        subscription_name=subscription,
        topic_name=topic,
        ack_deadline_seconds=ack_deadline,
        push_config=push_config,
        retain_acked_messages=retain_acked,
        message_retention_duration=message_retention,
        labels=labels if labels else None,
        filter_expr=filter,
        enable_message_ordering=enable_ordering
    )
    
    click.echo(f"Created subscription: {subscription_obj.name}")
    _output_result(subscription_obj, ctx.obj.get("output", "json"))


@pubsub.command("delete-subscription")
@click.argument("subscription")
@click.confirmation_option(prompt="Are you sure you want to delete this subscription?")
@click.pass_context
def delete_subscription(ctx, subscription):
    """Delete a Pub/Sub subscription."""
    from gcpoto.services.pubsub import PubSubService
    
    project_id = ctx.obj.get("project")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = PubSubService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials")
    )
    
    service.delete_subscription(subscription)
    click.echo(f"Deleted subscription: {subscription}")


@pubsub.command("pull")
@click.argument("subscription")
@click.option("--max-messages", type=int, default=10, help="Maximum number of messages to pull")
@click.option("--auto-ack", is_flag=True, help="Automatically acknowledge messages after pulling")
@click.pass_context
def pull_messages(ctx, subscription, max_messages, auto_ack):
    """Pull messages from a Pub/Sub subscription."""
    from gcpoto.services.pubsub import PubSubService
    
    project_id = ctx.obj.get("project")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    service = PubSubService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials")
    )
    
    messages = service.pull_messages(subscription, max_messages)
    
    if not messages:
        click.echo("No messages available.")
        return
    
    # Format and display the messages
    click.echo(f"Pulled {len(messages)} messages:")
    
    ack_ids = []
    for msg in messages:
        ack_ids.append(msg.get('ackId'))
        message_data = msg.get('message', {})
        data = message_data.get('data', '')
        attributes = message_data.get('attributes', {})
        
        # Try to decode the message data if it's base64 encoded
        try:
            import base64
            decoded_data = base64.b64decode(data).decode('utf-8')
        except Exception:
            decoded_data = data
        
        click.echo(f"Message ID: {message_data.get('messageId', 'unknown')}")
        click.echo(f"Data: {decoded_data}")
        if attributes:
            click.echo("Attributes:")
            for key, value in attributes.items():
                click.echo(f"  {key}: {value}")
        click.echo("---")
    
    # Auto-acknowledge messages if requested
    if auto_ack and ack_ids:
        service.acknowledge_messages(subscription, ack_ids)
        click.echo(f"Acknowledged {len(ack_ids)} messages.")


@cli.group()
@click.pass_context
def compute(ctx):
    """Commands for interacting with Google Compute Engine."""
    pass


@compute.command("list-instances")
@click.option("--zone", help="Zone to list instances from")
@click.pass_context
def list_instances(ctx, zone):
    """List compute instances in the project."""
    from gcpoto.services.compute import ComputeService
    
    project_id = ctx.obj.get("project_id")
    if not project_id:
        raise click.UsageError("Project ID must be specified")
    
    zone = zone or ctx.obj.get("zone")
    if not zone:
        raise click.UsageError("Zone must be specified")
    
    service = ComputeService(
        project_id=project_id,
        credentials_file=ctx.obj.get("credentials_file")
    )
    
    instances = service.list_resources(zone=zone)
    _output_result(instances, ctx.obj.get("output", "json"))


def _output_result(resources, output_format="json"):
    """Output the result in the specified format.
    
    Args:
        resources: List of GCPResource objects or a single GCPResource
        output_format: Format to output (json, text, or table)
    """
    if not isinstance(resources, list):
        resources = [resources]
    
    if output_format == "json":
        result = [r.to_dict() for r in resources]
        click.echo(json.dumps(result, indent=2))
    elif output_format == "text":
        for resource in resources:
            click.echo(f"ID: {resource.id}")
            click.echo(f"Name: {resource.name}")
            click.echo(f"Type: {resource.type}")
            click.echo(f"Project: {resource.project}")
            click.echo("---")
    elif output_format == "table":
        # Simple table output (a real implementation would use tabulate or similar)
        click.echo(f"{'ID':<20} {'Name':<30} {'Type':<20}")
        click.echo("-" * 70)
        for resource in resources:
            click.echo(f"{resource.id:<20} {resource.name:<30} {resource.type:<20}")


def main():
    """Main entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
