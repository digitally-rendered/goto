"""Models for Google Cloud Binary Authorization resources."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.binary_auth import get_schema


class Policy(GCPResource):
    """Model for a Binary Authorization Policy."""

    global_policy_evaluation_mode: Optional[str] = Field(
        None, description="The global policy evaluation mode"
    )
    default_admission_rule: Dict[str, Any] = Field(
        default_factory=dict,
        description="The default admission rule for the policy",
    )
    cluster_admission_rules: Optional[Dict[str, Any]] = Field(
        None, description="Per-cluster admission rules"
    )
    istio_service_identity_admission_rules: Optional[Dict[str, Any]] = Field(
        None, description="Per-Istio-service-identity admission rules"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("policy")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Policy":
        """Create a Policy from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Policy instance
        """
        return cls(
            id=response.get("name", "").split("/")[-1]
            if response.get("name")
            else "",
            name=response.get("name", ""),
            type="binaryauthorization.policy",
            project=response.get("name", "").split("/")[1]
            if len(response.get("name", "").split("/")) > 1
            else "",
            global_policy_evaluation_mode=response.get(
                "globalPolicyEvaluationMode"
            ),
            default_admission_rule=response.get("defaultAdmissionRule", {}),
            cluster_admission_rules=response.get("clusterAdmissionRules"),
            istio_service_identity_admission_rules=response.get(
                "istioServiceIdentityAdmissionRules"
            ),
            updated=response.get("updateTime"),
        )


class Attestor(GCPResource):
    """Model for a Binary Authorization Attestor."""

    description: Optional[str] = Field(
        None, description="A description of the attestor"
    )
    user_owned_grafeas_note: Optional[Dict[str, Any]] = Field(
        None, description="A Grafeas note reference for the attestor"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema("attestor")}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "Attestor":
        """Create an Attestor from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new Attestor instance
        """
        return cls(
            id=response.get("name", "").split("/")[-1]
            if response.get("name")
            else "",
            name=response.get("name", ""),
            type="binaryauthorization.attestor",
            project=response.get("name", "").split("/")[1]
            if len(response.get("name", "").split("/")) > 1
            else "",
            description=response.get("description"),
            user_owned_grafeas_note=response.get("userOwnedGrafeasNote"),
            created=response.get("createTime"),
            updated=response.get("updateTime"),
        )
