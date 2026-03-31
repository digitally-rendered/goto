"""Models for Google Cloud NAT resources."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from gcpoto.models.base import GCPResource
from gcpoto.schemas.cloud_nat import get_schema


class NATConfig(GCPResource):
    """Model for a Google Cloud NAT configuration."""

    region: str = Field("", description="The region of the NAT config")
    router_name: str = Field(
        "", description="The name of the Cloud Router hosting this NAT"
    )
    nat_ip_allocate_option: str = Field(
        "AUTO_ONLY",
        description="NAT IP allocation option (AUTO_ONLY or MANUAL_ONLY)",
    )
    source_subnetwork_ip_ranges_to_nat: str = Field(
        "ALL_SUBNETWORKS_ALL_IP_RANGES",
        description="Subnetwork IP ranges to NAT",
    )
    subnetworks: Optional[List[Dict[str, Any]]] = Field(
        None, description="Subnetworks to NAT if using specific subnetworks"
    )
    nat_ips: Optional[List[str]] = Field(
        None, description="NAT IP addresses for MANUAL_ONLY allocation"
    )
    min_ports_per_vm: Optional[int] = Field(
        None, description="Minimum number of ports per VM"
    )
    log_config: Optional[Dict[str, Any]] = Field(
        None, description="Logging configuration for the NAT"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"schema": get_schema()}

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "NATConfig":
        """Create a NATConfig from an API response.

        Args:
            response: The API response dictionary

        Returns:
            A new NATConfig instance
        """
        instance = cls(
            id=response.get("name", ""),
            name=response.get("name", ""),
            type="compute.natConfig",
            project=response.get("project", ""),
            region=response.get("region", ""),
            router_name=response.get("routerName", ""),
            nat_ip_allocate_option=response.get(
                "natIpAllocateOption", "AUTO_ONLY"
            ),
            source_subnetwork_ip_ranges_to_nat=response.get(
                "sourceSubnetworkIpRangesToNat",
                "ALL_SUBNETWORKS_ALL_IP_RANGES",
            ),
            subnetworks=response.get("subnetworks"),
            nat_ips=response.get("natIps"),
            min_ports_per_vm=response.get("minPortsPerVm"),
            log_config=response.get("logConfig"),
            created=response.get("creationTimestamp"),
            updated=response.get("updateTime"),
        )
        return instance
