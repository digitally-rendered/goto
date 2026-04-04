"""Models for Google Cloud Armor resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.armor import get_schema


class SecurityPolicy(GCPResource):
    """Model for a Google Cloud Armor Security Policy."""

    description: Optional[str] = Field(
        None, description="A description of the security policy"
    )
    rules: List[Dict] = Field(
        default_factory=list,
        description="The list of rules that belong to this policy",
    )
    fingerprint: Optional[str] = Field(
        None, description="Fingerprint of this resource for optimistic locking"
    )
    adaptive_protection_config: Optional[Dict] = Field(
        None, description="Adaptive protection configuration"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("security_policy")}

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
    def from_api_response(cls, response: Dict[str, Any]) -> "SecurityPolicy":
        """Create a SecurityPolicy from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new SecurityPolicy instance
        """
        instance = cls(
            id=response.get("id", ""),
            name=response.get("name", ""),
            type="compute.securityPolicy",
            project=response.get("project", ""),
            description=response.get("description"),
            rules=response.get("rules", []),
            fingerprint=response.get("fingerprint"),
            adaptive_protection_config=response.get("adaptiveProtectionConfig"),
            labels=response.get("labels"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance


class SecurityPolicyRule(GCPResource):
    """Model for a Google Cloud Armor Security Policy Rule."""

    policy_name: str = Field("", description="The security policy this rule belongs to")
    priority: int = Field(0, description="The priority of this rule (lower = higher priority)")
    description: Optional[str] = Field(
        None, description="A description of the rule"
    )
    action: str = Field("", description="The action to take (allow, deny(403), deny(404), deny(502), redirect, rate_based_ban, throttle)")
    match: Dict = Field(
        default_factory=dict,
        description="The match condition for the rule",
    )
    preview: bool = Field(
        False, description="Whether this rule is in preview mode"
    )
    rate_limit_options: Optional[Dict] = Field(
        None, description="Rate limit options for rate-based rules"
    )
    _tags: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("security_policy_rule")}

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
    def from_api_response(
        cls, response: Dict[str, Any], policy_name: str = ""
    ) -> "SecurityPolicyRule":
        """Create a SecurityPolicyRule from an API response.

        Args:
            response: The API response dictionary
            policy_name: The name of the security policy this rule belongs to

        Returns:
            A new SecurityPolicyRule instance
        """
        priority = response.get("priority", 0)
        instance = cls(
            id=f"{policy_name}/{priority}",
            name=f"rule-{priority}",
            type="compute.securityPolicyRule",
            project=response.get("project", ""),
            policy_name=policy_name,
            priority=priority,
            description=response.get("description"),
            action=response.get("action", ""),
            match=response.get("match", {}),
            preview=response.get("preview", False),
            rate_limit_options=response.get("rateLimitOptions"),
            labels=response.get("labels"),
        )
        if response.get("labels"):
            instance._tags = response["labels"]
        return instance
