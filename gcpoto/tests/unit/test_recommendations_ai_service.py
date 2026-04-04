"""Tests for Recommendations AI service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.recommendations_ai import RecommendationsAIService
from gcpoto.models.recommendations_ai import CatalogItem, PredictionResult
from gcpoto.exceptions import ResourceNotFoundError, APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_catalog_items = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value = (
            mock_catalog_items
        )

        mock_placements = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.catalogs.return_value.placements.return_value = (
            mock_placements
        )

        yield mock_service


@pytest.fixture
def sample_catalog_item_response():
    """Sample Recommendations AI catalog item API response."""
    return {
        "name": "projects/test-project/locations/global/catalogs/default_catalog/catalogItems/item-1",
        "id": "item-1",
        "title": "Cool Product",
        "categoryHierarchies": [
            {"categories": ["Electronics", "Phones"]}
        ],
        "description": "A very cool product",
        "languageCode": "en",
        "productMetadata": {
            "exactPrice": {"displayPrice": 99.99, "originalPrice": 129.99}
        },
    }


@pytest.fixture
def sample_prediction_response():
    """Sample Recommendations AI prediction API response."""
    return {
        "results": [
            {"id": "item-2", "metadata": {"score": 0.95}},
            {"id": "item-3", "metadata": {"score": 0.88}},
        ],
        "attributionToken": "attr-token-abc",
        "missingIds": ["item-99"],
    }


# --- Model tests ---


class TestCatalogItemModel:
    def test_from_api_response(self, sample_catalog_item_response):
        item = CatalogItem.from_api_response(
            sample_catalog_item_response, "test-project"
        )
        assert item.id == "item-1"
        assert item.title == "Cool Product"
        assert item.project == "test-project"
        assert item.type == "recommendationengine.catalogItem"
        assert item.description == "A very cool product"
        assert item.language_code == "en"
        assert len(item.category_hierarchies) == 1
        assert item.category_hierarchies[0]["categories"] == [
            "Electronics",
            "Phones",
        ]
        assert item.product_metadata is not None

    def test_from_api_response_extracts_project(
        self, sample_catalog_item_response
    ):
        item = CatalogItem.from_api_response(sample_catalog_item_response)
        assert item.project == "test-project"

    def test_from_api_response_minimal(self):
        item = CatalogItem.from_api_response(
            {"id": "x", "title": "Minimal"}, "p"
        )
        assert item.id == "x"
        assert item.title == "Minimal"
        assert item.category_hierarchies is None
        assert item.description is None
        assert item.item_attributes is None
        assert item.language_code is None
        assert item.product_metadata is None

    def test_get_tag_default(self, sample_catalog_item_response):
        item = CatalogItem.from_api_response(
            sample_catalog_item_response, "test-project"
        )
        assert item.get_tag("missing") == ""
        assert item.get_tag("missing", "fallback") == "fallback"


class TestPredictionResultModel:
    def test_from_api_response(self, sample_prediction_response):
        result = PredictionResult.from_api_response(
            sample_prediction_response, "test-project"
        )
        assert len(result.results) == 2
        assert result.attribution_token == "attr-token-abc"
        assert result.missing_ids == ["item-99"]
        assert result.project == "test-project"
        assert result.type == "recommendationengine.predictionResult"

    def test_from_api_response_minimal(self):
        result = PredictionResult.from_api_response({}, "p")
        assert result.results == []
        assert result.attribution_token is None
        assert result.missing_ids is None

    def test_get_tag_default(self, sample_prediction_response):
        result = PredictionResult.from_api_response(
            sample_prediction_response, "test-project"
        )
        assert result.get_tag("missing") == ""
        assert result.get_tag("missing", "fallback") == "fallback"


# --- Service init tests ---


class TestRecommendationsAIServiceInit:
    def test_init(self, mock_google_client):
        from googleapiclient.discovery import build

        service = RecommendationsAIService(project_id="test-project")
        assert service.project_id == "test-project"
        build.assert_called_once_with(
            "recommendationengine", "v1beta1", credentials=None
        )

    def test_catalog_path(self, mock_google_client):
        service = RecommendationsAIService(project_id="test-project")
        assert service._catalog_path("global", "default_catalog") == (
            "projects/test-project/locations/global/catalogs/default_catalog"
        )

    def test_catalog_items_path(self, mock_google_client):
        service = RecommendationsAIService(project_id="test-project")
        assert service._catalog_items_path("global", "default_catalog") == (
            "projects/test-project/locations/global/catalogs/default_catalog/catalogItems"
        )

    def test_catalog_item_path(self, mock_google_client):
        service = RecommendationsAIService(project_id="test-project")
        assert service._catalog_item_path(
            "global", "default_catalog", "item-1"
        ) == (
            "projects/test-project/locations/global/catalogs/default_catalog/catalogItems/item-1"
        )


# --- List catalog items tests ---


class TestListCatalogItems:
    def test_list_catalog_items(
        self, mock_google_client, sample_catalog_item_response
    ):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {
            "catalogItems": [sample_catalog_item_response]
        }

        service = RecommendationsAIService(project_id="test-project")
        items = service.list_catalog_items("global")

        mock_list.assert_called_once_with(
            parent="projects/test-project/locations/global/catalogs/default_catalog/catalogItems"
        )
        assert len(items) == 1
        assert isinstance(items[0], CatalogItem)
        assert items[0].title == "Cool Product"

    def test_list_catalog_items_empty(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.return_value = {}

        service = RecommendationsAIService(project_id="test-project")
        items = service.list_catalog_items("global")
        assert items == []

    def test_list_catalog_items_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_list = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.list
        )
        mock_list.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = RecommendationsAIService(project_id="test-project")
        with pytest.raises(APIError):
            service.list_catalog_items("global")


# --- Get catalog item tests ---


class TestGetCatalogItem:
    def test_get_catalog_item(
        self, mock_google_client, sample_catalog_item_response
    ):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.return_value = sample_catalog_item_response

        service = RecommendationsAIService(project_id="test-project")
        item = service.get_catalog_item("global", "default_catalog", "item-1")

        mock_get.assert_called_once_with(
            name="projects/test-project/locations/global/catalogs/default_catalog/catalogItems/item-1"
        )
        assert isinstance(item, CatalogItem)
        assert item.title == "Cool Product"

    def test_get_catalog_item_not_found(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = RecommendationsAIService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.get_catalog_item("global", "default_catalog", "bad-id")

    def test_get_catalog_item_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_get = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.get
        )
        mock_get.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = RecommendationsAIService(project_id="test-project")
        with pytest.raises(APIError):
            service.get_catalog_item("global", "default_catalog", "item-1")


# --- Create catalog item tests ---


class TestCreateCatalogItem:
    def test_create_catalog_item(
        self, mock_google_client, sample_catalog_item_response
    ):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_catalog_item_response

        service = RecommendationsAIService(project_id="test-project")
        item = service.create_catalog_item(
            location="global",
            catalog="default_catalog",
            item_id="item-1",
            title="Cool Product",
            category_hierarchies=[{"categories": ["Electronics", "Phones"]}],
            description="A very cool product",
        )

        call_args = mock_create.call_args
        body = call_args[1]["body"]
        assert body["id"] == "item-1"
        assert body["title"] == "Cool Product"
        assert body["categoryHierarchies"] == [
            {"categories": ["Electronics", "Phones"]}
        ]
        assert body["description"] == "A very cool product"
        assert isinstance(item, CatalogItem)

    def test_create_catalog_item_minimal(
        self, mock_google_client, sample_catalog_item_response
    ):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.return_value = sample_catalog_item_response

        service = RecommendationsAIService(project_id="test-project")
        item = service.create_catalog_item(
            location="global",
            catalog="default_catalog",
            item_id="item-1",
            title="Cool Product",
        )

        call_args = mock_create.call_args
        body = call_args[1]["body"]
        assert "categoryHierarchies" not in body
        assert "description" not in body
        assert isinstance(item, CatalogItem)

    def test_create_catalog_item_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_create = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.create
        )
        mock_create.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=409), content=b"Already exists"
        )

        service = RecommendationsAIService(project_id="test-project")
        with pytest.raises(APIError):
            service.create_catalog_item(
                "global", "default_catalog", "item-1", "Title"
            )


# --- Update catalog item tests ---


class TestUpdateCatalogItem:
    def test_update_catalog_item(
        self, mock_google_client, sample_catalog_item_response
    ):
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.return_value = sample_catalog_item_response

        service = RecommendationsAIService(project_id="test-project")
        item = service.update_catalog_item(
            location="global",
            catalog="default_catalog",
            item_id="item-1",
            update_mask="title,description",
            update_fields={
                "title": "Updated Product",
                "description": "Updated description",
            },
        )

        mock_patch.assert_called_once_with(
            name="projects/test-project/locations/global/catalogs/default_catalog/catalogItems/item-1",
            updateMask="title,description",
            body={
                "title": "Updated Product",
                "description": "Updated description",
            },
        )
        assert isinstance(item, CatalogItem)

    def test_update_catalog_item_not_found(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_patch = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.patch
        )
        mock_patch.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = RecommendationsAIService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.update_catalog_item(
                "global", "default_catalog", "bad-id", "title", {"title": "X"}
            )


# --- Delete catalog item tests ---


class TestDeleteCatalogItem:
    def test_delete_catalog_item(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.return_value = {}

        service = RecommendationsAIService(project_id="test-project")
        result = service.delete_catalog_item(
            "global", "default_catalog", "item-1"
        )

        mock_delete.assert_called_once_with(
            name="projects/test-project/locations/global/catalogs/default_catalog/catalogItems/item-1"
        )
        assert result is True

    def test_delete_catalog_item_not_found(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_delete = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.delete
        )
        mock_delete.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=404), content=b"Not found"
        )

        service = RecommendationsAIService(project_id="test-project")
        with pytest.raises(ResourceNotFoundError):
            service.delete_catalog_item(
                "global", "default_catalog", "bad-id"
            )


# --- Import catalog items tests ---


class TestImportCatalogItems:
    def test_import_catalog_items(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_import = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.import_
        )
        mock_import.return_value = mock_request
        mock_request.execute.return_value = {
            "name": "projects/test-project/locations/global/catalogs/default_catalog/operations/op123",
            "done": False,
        }

        service = RecommendationsAIService(project_id="test-project")
        input_config = {
            "catalogInlineSource": {
                "catalogItems": [
                    {"id": "item-1", "title": "Product 1"},
                    {"id": "item-2", "title": "Product 2"},
                ]
            }
        }
        result = service.import_catalog_items(
            "global", "default_catalog", input_config
        )

        call_args = mock_import.call_args
        body = call_args[1]["body"]
        assert body["inputConfig"] == input_config
        assert result["done"] is False

    def test_import_catalog_items_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_import = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.catalogItems.return_value.import_
        )
        mock_import.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=400), content=b"Bad request"
        )

        service = RecommendationsAIService(project_id="test-project")
        with pytest.raises(APIError):
            service.import_catalog_items("global", "default_catalog", {})


# --- Predict tests ---


class TestPredict:
    def test_predict(
        self, mock_google_client, sample_prediction_response
    ):
        mock_request = mock.MagicMock()
        mock_predict = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.placements.return_value.predict
        )
        mock_predict.return_value = mock_request
        mock_request.execute.return_value = sample_prediction_response

        service = RecommendationsAIService(project_id="test-project")
        user_event = {
            "eventType": "detail-page-view",
            "userInfo": {"visitorId": "visitor-1"},
        }
        result = service.predict(
            location="global",
            catalog="default_catalog",
            placement_id="recently_viewed_default",
            user_event=user_event,
            page_size=5,
        )

        call_args = mock_predict.call_args
        assert call_args[1]["name"] == (
            "projects/test-project/locations/global/catalogs/default_catalog"
            "/placements/recently_viewed_default"
        )
        body = call_args[1]["body"]
        assert body["userEvent"] == user_event
        assert body["pageSize"] == 5
        assert isinstance(result, PredictionResult)
        assert len(result.results) == 2
        assert result.attribution_token == "attr-token-abc"
        assert result.missing_ids == ["item-99"]

    def test_predict_with_filter(
        self, mock_google_client, sample_prediction_response
    ):
        mock_request = mock.MagicMock()
        mock_predict = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.placements.return_value.predict
        )
        mock_predict.return_value = mock_request
        mock_request.execute.return_value = sample_prediction_response

        service = RecommendationsAIService(project_id="test-project")
        user_event = {
            "eventType": "home-page-view",
            "userInfo": {"visitorId": "visitor-2"},
        }
        result = service.predict(
            location="global",
            catalog="default_catalog",
            placement_id="home_page",
            user_event=user_event,
            filter_str="tag=\"sale\"",
        )

        call_args = mock_predict.call_args
        body = call_args[1]["body"]
        assert body["filter"] == "tag=\"sale\""
        assert isinstance(result, PredictionResult)

    def test_predict_minimal(
        self, mock_google_client, sample_prediction_response
    ):
        mock_request = mock.MagicMock()
        mock_predict = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.placements.return_value.predict
        )
        mock_predict.return_value = mock_request
        mock_request.execute.return_value = sample_prediction_response

        service = RecommendationsAIService(project_id="test-project")
        user_event = {
            "eventType": "detail-page-view",
            "userInfo": {"visitorId": "visitor-1"},
        }
        result = service.predict(
            location="global",
            catalog="default_catalog",
            placement_id="p1",
            user_event=user_event,
        )

        call_args = mock_predict.call_args
        body = call_args[1]["body"]
        assert "pageSize" not in body
        assert "filter" not in body
        assert isinstance(result, PredictionResult)

    def test_predict_api_error(self, mock_google_client):
        mock_request = mock.MagicMock()
        mock_predict = (
            mock_google_client.projects.return_value.locations.return_value.catalogs.return_value.placements.return_value.predict
        )
        mock_predict.return_value = mock_request
        mock_request.execute.side_effect = HttpError(
            resp=mock.MagicMock(status=500), content=b"Internal error"
        )

        service = RecommendationsAIService(project_id="test-project")
        with pytest.raises(APIError):
            service.predict(
                "global",
                "default_catalog",
                "p1",
                {"eventType": "x", "userInfo": {"visitorId": "v1"}},
            )
