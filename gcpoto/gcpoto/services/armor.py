"""Service implementation for Google Cloud Armor."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.armor import SecurityPolicy, SecurityPolicyRule
from gcpoto.exceptions import (
    APIError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


class CloudArmorService(GCPService[SecurityPolicy]):
    """Service for interacting with Google Cloud Armor."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud Armor service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="compute",
            version="v1",
            credentials_file=credentials_file,
            resource_model=SecurityPolicy,
            **kwargs,
        )

    def list_security_policies(self, **kwargs) -> List[SecurityPolicy]:
        """List security policies in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of SecurityPolicy instances
        """
        logger.info(
            "Listing security policies for project %s", self.project_id
        )

        request = self.service.securityPolicies().list(
            project=self.project_id, **kwargs
        )

        policies = []
        while request is not None:
            response = self._execute(request)
            for policy_data in response.get("items", []):
                policies.append(SecurityPolicy.from_api_response(policy_data))
            request = self.service.securityPolicies().list_next(
                request, response
            )

        logger.info("Found %s security policies", len(policies))
        return policies

    def get_security_policy(self, policy_name: str) -> SecurityPolicy:
        """Get a specific security policy by name.

        Args:
            policy_name: The name of the security policy to retrieve

        Returns:
            A SecurityPolicy instance

        Raises:
            ResourceNotFoundError: If the policy does not exist
            APIError: If the API call fails
        """
        logger.info("Getting security policy %s", policy_name)

        request = self.service.securityPolicies().get(
            project=self.project_id, securityPolicy=policy_name
        )
        response = self._execute(request, "SecurityPolicy", policy_name)
        return SecurityPolicy.from_api_response(response)
    def create_security_policy(
        self,
        policy_name: str,
        description: Optional[str] = None,
    ) -> SecurityPolicy:
        """Create a new security policy.

        Args:
            policy_name: The name of the security policy to create
            description: Optional description for the policy

        Returns:
            A SecurityPolicy instance for the newly created policy

        Raises:
            ResourceAlreadyExistsError: If the policy already exists
            APIError: If the API call fails
        """
        logger.info("Creating security policy %s", policy_name)

        body = {"name": policy_name}
        if description is not None:
            body["description"] = description

        request = self.service.securityPolicies().insert(
            project=self.project_id, body=body
        )
        self._execute(request)
        logger.info("Created security policy %s", policy_name)
        return self.get_security_policy(policy_name)
    def delete_security_policy(self, policy_name: str) -> bool:
        """Delete a security policy.

        Args:
            policy_name: The name of the security policy to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the policy does not exist
            APIError: If the API call fails
        """
        logger.info("Deleting security policy %s", policy_name)

        request = self.service.securityPolicies().delete(
            project=self.project_id, securityPolicy=policy_name
        )
        self._execute(request)
        logger.info("Deleted security policy %s", policy_name)
        return True
    def add_rule(
        self,
        policy_name: str,
        priority: int,
        action: str,
        match: Dict,
        description: Optional[str] = None,
        preview: bool = False,
    ) -> SecurityPolicyRule:
        """Add a rule to a security policy.

        Args:
            policy_name: The name of the security policy
            priority: The priority of the rule (lower = higher priority)
            action: The action to take (allow, deny(403), deny(404), etc.)
            match: The match condition for the rule
            description: Optional description for the rule
            preview: Whether this rule is in preview mode

        Returns:
            A SecurityPolicyRule instance for the newly created rule

        Raises:
            ResourceNotFoundError: If the policy does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Adding rule with priority %s to security policy %s",
            priority,
            policy_name,
        )

        body = {
            "priority": priority,
            "action": action,
            "match": match,
            "preview": preview,
        }
        if description is not None:
            body["description"] = description

        request = self.service.securityPolicies().addRule(
            project=self.project_id,
            securityPolicy=policy_name,
            body=body,
        )
        self._execute(request, "SecurityPolicy", policy_name)
        logger.info(
            "Added rule with priority %s to security policy %s",
            priority,
            policy_name,
        )
        return self.get_rule(policy_name, priority)
    def remove_rule(self, policy_name: str, priority: int) -> bool:
        """Remove a rule from a security policy.

        Args:
            policy_name: The name of the security policy
            priority: The priority of the rule to remove

        Returns:
            True if the removal was successful

        Raises:
            ResourceNotFoundError: If the policy or rule does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Removing rule with priority %s from security policy %s",
            priority,
            policy_name,
        )

        request = self.service.securityPolicies().removeRule(
            project=self.project_id,
            securityPolicy=policy_name,
            priority=priority,
        )
        self._execute(request)
        logger.info(
            "Removed rule with priority %s from security policy %s",
            priority,
            policy_name,
        )
        return True
    def get_rule(
        self, policy_name: str, priority: int
    ) -> SecurityPolicyRule:
        """Get a specific rule from a security policy.

        Args:
            policy_name: The name of the security policy
            priority: The priority of the rule to retrieve

        Returns:
            A SecurityPolicyRule instance

        Raises:
            ResourceNotFoundError: If the policy or rule does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Getting rule with priority %s from security policy %s",
            priority,
            policy_name,
        )

        request = self.service.securityPolicies().getRule(
            project=self.project_id,
            securityPolicy=policy_name,
            priority=priority,
        )
        response = self._execute(request, "SecurityPolicyRule", str(priority))
        return SecurityPolicyRule.from_api_response(response, policy_name)
    def patch_rule(
        self,
        policy_name: str,
        priority: int,
        action: Optional[str] = None,
        match: Optional[Dict] = None,
        description: Optional[str] = None,
        preview: Optional[bool] = None,
    ) -> SecurityPolicyRule:
        """Patch (update) a rule in a security policy.

        Args:
            policy_name: The name of the security policy
            priority: The priority of the rule to update
            action: Optional new action for the rule
            match: Optional new match condition
            description: Optional new description
            preview: Optional new preview setting

        Returns:
            A SecurityPolicyRule instance for the updated rule

        Raises:
            ResourceNotFoundError: If the policy or rule does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Patching rule with priority %s in security policy %s",
            priority,
            policy_name,
        )

        body = {}
        if action is not None:
            body["action"] = action
        if match is not None:
            body["match"] = match
        if description is not None:
            body["description"] = description
        if preview is not None:
            body["preview"] = preview

        request = self.service.securityPolicies().patchRule(
            project=self.project_id,
            securityPolicy=policy_name,
            priority=priority,
            body=body,
        )
        self._execute(request, "SecurityPolicyRule", str(priority))
        logger.info(
            "Patched rule with priority %s in security policy %s",
            priority,
            policy_name,
        )
        return self.get_rule(policy_name, priority)
    def list_rules(self, policy_name: str) -> List[SecurityPolicyRule]:
        """List all rules in a security policy.

        Args:
            policy_name: The name of the security policy

        Returns:
            A list of SecurityPolicyRule instances

        Raises:
            ResourceNotFoundError: If the policy does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Listing rules for security policy %s", policy_name
        )

        policy = self.get_security_policy(policy_name)
        rules = [
            SecurityPolicyRule.from_api_response(rule_data, policy_name)
            for rule_data in policy.rules
        ]

        logger.info(
            "Found %s rules in security policy %s",
            len(rules),
            policy_name,
        )
        return rules
