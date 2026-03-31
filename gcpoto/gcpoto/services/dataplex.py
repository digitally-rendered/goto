"""Service implementation for Google Cloud Dataplex."""

import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.dataplex import Lake, Zone, Asset

logger = logging.getLogger(__name__)

class DataplexService(GCPService[Lake]):
    """Service for interacting with Google Cloud Dataplex."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Dataplex service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="dataplex",
            version="v1",
            credentials_file=credentials_file,
            resource_model=Lake,
            **kwargs,
        )

    # ---- Lake operations ----

    def list_lakes(self, location: str) -> List[Lake]:
        """List lakes in a location.

        Args:
            location: The GCP location (e.g. 'us-central1')

        Returns:
            A list of Lake instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        request = (
            self.service.projects()
            .locations()
            .lakes()
            .list(parent=parent)
        )

        lakes = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("lakes", []):
                lakes.append(
                    Lake.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .lakes()
                .list_next(request, response)
            )

        logger.debug("Listed %s lakes in %s", len(lakes), location)
        return lakes

    def get_lake(self, location: str, lake_id: str) -> Lake:
        """Get a specific lake.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID of the lake

        Returns:
            A Lake instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/lakes/{lake_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .lakes()
            .get(name=name)
        )
        response = self._execute(request, "lake", lake_id)
        logger.debug("Retrieved lake %s", lake_id)
        return Lake.from_api_response(response, self.project_id)

    def create_lake(
        self,
        location: str,
        lake_id: str,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Lake:
        """Create a new lake.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID for the new lake
            description: Optional description for the lake
            labels: Optional labels for the lake

        Returns:
            The created Lake instance
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        body: Dict[str, Any] = {}

        if description is not None:
            body["description"] = description

        if labels is not None:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .lakes()
            .create(
                parent=parent,
                lakeId=lake_id,
                body=body,
            )
        )
        response = self._execute(request)
        logger.debug("Created lake %s in %s", lake_id, location)
        return Lake.from_api_response(response, self.project_id)

    def update_lake(
        self,
        location: str,
        lake_id: str,
        update_mask: str,
        update_fields: Dict[str, Any],
    ) -> Lake:
        """Update a lake.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID of the lake to update
            update_mask: Comma-separated list of fields to update
            update_fields: The fields to update

        Returns:
            The updated Lake instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/lakes/{lake_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .lakes()
            .patch(
                name=name,
                updateMask=update_mask,
                body=update_fields,
            )
        )
        response = self._execute(request, "lake", lake_id)
        logger.debug("Updated lake %s", lake_id)
        return Lake.from_api_response(response, self.project_id)

    def delete_lake(self, location: str, lake_id: str) -> bool:
        """Delete a lake.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID of the lake to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/lakes/{lake_id}"
        )
        self.service.projects().locations().lakes().delete(
            name=name
        ).execute()
        logger.debug("Deleted lake %s", lake_id)
        return True

    # ---- Zone operations ----

    def list_zones(self, location: str, lake_id: str) -> List[Zone]:
        """List zones in a lake.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID of the parent lake

        Returns:
            A list of Zone instances
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/lakes/{lake_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .lakes()
            .zones()
            .list(parent=parent)
        )

        zones = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("zones", []):
                zones.append(
                    Zone.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .lakes()
                .zones()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s zones in lake %s", len(zones), lake_id
        )
        return zones

    def get_zone(
        self, location: str, lake_id: str, zone_id: str
    ) -> Zone:
        """Get a specific zone.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID of the parent lake
            zone_id: The ID of the zone

        Returns:
            A Zone instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/lakes/{lake_id}/zones/{zone_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .lakes()
            .zones()
            .get(name=name)
        )
        response = self._execute(request, "zone", zone_id)
        logger.debug("Retrieved zone %s", zone_id)
        return Zone.from_api_response(response, self.project_id)

    def create_zone(
        self,
        location: str,
        lake_id: str,
        zone_id: str,
        type_field: str,
        resource_spec: Optional[Dict[str, Any]] = None,
        discovery_spec: Optional[Dict[str, Any]] = None,
    ) -> Zone:
        """Create a new zone in a lake.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID of the parent lake
            zone_id: The ID for the new zone
            type_field: The zone type (RAW or CURATED)
            resource_spec: Optional resource specification
            discovery_spec: Optional discovery specification

        Returns:
            The created Zone instance
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/lakes/{lake_id}"
        )
        body: Dict[str, Any] = {"type": type_field}

        if resource_spec is not None:
            body["resourceSpec"] = resource_spec

        if discovery_spec is not None:
            body["discoverySpec"] = discovery_spec

        request = (
            self.service.projects()
            .locations()
            .lakes()
            .zones()
            .create(
                parent=parent,
                zoneId=zone_id,
                body=body,
            )
        )
        response = self._execute(request)
        logger.debug(
            "Created zone %s in lake %s", zone_id, lake_id
        )
        return Zone.from_api_response(response, self.project_id)

    def delete_zone(
        self, location: str, lake_id: str, zone_id: str
    ) -> bool:
        """Delete a zone.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID of the parent lake
            zone_id: The ID of the zone to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/lakes/{lake_id}/zones/{zone_id}"
        )
        self.service.projects().locations().lakes().zones().delete(
            name=name
        ).execute()
        logger.debug("Deleted zone %s", zone_id)
        return True

    # ---- Asset operations ----

    def list_assets(
        self, location: str, lake_id: str, zone_id: str
    ) -> List[Asset]:
        """List assets in a zone.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID of the parent lake
            zone_id: The ID of the parent zone

        Returns:
            A list of Asset instances
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/lakes/{lake_id}/zones/{zone_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .lakes()
            .zones()
            .assets()
            .list(parent=parent)
        )

        assets = []
        while request is not None:
            response = self._execute(request)
            for item in response.get("assets", []):
                assets.append(
                    Asset.from_api_response(item, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .lakes()
                .zones()
                .assets()
                .list_next(request, response)
            )

        logger.debug(
            "Listed %s assets in zone %s", len(assets), zone_id
        )
        return assets

    def get_asset(
        self,
        location: str,
        lake_id: str,
        zone_id: str,
        asset_id: str,
    ) -> Asset:
        """Get a specific asset.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID of the parent lake
            zone_id: The ID of the parent zone
            asset_id: The ID of the asset

        Returns:
            An Asset instance
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/lakes/{lake_id}/zones/{zone_id}/assets/{asset_id}"
        )
        request = (
            self.service.projects()
            .locations()
            .lakes()
            .zones()
            .assets()
            .get(name=name)
        )
        response = self._execute(request, "asset", asset_id)
        logger.debug("Retrieved asset %s", asset_id)
        return Asset.from_api_response(response, self.project_id)

    def create_asset(
        self,
        location: str,
        lake_id: str,
        zone_id: str,
        asset_id: str,
        resource_spec: Dict[str, Any],
        discovery_spec: Optional[Dict[str, Any]] = None,
    ) -> Asset:
        """Create a new asset in a zone.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID of the parent lake
            zone_id: The ID of the parent zone
            asset_id: The ID for the new asset
            resource_spec: The resource specification
            discovery_spec: Optional discovery specification

        Returns:
            The created Asset instance
        """
        parent = (
            f"projects/{self.project_id}/locations/{location}"
            f"/lakes/{lake_id}/zones/{zone_id}"
        )
        body: Dict[str, Any] = {"resourceSpec": resource_spec}

        if discovery_spec is not None:
            body["discoverySpec"] = discovery_spec

        request = (
            self.service.projects()
            .locations()
            .lakes()
            .zones()
            .assets()
            .create(
                parent=parent,
                assetId=asset_id,
                body=body,
            )
        )
        response = self._execute(request)
        logger.debug(
            "Created asset %s in zone %s", asset_id, zone_id
        )
        return Asset.from_api_response(response, self.project_id)

    def delete_asset(
        self,
        location: str,
        lake_id: str,
        zone_id: str,
        asset_id: str,
    ) -> bool:
        """Delete an asset.

        Args:
            location: The GCP location (e.g. 'us-central1')
            lake_id: The ID of the parent lake
            zone_id: The ID of the parent zone
            asset_id: The ID of the asset to delete

        Returns:
            True if deletion was successful
        """
        name = (
            f"projects/{self.project_id}/locations/{location}"
            f"/lakes/{lake_id}/zones/{zone_id}/assets/{asset_id}"
        )
        (
            self.service.projects()
            .locations()
            .lakes()
            .zones()
            .assets()
            .delete(name=name)
            .execute()
        )
        logger.debug("Deleted asset %s", asset_id)
        return True
