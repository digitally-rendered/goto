"""Utility functions for formatting GCP resource paths."""


def format_topic_path(project_id: str, topic_name: str) -> str:
    """Return full projects/{project}/topics/{topic} path if not already formatted.

    Args:
        project_id: The GCP project ID.
        topic_name: Either a short topic name or a full resource path.

    Returns:
        The fully-qualified topic resource path.
    """
    if "/" not in topic_name:
        return f"projects/{project_id}/topics/{topic_name}"
    return topic_name


def format_subscription_path(project_id: str, subscription_name: str) -> str:
    """Return full projects/{project}/subscriptions/{sub} path if not already formatted.

    Args:
        project_id: The GCP project ID.
        subscription_name: Either a short subscription name or a full resource path.

    Returns:
        The fully-qualified subscription resource path.
    """
    if "/" not in subscription_name:
        return f"projects/{project_id}/subscriptions/{subscription_name}"
    return subscription_name


def format_snapshot_path(project_id: str, snapshot_name: str) -> str:
    """Return full projects/{project}/snapshots/{snap} path if not already formatted.

    Args:
        project_id: The GCP project ID.
        snapshot_name: Either a short snapshot name or a full resource path.

    Returns:
        The fully-qualified snapshot resource path.
    """
    if "/" not in snapshot_name:
        return f"projects/{project_id}/snapshots/{snapshot_name}"
    return snapshot_name


def extract_name_from_path(full_path: str) -> str:
    """Extract the last segment from a full resource path.

    Args:
        full_path: A fully-qualified resource path
            (e.g. ``projects/my-proj/topics/my-topic``).

    Returns:
        The last path segment (e.g. ``my-topic``).
    """
    return full_path.split("/")[-1]
