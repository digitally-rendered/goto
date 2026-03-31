"""Tests for Dataplex service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.dataplex import DataplexService
from gcpoto.models.dataplex import Lake, Zone, Asset
from gcpoto.exceptions import ResourceNotFoundError, APIError


PROJECT_ID = "test-project"
LOCATION = "us-central1"
LAKE_ID = "my-lake"
ZONE_ID = "my-zone"
ASSET_ID = "my-asset"


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_lakes = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.lakes.return_value = (
            mock_lakes
        )

        mock_zones = mock.MagicMock()
        mock_lakes.zones.return_value = mock_zones

        mock_assets = mock.MagicMock()
        mock_zones.assets.return_value = mock_assets

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a DataplexService with mocked client."""
    return DataplexService(project_id=PROJECT_ID)


@pytest.fixture
def mock_lakes(mock_google_client):
    """Shortcut to mock lakes resource."""
    return (
        mock_google_client.projects.return_value.locations.return_value
        .lakes.return_value
    )


@pytest.fixture
def mock_zones(mock_lakes):
    """Shortcut to mock zones resource."""
    return mock_lakes.zones.return_value


@pytest.fixture
def mock_assets(mock_zones):
    """Shortcut to mock assets resource."""
    return mock_zones.assets.return_value


@pytest.fixture
def sample_lake_response():
    """Sample lake API response."""
    return {
        "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/lakes/{LAKE_ID}",
        "description": "Test lake",
        "state": "ACTIVE",
        "metastore": {"service": "projects/test/locations/us-central1/services/metastore1"},
        "createTime": "2026-03-31T10:00:00Z",
        "updateTime": "2026-03-31T11:00:00Z",
        "labels": {"env": "test"},
    }


@pytest.fixture
def sample_zone_response():
    """Sample zone API response."""
    return {
        "name": (
            f"projects/{PROJECT_ID}/locations/{LOCATION}"
            f"/lakes/{LAKE_ID}/zones/{ZONE_ID}"
        ),
        "type": "RAW",
        "description": "Test zone",
        "state": "ACTIVE",
        "discoverySpec": {"enabled": True},
        "resourceSpec": {"locationType": "SINGLE_REGION"},
        "createTime": "2026-03-31T10:00:00Z",
        "updateTime": "2026-03-31T11:00:00Z",
        "labels": {"env": "test"},
    }


@pytest.fixture
def sample_asset_response():
    """Sample asset API response."""
    return {
        "name": (
            f"projects/{PROJECT_ID}/locations/{LOCATION}"
            f"/lakes/{LAKE_ID}/zones/{ZONE_ID}/assets/{ASSET_ID}"
        ),
        "resourceSpec": {
            "type": "BIGQUERY_DATASET",
            "name": "projects/test/datasets/my_dataset",
        },
        "discoverySpec": {"enabled": True},
        "state": "ACTIVE",
        "createTime": "2026-03-31T10:00:00Z",
        "updateTime": "2026-03-31T11:00:00Z",
        "labels": {"env": "test"},
    }


class TestDataplexServiceInit:
    def test_init(self, mock_google_client):
        """Test initializing the DataplexService."""
        from googleapiclient.discovery import build

        svc = DataplexService(project_id=PROJECT_ID)
        assert svc.project_id == PROJECT_ID
        build.assert_called_once_with("dataplex", "v1", credentials=None)


class TestListLakes:
    def test_list_lakes(
        self, service, mock_lakes, sample_lake_response
    ):
        """Test listing lakes."""
        mock_request = mock.MagicMock()
        mock_lakes.list.return_value = mock_request
        mock_request.execute.return_value = {
            "lakes": [sample_lake_response]
        }
        mock_lakes.list_next.return_value = None

        results = service.list_lakes(LOCATION)

        mock_lakes.list.assert_called_once_with(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}"
        )
        assert len(results) == 1
        assert isinstance(results[0], Lake)
        assert results[0].description == "Test lake"

    def test_list_lakes_empty(self, service, mock_lakes):
        """Test listing lakes when none exist."""
        mock_request = mock.MagicMock()
        mock_lakes.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_lakes.list_next.return_value = None

        results = service.list_lakes(LOCATION)
        assert len(results) == 0


class TestGetLake:
    def test_get_lake(
        self, service, mock_lakes, sample_lake_response
    ):
        """Test getting a specific lake."""
        mock_request = mock.MagicMock()
        mock_lakes.get.return_value = mock_request
        mock_request.execute.return_value = sample_lake_response

        result = service.get_lake(LOCATION, LAKE_ID)

        assert isinstance(result, Lake)
        assert result.description == "Test lake"
        assert result.state == "ACTIVE"

    def test_get_lake_not_found(self, service, mock_lakes):
        """Test getting a lake that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_lakes.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_lake(LOCATION, LAKE_ID)


class TestCreateLake:
    def test_create_lake(
        self, service, mock_lakes, sample_lake_response
    ):
        """Test creating a new lake."""
        mock_request = mock.MagicMock()
        mock_lakes.create.return_value = mock_request
        mock_request.execute.return_value = sample_lake_response

        result = service.create_lake(
            LOCATION, LAKE_ID, description="Test lake"
        )

        assert isinstance(result, Lake)
        assert result.description == "Test lake"

    def test_create_lake_api_error(self, service, mock_lakes):
        """Test creating a lake when API returns an error."""
        mock_request = mock.MagicMock()
        mock_lakes.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_lake(LOCATION, LAKE_ID)


class TestUpdateLake:
    def test_update_lake(
        self, service, mock_lakes, sample_lake_response
    ):
        """Test updating a lake."""
        mock_request = mock.MagicMock()
        mock_lakes.patch.return_value = mock_request
        mock_request.execute.return_value = sample_lake_response

        result = service.update_lake(
            LOCATION,
            LAKE_ID,
            "description",
            {"description": "Updated"},
        )

        mock_lakes.patch.assert_called_once_with(
            name=f"projects/{PROJECT_ID}/locations/{LOCATION}/lakes/{LAKE_ID}",
            updateMask="description",
            body={"description": "Updated"},
        )
        assert isinstance(result, Lake)

    def test_update_lake_not_found(self, service, mock_lakes):
        """Test updating a lake that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_lakes.patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.update_lake(
                LOCATION, LAKE_ID, "description", {"description": "x"}
            )


class TestDeleteLake:
    def test_delete_lake(self, service, mock_lakes):
        """Test deleting a lake."""
        mock_lakes.delete.return_value.execute.return_value = {}

        result = service.delete_lake(LOCATION, LAKE_ID)
        assert result is True

    def test_delete_lake_not_found(self, service, mock_lakes):
        """Test deleting a lake that doesn't exist."""
        mock_lakes.delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_lake(LOCATION, LAKE_ID)


class TestListZones:
    def test_list_zones(
        self, service, mock_zones, sample_zone_response
    ):
        """Test listing zones."""
        mock_request = mock.MagicMock()
        mock_zones.list.return_value = mock_request
        mock_request.execute.return_value = {
            "zones": [sample_zone_response]
        }
        mock_zones.list_next.return_value = None

        results = service.list_zones(LOCATION, LAKE_ID)

        assert len(results) == 1
        assert isinstance(results[0], Zone)
        assert results[0].type_field == "RAW"

    def test_list_zones_empty(self, service, mock_zones):
        """Test listing zones when none exist."""
        mock_request = mock.MagicMock()
        mock_zones.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_zones.list_next.return_value = None

        results = service.list_zones(LOCATION, LAKE_ID)
        assert len(results) == 0


class TestGetZone:
    def test_get_zone(
        self, service, mock_zones, sample_zone_response
    ):
        """Test getting a specific zone."""
        mock_request = mock.MagicMock()
        mock_zones.get.return_value = mock_request
        mock_request.execute.return_value = sample_zone_response

        result = service.get_zone(LOCATION, LAKE_ID, ZONE_ID)

        assert isinstance(result, Zone)
        assert result.type_field == "RAW"
        assert result.state == "ACTIVE"

    def test_get_zone_not_found(self, service, mock_zones):
        """Test getting a zone that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_zones.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_zone(LOCATION, LAKE_ID, ZONE_ID)


class TestCreateZone:
    def test_create_zone(
        self, service, mock_zones, sample_zone_response
    ):
        """Test creating a new zone."""
        mock_request = mock.MagicMock()
        mock_zones.create.return_value = mock_request
        mock_request.execute.return_value = sample_zone_response

        result = service.create_zone(
            LOCATION, LAKE_ID, ZONE_ID, "RAW"
        )

        assert isinstance(result, Zone)
        assert result.type_field == "RAW"

    def test_create_zone_api_error(self, service, mock_zones):
        """Test creating a zone when API returns an error."""
        mock_request = mock.MagicMock()
        mock_zones.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_zone(
                LOCATION, LAKE_ID, ZONE_ID, "RAW"
            )


class TestDeleteZone:
    def test_delete_zone(self, service, mock_zones):
        """Test deleting a zone."""
        mock_zones.delete.return_value.execute.return_value = {}

        result = service.delete_zone(LOCATION, LAKE_ID, ZONE_ID)
        assert result is True

    def test_delete_zone_not_found(self, service, mock_zones):
        """Test deleting a zone that doesn't exist."""
        mock_zones.delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_zone(LOCATION, LAKE_ID, ZONE_ID)


class TestListAssets:
    def test_list_assets(
        self, service, mock_assets, sample_asset_response
    ):
        """Test listing assets."""
        mock_request = mock.MagicMock()
        mock_assets.list.return_value = mock_request
        mock_request.execute.return_value = {
            "assets": [sample_asset_response]
        }
        mock_assets.list_next.return_value = None

        results = service.list_assets(LOCATION, LAKE_ID, ZONE_ID)

        assert len(results) == 1
        assert isinstance(results[0], Asset)
        assert results[0].resource_spec is not None

    def test_list_assets_empty(self, service, mock_assets):
        """Test listing assets when none exist."""
        mock_request = mock.MagicMock()
        mock_assets.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_assets.list_next.return_value = None

        results = service.list_assets(LOCATION, LAKE_ID, ZONE_ID)
        assert len(results) == 0


class TestGetAsset:
    def test_get_asset(
        self, service, mock_assets, sample_asset_response
    ):
        """Test getting a specific asset."""
        mock_request = mock.MagicMock()
        mock_assets.get.return_value = mock_request
        mock_request.execute.return_value = sample_asset_response

        result = service.get_asset(
            LOCATION, LAKE_ID, ZONE_ID, ASSET_ID
        )

        assert isinstance(result, Asset)
        assert result.state == "ACTIVE"
        assert result.resource_spec is not None

    def test_get_asset_not_found(self, service, mock_assets):
        """Test getting an asset that doesn't exist."""
        mock_request = mock.MagicMock()
        mock_assets.get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.get_asset(
                LOCATION, LAKE_ID, ZONE_ID, ASSET_ID
            )


class TestCreateAsset:
    def test_create_asset(
        self, service, mock_assets, sample_asset_response
    ):
        """Test creating a new asset."""
        mock_request = mock.MagicMock()
        mock_assets.create.return_value = mock_request
        mock_request.execute.return_value = sample_asset_response

        result = service.create_asset(
            LOCATION,
            LAKE_ID,
            ZONE_ID,
            ASSET_ID,
            resource_spec={"type": "BIGQUERY_DATASET"},
        )

        assert isinstance(result, Asset)
        assert result.resource_spec is not None

    def test_create_asset_api_error(self, service, mock_assets):
        """Test creating an asset when API returns an error."""
        mock_request = mock.MagicMock()
        mock_assets.create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        with pytest.raises(APIError):
            service.create_asset(
                LOCATION, LAKE_ID, ZONE_ID, ASSET_ID, {}
            )


class TestDeleteAsset:
    def test_delete_asset(self, service, mock_assets):
        """Test deleting an asset."""
        mock_assets.delete.return_value.execute.return_value = {}

        result = service.delete_asset(
            LOCATION, LAKE_ID, ZONE_ID, ASSET_ID
        )
        assert result is True

    def test_delete_asset_not_found(self, service, mock_assets):
        """Test deleting an asset that doesn't exist."""
        mock_assets.delete.return_value.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        with pytest.raises(ResourceNotFoundError):
            service.delete_asset(
                LOCATION, LAKE_ID, ZONE_ID, ASSET_ID
            )


class TestLakeModel:
    def test_from_api_response(self, sample_lake_response):
        """Test creating a Lake from API response."""
        lake = Lake.from_api_response(sample_lake_response)

        assert lake.id == LAKE_ID
        assert lake.location == LOCATION
        assert lake.project == PROJECT_ID
        assert lake.description == "Test lake"
        assert lake.state == "ACTIVE"
        assert lake.metastore is not None
        assert lake.type == "dataplex.lake"

    def test_from_api_response_minimal(self):
        """Test creating a Lake from minimal API response."""
        response = {
            "name": f"projects/{PROJECT_ID}/locations/{LOCATION}/lakes/minimal"
        }
        lake = Lake.from_api_response(response)

        assert lake.id == "minimal"
        assert lake.description is None
        assert lake.state == ""

    def test_get_tag(self, sample_lake_response):
        """Test getting tags from a Lake."""
        lake = Lake.from_api_response(sample_lake_response)

        assert lake.get_tag("env") == "test"
        assert lake.get_tag("missing") == ""
        assert lake.get_tag("missing", "default") == "default"


class TestZoneModel:
    def test_from_api_response(self, sample_zone_response):
        """Test creating a Zone from API response."""
        zone = Zone.from_api_response(sample_zone_response)

        assert zone.id == ZONE_ID
        assert zone.lake_name == LAKE_ID
        assert zone.location == LOCATION
        assert zone.project == PROJECT_ID
        assert zone.type_field == "RAW"
        assert zone.description == "Test zone"
        assert zone.state == "ACTIVE"
        assert zone.discovery_spec is not None
        assert zone.resource_spec is not None
        assert zone.type == "dataplex.zone"

    def test_from_api_response_minimal(self):
        """Test creating a Zone from minimal API response."""
        response = {
            "name": (
                f"projects/{PROJECT_ID}/locations/{LOCATION}"
                f"/lakes/{LAKE_ID}/zones/minimal"
            )
        }
        zone = Zone.from_api_response(response)

        assert zone.id == "minimal"
        assert zone.type_field == ""
        assert zone.description is None


class TestAssetModel:
    def test_from_api_response(self, sample_asset_response):
        """Test creating an Asset from API response."""
        asset = Asset.from_api_response(sample_asset_response)

        assert asset.id == ASSET_ID
        assert asset.zone_name == ZONE_ID
        assert asset.lake_name == LAKE_ID
        assert asset.location == LOCATION
        assert asset.project == PROJECT_ID
        assert asset.resource_spec is not None
        assert asset.discovery_spec is not None
        assert asset.state == "ACTIVE"
        assert asset.type == "dataplex.asset"

    def test_from_api_response_minimal(self):
        """Test creating an Asset from minimal API response."""
        response = {
            "name": (
                f"projects/{PROJECT_ID}/locations/{LOCATION}"
                f"/lakes/{LAKE_ID}/zones/{ZONE_ID}/assets/minimal"
            )
        }
        asset = Asset.from_api_response(response)

        assert asset.id == "minimal"
        assert asset.resource_spec == {}
        assert asset.discovery_spec is None
