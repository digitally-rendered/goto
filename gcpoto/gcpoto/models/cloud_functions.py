"""Models for Google Cloud Functions resources."""

from typing import Dict, Optional, Any
from pydantic import Field

from gcpoto.models.base import GCPResource


class CloudFunction(GCPResource):
    """Model for a Google Cloud Function."""

    location: str = Field("", description="The location (region) of the function")
    runtime: str = Field("", description="The runtime environment for the function")
    entry_point: str = Field(
        "", description="The name of the function entry point in the source code"
    )
    source_archive_url: Optional[str] = Field(
        None,
        description="The Google Cloud Storage URL pointing to the zip archive with the function source code",
    )
    source_repository: Optional[Dict[str, Any]] = Field(
        None,
        description="The source repository where the function is defined",
    )
    source_upload_url: Optional[str] = Field(
        None,
        description="The Google Cloud Storage signed URL for uploading function source code",
    )
    status: str = Field(
        "", description="The status of the function deployment"
    )
    timeout: Optional[str] = Field(
        None,
        description="The function execution timeout (e.g. '60s')",
    )
    available_memory_mb: Optional[int] = Field(
        None,
        description="The amount of memory in MB available for the function",
    )
    service_account_email: Optional[str] = Field(
        None,
        description="The email of the service account used by the function",
    )
    environment_variables: Optional[Dict[str, str]] = Field(
        None,
        description="Environment variables available during function execution",
    )
    build_environment_variables: Optional[Dict[str, str]] = Field(
        None,
        description="Environment variables available during build time",
    )
    max_instances: Optional[int] = Field(
        None,
        description="The maximum number of function instances",
    )
    min_instances: Optional[int] = Field(
        None,
        description="The minimum number of function instances",
    )
    vpc_connector: Optional[str] = Field(
        None,
        description="The VPC Network Connector that the function can connect to",
    )
    ingress_settings: Optional[str] = Field(
        None,
        description="The ingress settings for the function (e.g. ALLOW_ALL, ALLOW_INTERNAL_ONLY)",
    )
    trigger: Optional[Dict[str, Any]] = Field(
        None,
        description="The trigger configuration for the function (httpsTrigger or eventTrigger)",
    )
    _tags: Optional[Dict[str, str]] = None

    def get_tag(self, key: str, default: str = "") -> str:
        """Get a tag value by key, falling back to labels.

        Args:
            key: The tag key to look up
            default: Default value to return if key not found

        Returns:
            The tag value or default if not found
        """
        if self._tags and key in self._tags:
            return self._tags[key]
        if self.labels and key in self.labels:
            return self.labels[key]
        return default

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "CloudFunction":
        """Create a CloudFunction from an API response.

        Args:
            response: The API response dictionary from the Cloud Functions API

        Returns:
            A new CloudFunction instance
        """
        # The API returns the full name in the format:
        # projects/{project}/locations/{location}/functions/{function}
        full_name = response.get("name", "")
        parts = full_name.split("/")

        function_name = parts[-1] if len(parts) >= 6 else full_name
        project_id = parts[1] if len(parts) >= 2 else ""
        location = parts[3] if len(parts) >= 4 else ""

        # Extract trigger information
        trigger = None
        if response.get("httpsTrigger"):
            trigger = {"httpsTrigger": response["httpsTrigger"]}
        elif response.get("eventTrigger"):
            trigger = {"eventTrigger": response["eventTrigger"]}

        instance = cls(
            id=full_name,
            name=function_name,
            type="cloudfunctions.function",
            project=project_id,
            location=location,
            runtime=response.get("runtime", ""),
            entry_point=response.get("entryPoint", ""),
            source_archive_url=response.get("sourceArchiveUrl"),
            source_repository=response.get("sourceRepository"),
            source_upload_url=response.get("sourceUploadUrl"),
            status=response.get("status", ""),
            timeout=response.get("timeout"),
            available_memory_mb=response.get("availableMemoryMb"),
            service_account_email=response.get("serviceAccountEmail"),
            environment_variables=response.get("environmentVariables"),
            build_environment_variables=response.get("buildEnvironmentVariables"),
            max_instances=response.get("maxInstances"),
            min_instances=response.get("minInstances"),
            vpc_connector=response.get("vpcConnector"),
            ingress_settings=response.get("ingressSettings"),
            trigger=trigger,
            labels=response.get("labels"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )

        if response.get("labels"):
            instance._tags = response["labels"]

        return instance
