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


def format_secret_path(project_id: str, secret_id: str) -> str:
    """Return full projects/{project}/secrets/{secret} path if not already formatted.

    Args:
        project_id: The GCP project ID.
        secret_id: Either a short secret ID or a full resource path.

    Returns:
        The fully-qualified secret resource path.
    """
    if "/" not in secret_id:
        return f"projects/{project_id}/secrets/{secret_id}"
    return secret_id


def format_secret_version_path(
    project_id: str, secret_id: str, version_id: str
) -> str:
    """Return full projects/{project}/secrets/{secret}/versions/{version} path.

    Args:
        project_id: The GCP project ID.
        secret_id: Either a short secret ID or a full secret resource path.
        version_id: The version identifier (e.g. '1', 'latest').

    Returns:
        The fully-qualified secret version resource path.
    """
    secret_path = format_secret_path(project_id, secret_id)
    return f"{secret_path}/versions/{version_id}"


def format_key_ring_path(
    project_id: str, location: str, key_ring_id: str
) -> str:
    """Return full projects/{project}/locations/{location}/keyRings/{keyRing} path.

    Args:
        project_id: The GCP project ID.
        location: The GCP location (e.g. 'global', 'us-east1').
        key_ring_id: The key ring ID.

    Returns:
        The fully-qualified key ring resource path.
    """
    return (
        f"projects/{project_id}/locations/{location}/keyRings/{key_ring_id}"
    )


def format_crypto_key_path(
    project_id: str, location: str, key_ring_id: str, key_id: str
) -> str:
    """Return full projects/{project}/locations/{loc}/keyRings/{kr}/cryptoKeys/{key} path.

    Args:
        project_id: The GCP project ID.
        location: The GCP location (e.g. 'global', 'us-east1').
        key_ring_id: The key ring ID.
        key_id: The crypto key ID.

    Returns:
        The fully-qualified crypto key resource path.
    """
    return (
        f"projects/{project_id}/locations/{location}"
        f"/keyRings/{key_ring_id}/cryptoKeys/{key_id}"
    )


def extract_name_from_path(full_path: str) -> str:
    """Extract the last segment from a full resource path.

    Args:
        full_path: A fully-qualified resource path
            (e.g. ``projects/my-proj/topics/my-topic``).

    Returns:
        The last path segment (e.g. ``my-topic``).
    """
    return full_path.split("/")[-1]
