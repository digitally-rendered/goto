"""Tests for Cloud Armor service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.armor import CloudArmorService
from gcpoto.models.armor import SecurityPolicy, SecurityPolicyRule
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
)


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_security_policies = mock.MagicMock()
        mock_service.securityPolicies.return_value = mock_security_policies

        yield mock_service


@pytest.fixture
def sample_policy_response():
    """Sample Cloud Armor security policy API response."""
    return {
        "id": "123456789",
        "name": "my-security-policy",
        "description": "My security policy",
        "rules": [
            {
                "priority": 2147483647,
                "action": "allow",
                "match": {"versionedExpr": "SRC_IPS_V1", "config": {"srcIpRanges": ["*"]}},
                "description": "Default rule",
                "preview": False,
            },
            {
                "priority": 1000,
                "action": "deny(403)",
                "match": {"versionedExpr": "SRC_IPS_V1", "config": {"srcIpRanges": ["10.0.0.0/8"]}},
                "description": "Block internal IPs",
                "preview": True,
            },
        ],
        "fingerprint": "abc123def456",
        "adaptiveProtectionConfig": {"layer7DdosDefenseConfig": {"enable": True}},
        "labels": {"env": "production", "team": "security"},
        "project": "test-project",
        "creationTimestamp": "2024-06-15T10:30:00.000Z",
    }


@pytest.fixture
def sample_rule_response():
    """Sample Cloud Armor security policy rule API response."""
    return {
        "priority": 1000,
        "action": "deny(403)",
        "match": {
            "versionedExpr": "SRC_IPS_V1",
            "config": {"srcIpRanges": ["10.0.0.0/8"]},
        },
        "description": "Block internal IPs",
        "preview": True,
        "project": "test-project",
    }


@pytest.fixture
def service(mock_google_client):
    """Create a CloudArmorService instance with mocked API client."""
    svc = CloudArmorService(project_id="test-project")
    return svc


class TestCloudArmorServiceInit:
    """Tests for CloudArmorService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the CloudArmorService."""
        from googleapiclient.discovery import build

        service = CloudArmorService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "compute"
        assert service.version == "v1"
        build.assert_called_once_with("compute", "v1", credentials=None)

    def test_init_with_credentials(self, mock_google_client):
        """Test initializing with credentials file."""
        with mock.patch(
            "google.oauth2.service_account.Credentials.from_service_account_file"
        ) as mock_creds:
            mock_creds.return_value = mock.MagicMock()
            service = CloudArmorService(
                project_id="test-project",
                credentials_file="/path/to/creds.json",
            )
            assert service.project_id == "test-project"
            mock_creds.assert_called_once()


class TestListSecurityPolicies:
    """Tests for listing security policies."""

    def test_list_security_policies(self, service, sample_policy_response):
        """Test listing security policies."""
        mock_request = mock.MagicMock()
        mock_list = service.service.securityPolicies.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "items": [sample_policy_response]
        }

        mock_list_next = service.service.securityPolicies.return_value.list_next
        mock_list_next.return_value = None

        policies = service.list_security_policies()

        mock_list.assert_called_once_with(project="test-project")
        assert len(policies) == 1
        assert isinstance(policies[0], SecurityPolicy)
        assert policies[0].name == "my-security-policy"
        assert policies[0].description == "My security policy"
        assert len(policies[0].rules) == 2

    def test_list_security_policies_empty(self, service):
        """Test listing policies when none exist."""
        mock_request = mock.MagicMock()
        mock_list = service.service.securityPolicies.return_value.list
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {"items": []}

        mock_list_next = service.service.securityPolicies.return_value.list_next
        mock_list_next.return_value = None

        policies = service.list_security_policies()

        assert len(policies) == 0

    def test_list_security_policies_pagination(self, service, sample_policy_response):
        """Test listing policies with pagination."""
        mock_request_page1 = mock.MagicMock()
        mock_request_page2 = mock.MagicMock()

        mock_list = service.service.securityPolicies.return_value.list
        mock_list.return_value = mock_request_page1

        mock_request_page1.execute.return_value = {
            "items": [sample_policy_response]
        }

        second_policy = dict(sample_policy_response)
        second_policy["name"] = "second-policy"
        mock_request_page2.execute.return_value = {
            "items": [second_policy]
        }

        mock_list_next = service.service.securityPolicies.return_value.list_next
        mock_list_next.side_effect = [mock_request_page2, None]

        policies = service.list_security_policies()

        assert len(policies) == 2
        assert policies[0].name == "my-security-policy"
        assert policies[1].name == "second-policy"


class TestGetSecurityPolicy:
    """Tests for getting a security policy."""

    def test_get_security_policy(self, service, sample_policy_response):
        """Test getting a specific security policy."""
        mock_request = mock.MagicMock()
        mock_get = service.service.securityPolicies.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_policy_response

        policy = service.get_security_policy("my-security-policy")

        mock_get.assert_called_once_with(
            project="test-project", securityPolicy="my-security-policy"
        )
        assert isinstance(policy, SecurityPolicy)
        assert policy.name == "my-security-policy"
        assert policy.description == "My security policy"
        assert policy.fingerprint == "abc123def456"
        assert policy.adaptive_protection_config is not None

    def test_get_security_policy_not_found(self, service):
        """Test getting a policy that does not exist."""
        mock_request = mock.MagicMock()
        mock_get = service.service.securityPolicies.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_security_policy("nonexistent-policy")

    def test_get_security_policy_api_error(self, service):
        """Test getting a policy with an API error."""
        mock_request = mock.MagicMock()
        mock_get = service.service.securityPolicies.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_security_policy("my-security-policy")


class TestCreateSecurityPolicy:
    """Tests for creating a security policy."""

    def test_create_security_policy(self, service, sample_policy_response):
        """Test creating a security policy."""
        mock_insert_request = mock.MagicMock()
        mock_insert = service.service.securityPolicies.return_value.insert
        mock_insert.return_value = mock_insert_request
        mock_insert_request.execute.return_value = {}

        mock_get_request = mock.MagicMock()
        mock_get = service.service.securityPolicies.return_value.get
        mock_get.return_value = mock_get_request
        mock_get_request.execute.return_value = sample_policy_response

        policy = service.create_security_policy(
            policy_name="my-security-policy",
            description="My security policy",
        )

        mock_insert.assert_called_once_with(
            project="test-project",
            body={
                "name": "my-security-policy",
                "description": "My security policy",
            },
        )
        assert isinstance(policy, SecurityPolicy)
        assert policy.name == "my-security-policy"

    def test_create_security_policy_minimal(self, service, sample_policy_response):
        """Test creating a policy with minimal parameters."""
        mock_insert_request = mock.MagicMock()
        mock_insert = service.service.securityPolicies.return_value.insert
        mock_insert.return_value = mock_insert_request
        mock_insert_request.execute.return_value = {}

        mock_get_request = mock.MagicMock()
        mock_get = service.service.securityPolicies.return_value.get
        mock_get.return_value = mock_get_request
        mock_get_request.execute.return_value = sample_policy_response

        policy = service.create_security_policy(policy_name="my-security-policy")

        mock_insert.assert_called_once_with(
            project="test-project",
            body={"name": "my-security-policy"},
        )
        assert isinstance(policy, SecurityPolicy)

    def test_create_security_policy_already_exists(self, service):
        """Test creating a policy that already exists."""
        mock_request = mock.MagicMock()
        mock_insert = service.service.securityPolicies.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        with pytest.raises(ResourceAlreadyExistsError):
            service.create_security_policy(policy_name="my-security-policy")

    def test_create_security_policy_api_error(self, service):
        """Test creating a policy with an API error."""
        mock_request = mock.MagicMock()
        mock_insert = service.service.securityPolicies.return_value.insert
        mock_insert.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=403), content=b"Forbidden"
        )

        with pytest.raises(APIError):
            service.create_security_policy(policy_name="my-security-policy")


class TestDeleteSecurityPolicy:
    """Tests for deleting a security policy."""

    def test_delete_security_policy(self, service):
        """Test deleting a security policy."""
        mock_request = mock.MagicMock()
        mock_delete = service.service.securityPolicies.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.delete_security_policy("my-security-policy")

        mock_delete.assert_called_once_with(
            project="test-project", securityPolicy="my-security-policy"
        )
        assert result is True

    def test_delete_security_policy_not_found(self, service):
        """Test deleting a policy that does not exist."""
        mock_request = mock.MagicMock()
        mock_delete = service.service.securityPolicies.return_value.delete
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_security_policy("nonexistent-policy")


class TestAddRule:
    """Tests for adding rules to a security policy."""

    def test_add_rule(self, service, sample_rule_response):
        """Test adding a rule to a security policy."""
        mock_add_request = mock.MagicMock()
        mock_add_rule = service.service.securityPolicies.return_value.addRule
        mock_add_rule.return_value = mock_add_request
        mock_add_request.execute.return_value = {}

        mock_get_request = mock.MagicMock()
        mock_get_rule = service.service.securityPolicies.return_value.getRule
        mock_get_rule.return_value = mock_get_request
        mock_get_request.execute.return_value = sample_rule_response

        match = {
            "versionedExpr": "SRC_IPS_V1",
            "config": {"srcIpRanges": ["10.0.0.0/8"]},
        }
        rule = service.add_rule(
            policy_name="my-security-policy",
            priority=1000,
            action="deny(403)",
            match=match,
            description="Block internal IPs",
            preview=True,
        )

        mock_add_rule.assert_called_once_with(
            project="test-project",
            securityPolicy="my-security-policy",
            body={
                "priority": 1000,
                "action": "deny(403)",
                "match": match,
                "preview": True,
                "description": "Block internal IPs",
            },
        )
        assert isinstance(rule, SecurityPolicyRule)
        assert rule.priority == 1000
        assert rule.action == "deny(403)"

    def test_add_rule_minimal(self, service, sample_rule_response):
        """Test adding a rule with minimal parameters."""
        mock_add_request = mock.MagicMock()
        mock_add_rule = service.service.securityPolicies.return_value.addRule
        mock_add_rule.return_value = mock_add_request
        mock_add_request.execute.return_value = {}

        mock_get_request = mock.MagicMock()
        mock_get_rule = service.service.securityPolicies.return_value.getRule
        mock_get_rule.return_value = mock_get_request
        mock_get_request.execute.return_value = sample_rule_response

        match = {"versionedExpr": "SRC_IPS_V1", "config": {"srcIpRanges": ["*"]}}
        rule = service.add_rule(
            policy_name="my-security-policy",
            priority=1000,
            action="allow",
            match=match,
        )

        mock_add_rule.assert_called_once_with(
            project="test-project",
            securityPolicy="my-security-policy",
            body={
                "priority": 1000,
                "action": "allow",
                "match": match,
                "preview": False,
            },
        )
        assert isinstance(rule, SecurityPolicyRule)

    def test_add_rule_policy_not_found(self, service):
        """Test adding a rule to a nonexistent policy."""
        mock_request = mock.MagicMock()
        mock_add_rule = service.service.securityPolicies.return_value.addRule
        mock_add_rule.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.add_rule(
                policy_name="nonexistent",
                priority=1000,
                action="allow",
                match={"versionedExpr": "SRC_IPS_V1"},
            )

    def test_add_rule_api_error(self, service):
        """Test adding a rule with an API error."""
        mock_request = mock.MagicMock()
        mock_add_rule = service.service.securityPolicies.return_value.addRule
        mock_add_rule.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.add_rule(
                policy_name="my-policy",
                priority=1000,
                action="allow",
                match={},
            )


class TestRemoveRule:
    """Tests for removing rules from a security policy."""

    def test_remove_rule(self, service):
        """Test removing a rule from a security policy."""
        mock_request = mock.MagicMock()
        mock_remove = service.service.securityPolicies.return_value.removeRule
        mock_remove.return_value = mock_request
        mock_request.execute.return_value = {}

        result = service.remove_rule("my-security-policy", 1000)

        mock_remove.assert_called_once_with(
            project="test-project",
            securityPolicy="my-security-policy",
            priority=1000,
        )
        assert result is True

    def test_remove_rule_not_found(self, service):
        """Test removing a rule that does not exist."""
        mock_request = mock.MagicMock()
        mock_remove = service.service.securityPolicies.return_value.removeRule
        mock_remove.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.remove_rule("my-security-policy", 9999)


class TestGetRule:
    """Tests for getting a rule from a security policy."""

    def test_get_rule(self, service, sample_rule_response):
        """Test getting a specific rule."""
        mock_request = mock.MagicMock()
        mock_get_rule = service.service.securityPolicies.return_value.getRule
        mock_get_rule.return_value = mock_request
        mock_request.execute.return_value = sample_rule_response

        rule = service.get_rule("my-security-policy", 1000)

        mock_get_rule.assert_called_once_with(
            project="test-project",
            securityPolicy="my-security-policy",
            priority=1000,
        )
        assert isinstance(rule, SecurityPolicyRule)
        assert rule.priority == 1000
        assert rule.action == "deny(403)"
        assert rule.preview is True
        assert rule.policy_name == "my-security-policy"

    def test_get_rule_not_found(self, service):
        """Test getting a rule that does not exist."""
        mock_request = mock.MagicMock()
        mock_get_rule = service.service.securityPolicies.return_value.getRule
        mock_get_rule.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_rule("my-security-policy", 9999)

    def test_get_rule_api_error(self, service):
        """Test getting a rule with an API error."""
        mock_request = mock.MagicMock()
        mock_get_rule = service.service.securityPolicies.return_value.getRule
        mock_get_rule.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        with pytest.raises(APIError):
            service.get_rule("my-security-policy", 1000)


class TestPatchRule:
    """Tests for patching rules in a security policy."""

    def test_patch_rule(self, service, sample_rule_response):
        """Test patching a rule."""
        mock_patch_request = mock.MagicMock()
        mock_patch_rule = service.service.securityPolicies.return_value.patchRule
        mock_patch_rule.return_value = mock_patch_request
        mock_patch_request.execute.return_value = {}

        updated_rule_response = dict(sample_rule_response)
        updated_rule_response["action"] = "allow"
        mock_get_request = mock.MagicMock()
        mock_get_rule = service.service.securityPolicies.return_value.getRule
        mock_get_rule.return_value = mock_get_request
        mock_get_request.execute.return_value = updated_rule_response

        rule = service.patch_rule(
            policy_name="my-security-policy",
            priority=1000,
            action="allow",
            description="Updated rule",
        )

        mock_patch_rule.assert_called_once_with(
            project="test-project",
            securityPolicy="my-security-policy",
            priority=1000,
            body={"action": "allow", "description": "Updated rule"},
        )
        assert isinstance(rule, SecurityPolicyRule)
        assert rule.action == "allow"

    def test_patch_rule_preview_only(self, service, sample_rule_response):
        """Test patching only the preview setting."""
        mock_patch_request = mock.MagicMock()
        mock_patch_rule = service.service.securityPolicies.return_value.patchRule
        mock_patch_rule.return_value = mock_patch_request
        mock_patch_request.execute.return_value = {}

        mock_get_request = mock.MagicMock()
        mock_get_rule = service.service.securityPolicies.return_value.getRule
        mock_get_rule.return_value = mock_get_request
        mock_get_request.execute.return_value = sample_rule_response

        service.patch_rule(
            policy_name="my-security-policy",
            priority=1000,
            preview=False,
        )

        mock_patch_rule.assert_called_once_with(
            project="test-project",
            securityPolicy="my-security-policy",
            priority=1000,
            body={"preview": False},
        )

    def test_patch_rule_not_found(self, service):
        """Test patching a rule that does not exist."""
        mock_request = mock.MagicMock()
        mock_patch_rule = service.service.securityPolicies.return_value.patchRule
        mock_patch_rule.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.patch_rule(
                policy_name="my-security-policy",
                priority=9999,
                action="allow",
            )

    def test_patch_rule_with_match(self, service, sample_rule_response):
        """Test patching a rule with a new match condition."""
        mock_patch_request = mock.MagicMock()
        mock_patch_rule = service.service.securityPolicies.return_value.patchRule
        mock_patch_rule.return_value = mock_patch_request
        mock_patch_request.execute.return_value = {}

        mock_get_request = mock.MagicMock()
        mock_get_rule = service.service.securityPolicies.return_value.getRule
        mock_get_rule.return_value = mock_get_request
        mock_get_request.execute.return_value = sample_rule_response

        new_match = {
            "versionedExpr": "SRC_IPS_V1",
            "config": {"srcIpRanges": ["192.168.0.0/16"]},
        }
        service.patch_rule(
            policy_name="my-security-policy",
            priority=1000,
            match=new_match,
        )

        mock_patch_rule.assert_called_once_with(
            project="test-project",
            securityPolicy="my-security-policy",
            priority=1000,
            body={"match": new_match},
        )


class TestListRules:
    """Tests for listing rules in a security policy."""

    def test_list_rules(self, service, sample_policy_response):
        """Test listing rules in a security policy."""
        mock_request = mock.MagicMock()
        mock_get = service.service.securityPolicies.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_policy_response

        rules = service.list_rules("my-security-policy")

        assert len(rules) == 2
        assert isinstance(rules[0], SecurityPolicyRule)
        assert rules[0].priority == 2147483647
        assert rules[0].action == "allow"
        assert rules[1].priority == 1000
        assert rules[1].action == "deny(403)"
        assert rules[1].preview is True

    def test_list_rules_empty(self, service):
        """Test listing rules when none exist."""
        mock_request = mock.MagicMock()
        mock_get = service.service.securityPolicies.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.return_value = {
            "id": "123",
            "name": "empty-policy",
            "rules": [],
            "project": "test-project",
        }

        rules = service.list_rules("empty-policy")

        assert len(rules) == 0

    def test_list_rules_policy_not_found(self, service):
        """Test listing rules for a nonexistent policy."""
        mock_request = mock.MagicMock()
        mock_get = service.service.securityPolicies.return_value.get
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.list_rules("nonexistent-policy")


class TestSecurityPolicyModel:
    """Tests for the SecurityPolicy model."""

    def test_from_api_response(self, sample_policy_response):
        """Test creating a SecurityPolicy from an API response."""
        policy = SecurityPolicy.from_api_response(sample_policy_response)

        assert policy.id == "123456789"
        assert policy.name == "my-security-policy"
        assert policy.description == "My security policy"
        assert policy.type == "compute.securityPolicy"
        assert policy.project == "test-project"
        assert policy.fingerprint == "abc123def456"
        assert len(policy.rules) == 2
        assert policy.adaptive_protection_config is not None
        assert policy.labels == {"env": "production", "team": "security"}

    def test_from_api_response_minimal(self):
        """Test creating a SecurityPolicy from a minimal response."""
        policy = SecurityPolicy.from_api_response({"name": "simple-policy"})

        assert policy.name == "simple-policy"
        assert policy.description is None
        assert policy.rules == []
        assert policy.fingerprint is None
        assert policy.adaptive_protection_config is None

    def test_get_tag(self, sample_policy_response):
        """Test the get_tag method."""
        policy = SecurityPolicy.from_api_response(sample_policy_response)

        assert policy.get_tag("env") == "production"
        assert policy.get_tag("team") == "security"
        assert policy.get_tag("missing") == ""
        assert policy.get_tag("missing", "default") == "default"


class TestSecurityPolicyRuleModel:
    """Tests for the SecurityPolicyRule model."""

    def test_from_api_response(self, sample_rule_response):
        """Test creating a SecurityPolicyRule from an API response."""
        rule = SecurityPolicyRule.from_api_response(
            sample_rule_response, "my-security-policy"
        )

        assert rule.priority == 1000
        assert rule.action == "deny(403)"
        assert rule.preview is True
        assert rule.description == "Block internal IPs"
        assert rule.policy_name == "my-security-policy"
        assert rule.type == "compute.securityPolicyRule"
        assert rule.id == "my-security-policy/1000"
        assert rule.name == "rule-1000"
        assert rule.match == {
            "versionedExpr": "SRC_IPS_V1",
            "config": {"srcIpRanges": ["10.0.0.0/8"]},
        }

    def test_from_api_response_minimal(self):
        """Test creating a SecurityPolicyRule from a minimal response."""
        rule = SecurityPolicyRule.from_api_response(
            {"priority": 100, "action": "allow", "match": {}}
        )

        assert rule.priority == 100
        assert rule.action == "allow"
        assert rule.preview is False
        assert rule.description is None
        assert rule.rate_limit_options is None

    def test_from_api_response_with_rate_limit(self):
        """Test creating a SecurityPolicyRule with rate limit options."""
        response = {
            "priority": 500,
            "action": "throttle",
            "match": {"versionedExpr": "SRC_IPS_V1", "config": {"srcIpRanges": ["*"]}},
            "rateLimitOptions": {
                "rateLimitThreshold": {"count": 100, "intervalSec": 60},
                "conformAction": "allow",
                "exceedAction": "deny(429)",
            },
        }

        rule = SecurityPolicyRule.from_api_response(response, "my-policy")

        assert rule.action == "throttle"
        assert rule.rate_limit_options is not None
        assert rule.rate_limit_options["rateLimitThreshold"]["count"] == 100
