"""Service implementation for Google Cloud Certificate Manager."""

import logging
from typing import List, Optional, Dict, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcpoto.services.base import GCPService
from gcpoto.models.certificate_manager import Certificate, CertificateMap
from gcpoto.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    APIError,
    PermissionDeniedError,
    QuotaExceededError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class CertificateManagerService(GCPService[Certificate]):
    """Service for interacting with Google Cloud Certificate Manager."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Certificate Manager service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="certificatemanager",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Certificate,
            **kwargs,
        )

    def list_certificates(self, location: str) -> List[Certificate]:
        """List certificates in a location.

        Args:
            location: The location to list certificates in (e.g. "global")

        Returns:
            A list of Certificate instances
        """
        logger.info(
            "Listing certificates in location %s for project %s",
            location,
            self.project_id,
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        request = self.service.projects().locations().certificates().list(
            parent=parent
        )

        certificates = []
        while request is not None:
            response = request.execute()
            for cert_data in response.get("certificates", []):
                certificates.append(Certificate.from_api_response(cert_data))
            request = (
                self.service.projects()
                .locations()
                .certificates()
                .list_next(request, response)
            )

        logger.info("Found %s certificates", len(certificates))
        return certificates

    def get_certificate(
        self, location: str, cert_name: str
    ) -> Certificate:
        """Get a specific certificate.

        Args:
            location: The location of the certificate
            cert_name: The name of the certificate

        Returns:
            A Certificate instance

        Raises:
            ResourceNotFoundError: If the certificate does not exist
        """
        logger.info("Getting certificate %s in location %s", cert_name, location)

        name = f"projects/{self.project_id}/locations/{location}/certificates/{cert_name}"

        try:
            request = (
                self.service.projects()
                .locations()
                .certificates()
                .get(name=name)
            )
            response = request.execute()
            return Certificate.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("Certificate", cert_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_certificate(
        self,
        location: str,
        cert_name: str,
        managed: Optional[Dict[str, Any]] = None,
        self_managed: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Certificate:
        """Create a certificate.

        Args:
            location: The location to create the certificate in
            cert_name: The name for the certificate
            managed: Managed certificate configuration
            self_managed: Self-managed certificate configuration
            description: Optional description for the certificate
            labels: Optional labels to apply to the certificate

        Returns:
            The created Certificate instance

        Raises:
            ResourceAlreadyExistsError: If the certificate already exists
            APIError: If the API call fails
        """
        logger.info(
            "Creating certificate %s in location %s", cert_name, location
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        body = {}

        if managed:
            body["managed"] = managed
        if self_managed:
            body["selfManaged"] = self_managed
        if description:
            body["description"] = description
        if labels:
            body["labels"] = labels

        try:
            request = (
                self.service.projects()
                .locations()
                .certificates()
                .create(
                    parent=parent,
                    certificateId=cert_name,
                    body=body,
                )
            )
            response = request.execute()
            logger.info("Created certificate %s", cert_name)
            return Certificate.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"Certificate '{cert_name}' already exists"
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def delete_certificate(self, location: str, cert_name: str) -> bool:
        """Delete a certificate.

        Args:
            location: The location of the certificate
            cert_name: The name of the certificate to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the certificate does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Deleting certificate %s in location %s", cert_name, location
        )

        name = f"projects/{self.project_id}/locations/{location}/certificates/{cert_name}"

        try:
            self.service.projects().locations().certificates().delete(
                name=name
            ).execute()
            logger.info("Deleted certificate %s", cert_name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("Certificate", cert_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def list_certificate_maps(self, location: str) -> List[CertificateMap]:
        """List certificate maps in a location.

        Args:
            location: The location to list certificate maps in

        Returns:
            A list of CertificateMap instances
        """
        logger.info(
            "Listing certificate maps in location %s for project %s",
            location,
            self.project_id,
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        request = (
            self.service.projects()
            .locations()
            .certificateMaps()
            .list(parent=parent)
        )

        maps = []
        while request is not None:
            response = request.execute()
            for map_data in response.get("certificateMaps", []):
                maps.append(CertificateMap.from_api_response(map_data))
            request = (
                self.service.projects()
                .locations()
                .certificateMaps()
                .list_next(request, response)
            )

        logger.info("Found %s certificate maps", len(maps))
        return maps

    def get_certificate_map(
        self, location: str, map_name: str
    ) -> CertificateMap:
        """Get a specific certificate map.

        Args:
            location: The location of the certificate map
            map_name: The name of the certificate map

        Returns:
            A CertificateMap instance

        Raises:
            ResourceNotFoundError: If the certificate map does not exist
        """
        logger.info(
            "Getting certificate map %s in location %s", map_name, location
        )

        name = f"projects/{self.project_id}/locations/{location}/certificateMaps/{map_name}"

        try:
            request = (
                self.service.projects()
                .locations()
                .certificateMaps()
                .get(name=name)
            )
            response = request.execute()
            return CertificateMap.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("CertificateMap", map_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def create_certificate_map(
        self,
        location: str,
        map_name: str,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> CertificateMap:
        """Create a certificate map.

        Args:
            location: The location to create the certificate map in
            map_name: The name for the certificate map
            description: Optional description for the certificate map
            labels: Optional labels to apply to the certificate map

        Returns:
            The created CertificateMap instance

        Raises:
            ResourceAlreadyExistsError: If the certificate map already exists
            APIError: If the API call fails
        """
        logger.info(
            "Creating certificate map %s in location %s", map_name, location
        )

        parent = f"projects/{self.project_id}/locations/{location}"
        body = {}

        if description:
            body["description"] = description
        if labels:
            body["labels"] = labels

        try:
            request = (
                self.service.projects()
                .locations()
                .certificateMaps()
                .create(
                    parent=parent,
                    certificateMapId=map_name,
                    body=body,
                )
            )
            response = request.execute()
            logger.info("Created certificate map %s", map_name)
            return CertificateMap.from_api_response(response)
        except HttpError as e:
            if e.resp.status == 409:
                raise ResourceAlreadyExistsError(
                    f"CertificateMap '{map_name}' already exists"
                )
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))

    def delete_certificate_map(
        self, location: str, map_name: str
    ) -> bool:
        """Delete a certificate map.

        Args:
            location: The location of the certificate map
            map_name: The name of the certificate map to delete

        Returns:
            True if the deletion was successful

        Raises:
            ResourceNotFoundError: If the certificate map does not exist
            APIError: If the API call fails
        """
        logger.info(
            "Deleting certificate map %s in location %s", map_name, location
        )

        name = f"projects/{self.project_id}/locations/{location}/certificateMaps/{map_name}"

        try:
            self.service.projects().locations().certificateMaps().delete(
                name=name
            ).execute()
            logger.info("Deleted certificate map %s", map_name)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                raise ResourceNotFoundError("CertificateMap", map_name)
            if e.resp.status == 403:
                raise PermissionDeniedError(e.resp.status, str(e))
            if e.resp.status == 429:
                raise QuotaExceededError(e.resp.status, str(e))
            if e.resp.status == 503:
                raise ServiceUnavailableError(e.resp.status, str(e))
            raise APIError(e.resp.status, str(e))
