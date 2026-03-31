"""Service implementation for Google Cloud DNS."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.dns import ManagedZone, ResourceRecordSet
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class DNSService(GCPService[ManagedZone]):
    """Service for interacting with Google Cloud DNS."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Cloud DNS service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="dns",
            version="v1",
            credentials_file=credentials_file,
            resource_model=ManagedZone,
            **kwargs,
        )

    def list_zones(self, **kwargs) -> List[ManagedZone]:
        """List DNS managed zones in the project.

        Args:
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of ManagedZone instances
        """
        logger.info("Listing DNS managed zones for project %s", self.project_id)

        request = self.service.managedZones().list(
            project=self.project_id, **kwargs
        )

        zones = []
        while request is not None:
            response = request.execute()
            for zone_data in response.get("managedZones", []):
                zones.append(ManagedZone.from_api_response(zone_data))
            request = self.service.managedZones().list_next(request, response)

        logger.info("Found %s DNS managed zones", len(zones))
        return zones

    def get_zone(self, zone_name: str) -> ManagedZone:
        """Get a specific DNS managed zone by name.

        Args:
            zone_name: The name of the managed zone to retrieve

        Returns:
            A ManagedZone instance

        Raises:
            ResourceNotFoundError: If the zone does not exist
        """
        logger.info("Getting DNS managed zone %s", zone_name)

        try:
            request = self.service.managedZones().get(
                project=self.project_id, managedZone=zone_name
            )
            response = request.execute()
            return ManagedZone.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ManagedZone", zone_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_zone(
        self,
        zone_name: str,
        dns_name: str,
        description: str = "",
        visibility: str = "public",
        labels: Optional[Dict[str, str]] = None,
    ) -> ManagedZone:
        """Create a new DNS managed zone.

        Args:
            zone_name: The name of the managed zone to create
            dns_name: The DNS name of the zone (e.g. "example.com.")
            description: Optional description for the zone
            visibility: Zone visibility ("public" or "private")
            labels: Optional labels to apply to the zone

        Returns:
            A ManagedZone instance for the newly created zone

        Raises:
            ResourceAlreadyExistsError: If the zone already exists
            APIError: If the API call fails
        """
        logger.info("Creating DNS managed zone %s for %s", zone_name, dns_name)

        body = {
            "name": zone_name,
            "dnsName": dns_name,
            "description": description,
            "visibility": visibility,
        }

        if labels:
            body["labels"] = labels

        try:
            request = self.service.managedZones().create(
                project=self.project_id, body=body
            )
            response = request.execute()
            logger.info("Created DNS managed zone %s", zone_name)
            return ManagedZone.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"ManagedZone '{zone_name}' already exists"
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def delete_zone(self, zone_name: str) -> bool:
        """Delete a DNS managed zone.

        Args:
            zone_name: The name of the managed zone to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the zone does not exist
            APIError: If the API call fails
        """
        logger.info("Deleting DNS managed zone %s", zone_name)

        try:
            self.service.managedZones().delete(
                project=self.project_id, managedZone=zone_name
            ).execute()
            logger.info("Deleted DNS managed zone %s", zone_name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ManagedZone", zone_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def update_zone(
        self,
        zone_name: str,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> ManagedZone:
        """Update a DNS managed zone.

        Args:
            zone_name: The name of the managed zone to update
            description: Optional new description for the zone
            labels: Optional new labels for the zone

        Returns:
            A ManagedZone instance for the updated zone

        Raises:
            ResourceNotFoundError: If the zone does not exist
            APIError: If the API call fails
        """
        logger.info("Updating DNS managed zone %s", zone_name)

        body = {}
        if description is not None:
            body["description"] = description
        if labels is not None:
            body["labels"] = labels

        try:
            request = self.service.managedZones().patch(
                project=self.project_id, managedZone=zone_name, body=body
            )
            response = request.execute()
            logger.info("Updated DNS managed zone %s", zone_name)
            return ManagedZone.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("ManagedZone", zone_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def list_record_sets(self, zone_name: str, **kwargs) -> List[ResourceRecordSet]:
        """List resource record sets in a managed zone.

        Args:
            zone_name: The name of the managed zone
            **kwargs: Additional parameters to pass to the list request

        Returns:
            A list of ResourceRecordSet instances
        """
        logger.info(
            "Listing record sets for zone %s in project %s",
            zone_name,
            self.project_id,
        )

        request = self.service.resourceRecordSets().list(
            project=self.project_id, managedZone=zone_name, **kwargs
        )

        record_sets = []
        while request is not None:
            response = request.execute()
            for rrset_data in response.get("rrsets", []):
                record_sets.append(
                    ResourceRecordSet.from_api_response(rrset_data, zone_name)
                )
            request = self.service.resourceRecordSets().list_next(
                request, response
            )

        logger.info("Found %s record sets in zone %s", len(record_sets), zone_name)
        return record_sets

    def get_record_set(
        self, zone_name: str, name: str, type: str
    ) -> ResourceRecordSet:
        """Get a specific resource record set.

        Args:
            zone_name: The name of the managed zone
            name: The DNS name of the record set
            type: The record type (A, AAAA, CNAME, etc.)

        Returns:
            A ResourceRecordSet instance

        Raises:
            ResourceNotFoundError: If the record set does not exist
        """
        logger.info(
            "Getting record set %s (type %s) in zone %s", name, type, zone_name
        )

        try:
            request = self.service.resourceRecordSets().get(
                project=self.project_id,
                managedZone=zone_name,
                name=name,
                type=type,
            )
            response = request.execute()
            return ResourceRecordSet.from_api_response(response, zone_name)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "ResourceRecordSet", f"{name} ({type})"
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_record_set(
        self,
        zone_name: str,
        name: str,
        type: str,
        ttl: int,
        rrdatas: List[str],
    ) -> ResourceRecordSet:
        """Create a new resource record set in a managed zone.

        Args:
            zone_name: The name of the managed zone
            name: The DNS name for the record set
            type: The record type (A, AAAA, CNAME, etc.)
            ttl: Time to live in seconds
            rrdatas: List of resource record data strings

        Returns:
            A ResourceRecordSet instance for the newly created record

        Raises:
            ResourceAlreadyExistsError: If the record set already exists
            APIError: If the API call fails
        """
        logger.info(
            "Creating record set %s (type %s) in zone %s", name, type, zone_name
        )

        body = {
            "name": name,
            "type": type,
            "ttl": ttl,
            "rrdatas": rrdatas,
        }

        try:
            request = self.service.resourceRecordSets().create(
                project=self.project_id, managedZone=zone_name, body=body
            )
            response = request.execute()
            logger.info(
                "Created record set %s (type %s) in zone %s",
                name,
                type,
                zone_name,
            )
            return ResourceRecordSet.from_api_response(response, zone_name)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"ResourceRecordSet '{name}' (type {type}) already exists"
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def delete_record_set(
        self, zone_name: str, name: str, type: str
    ) -> bool:
        """Delete a resource record set from a managed zone.

        Args:
            zone_name: The name of the managed zone
            name: The DNS name of the record set to delete
            type: The record type (A, AAAA, CNAME, etc.)

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the record set does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Deleting record set %s (type %s) from zone %s",
            name,
            type,
            zone_name,
        )

        try:
            self.service.resourceRecordSets().delete(
                project=self.project_id,
                managedZone=zone_name,
                name=name,
                type=type,
            ).execute()
            logger.info(
                "Deleted record set %s (type %s) from zone %s",
                name,
                type,
                zone_name,
            )
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "ResourceRecordSet", f"{name} ({type})"
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def update_record_set(
        self,
        zone_name: str,
        name: str,
        type: str,
        ttl: Optional[int] = None,
        rrdatas: Optional[List[str]] = None,
    ) -> ResourceRecordSet:
        """Update a resource record set in a managed zone.

        Args:
            zone_name: The name of the managed zone
            name: The DNS name of the record set to update
            type: The record type (A, AAAA, CNAME, etc.)
            ttl: Optional new TTL in seconds
            rrdatas: Optional new list of resource record data strings

        Returns:
            A ResourceRecordSet instance for the updated record

        Raises:
            ResourceNotFoundError: If the record set does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Updating record set %s (type %s) in zone %s", name, type, zone_name
        )

        body = {
            "name": name,
            "type": type,
        }
        if ttl is not None:
            body["ttl"] = ttl
        if rrdatas is not None:
            body["rrdatas"] = rrdatas

        try:
            request = self.service.resourceRecordSets().patch(
                project=self.project_id,
                managedZone=zone_name,
                name=name,
                type=type,
                body=body,
            )
            response = request.execute()
            logger.info(
                "Updated record set %s (type %s) in zone %s",
                name,
                type,
                zone_name,
            )
            return ResourceRecordSet.from_api_response(response, zone_name)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError(
                    "ResourceRecordSet", f"{name} ({type})"
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))
