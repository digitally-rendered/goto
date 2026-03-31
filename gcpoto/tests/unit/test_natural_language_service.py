"""Tests for Natural Language service."""

from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.natural_language import NaturalLanguageService
from gcpoto.models.natural_language import NLResult
from gcpoto.exceptions import APIError


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        mock_documents = mock.MagicMock()
        mock_service.documents.return_value = mock_documents

        yield mock_service


@pytest.fixture
def service(mock_google_client):
    """Create a NaturalLanguageService with mocked client."""
    return NaturalLanguageService(project_id="test-project")


@pytest.fixture
def sample_sentiment_response():
    """Sample Natural Language sentiment analysis API response."""
    return {
        "documentSentiment": {
            "magnitude": 0.8,
            "score": 0.7,
        },
        "sentences": [
            {
                "text": {"content": "I love this product.", "beginOffset": 0},
                "sentiment": {"magnitude": 0.8, "score": 0.7},
            }
        ],
    }


@pytest.fixture
def sample_entities_response():
    """Sample Natural Language entity analysis API response."""
    return {
        "entities": [
            {
                "name": "Google",
                "type": "ORGANIZATION",
                "salience": 0.85,
                "mentions": [
                    {
                        "text": {"content": "Google", "beginOffset": 0},
                        "type": "PROPER",
                    }
                ],
                "metadata": {"mid": "/m/045c7b", "wikipedia_url": "https://en.wikipedia.org/wiki/Google"},
            }
        ],
    }


@pytest.fixture
def sample_syntax_response():
    """Sample Natural Language syntax analysis API response."""
    return {
        "sentences": [
            {
                "text": {"content": "Hello world.", "beginOffset": 0},
            }
        ],
        "tokens": [
            {
                "text": {"content": "Hello", "beginOffset": 0},
                "partOfSpeech": {"tag": "X"},
                "dependencyEdge": {"headTokenIndex": 1, "label": "DISCOURSE"},
                "lemma": "Hello",
            },
            {
                "text": {"content": "world", "beginOffset": 6},
                "partOfSpeech": {"tag": "NOUN"},
                "dependencyEdge": {"headTokenIndex": 1, "label": "ROOT"},
                "lemma": "world",
            },
        ],
    }


@pytest.fixture
def sample_classify_response():
    """Sample Natural Language text classification API response."""
    return {
        "categories": [
            {
                "name": "/Science/Computer Science",
                "confidence": 0.92,
            },
            {
                "name": "/Technology",
                "confidence": 0.85,
            },
        ],
    }


@pytest.fixture
def sample_annotate_response():
    """Sample Natural Language annotateText API response."""
    return {
        "sentences": [
            {
                "text": {"content": "Google is great.", "beginOffset": 0},
                "sentiment": {"magnitude": 0.6, "score": 0.6},
            }
        ],
        "tokens": [
            {
                "text": {"content": "Google", "beginOffset": 0},
                "partOfSpeech": {"tag": "NOUN"},
                "lemma": "Google",
            }
        ],
        "entities": [
            {
                "name": "Google",
                "type": "ORGANIZATION",
                "salience": 0.9,
            }
        ],
        "documentSentiment": {
            "magnitude": 0.6,
            "score": 0.6,
        },
        "categories": [
            {
                "name": "/Technology",
                "confidence": 0.88,
            }
        ],
    }


def _make_http_error(status_code, reason="error"):
    """Create a mock HttpError with the given status code."""
    resp = mock.MagicMock()
    resp.status = status_code
    return HttpError(
        resp, b'{"error": {"message": "' + reason.encode() + b'"}}'
    )


# ---- NLResult Model Tests ----


class TestNLResultModel:
    def test_from_api_response_sentiment(self, sample_sentiment_response):
        result = NLResult.from_api_response(sample_sentiment_response)
        assert result.type == "natural_language.result"
        assert result.sentiment is not None
        assert result.sentiment["score"] == 0.7
        assert result.sentiment["magnitude"] == 0.8
        assert result.sentences is not None
        assert len(result.sentences) == 1

    def test_from_api_response_entities(self, sample_entities_response):
        result = NLResult.from_api_response(sample_entities_response)
        assert result.entities is not None
        assert len(result.entities) == 1
        assert result.entities[0]["name"] == "Google"
        assert result.entities[0]["type"] == "ORGANIZATION"

    def test_from_api_response_minimal(self):
        response = {}
        result = NLResult.from_api_response(response)
        assert result.type == "natural_language.result"
        assert result.sentences is None
        assert result.tokens is None
        assert result.entities is None
        assert result.sentiment is None
        assert result.categories is None


# ---- NaturalLanguageService Sentiment Tests ----


class TestNaturalLanguageServiceSentiment:
    def test_analyze_sentiment(self, service, sample_sentiment_response):
        mock_documents = service.service.documents()
        mock_documents.analyzeSentiment().execute.return_value = (
            sample_sentiment_response
        )

        result = service.analyze_sentiment("I love this product.")
        assert isinstance(result, NLResult)
        assert result.sentiment is not None
        assert result.sentiment["score"] == 0.7

    def test_analyze_sentiment_with_language(
        self, service, sample_sentiment_response
    ):
        mock_documents = service.service.documents()
        mock_documents.analyzeSentiment().execute.return_value = (
            sample_sentiment_response
        )

        result = service.analyze_sentiment(
            "I love this product.", language="en"
        )
        assert isinstance(result, NLResult)

    def test_analyze_sentiment_html(self, service, sample_sentiment_response):
        mock_documents = service.service.documents()
        mock_documents.analyzeSentiment().execute.return_value = (
            sample_sentiment_response
        )

        result = service.analyze_sentiment(
            "<p>I love this product.</p>", content_type="HTML"
        )
        assert isinstance(result, NLResult)

    def test_analyze_sentiment_api_error(self, service):
        mock_documents = service.service.documents()
        mock_documents.analyzeSentiment().execute.side_effect = (
            _make_http_error(400)
        )

        with pytest.raises(APIError):
            service.analyze_sentiment("test")


# ---- NaturalLanguageService Entities Tests ----


class TestNaturalLanguageServiceEntities:
    def test_analyze_entities(self, service, sample_entities_response):
        mock_documents = service.service.documents()
        mock_documents.analyzeEntities().execute.return_value = (
            sample_entities_response
        )

        result = service.analyze_entities("Google is a technology company.")
        assert isinstance(result, NLResult)
        assert result.entities is not None
        assert result.entities[0]["name"] == "Google"

    def test_analyze_entities_api_error(self, service):
        mock_documents = service.service.documents()
        mock_documents.analyzeEntities().execute.side_effect = (
            _make_http_error(500)
        )

        with pytest.raises(APIError):
            service.analyze_entities("test")


# ---- NaturalLanguageService Syntax Tests ----


class TestNaturalLanguageServiceSyntax:
    def test_analyze_syntax(self, service, sample_syntax_response):
        mock_documents = service.service.documents()
        mock_documents.analyzeSyntax().execute.return_value = (
            sample_syntax_response
        )

        result = service.analyze_syntax("Hello world.")
        assert isinstance(result, NLResult)
        assert result.tokens is not None
        assert len(result.tokens) == 2
        assert result.sentences is not None

    def test_analyze_syntax_api_error(self, service):
        mock_documents = service.service.documents()
        mock_documents.analyzeSyntax().execute.side_effect = (
            _make_http_error(400)
        )

        with pytest.raises(APIError):
            service.analyze_syntax("test")


# ---- NaturalLanguageService Classify Tests ----


class TestNaturalLanguageServiceClassify:
    def test_classify_text(self, service, sample_classify_response):
        mock_documents = service.service.documents()
        mock_documents.classifyText().execute.return_value = (
            sample_classify_response
        )

        result = service.classify_text(
            "Python is a popular programming language."
        )
        assert isinstance(result, NLResult)
        assert result.categories is not None
        assert len(result.categories) == 2
        assert result.categories[0]["name"] == "/Science/Computer Science"

    def test_classify_text_api_error(self, service):
        mock_documents = service.service.documents()
        mock_documents.classifyText().execute.side_effect = (
            _make_http_error(400)
        )

        with pytest.raises(APIError):
            service.classify_text("test")


# ---- NaturalLanguageService Annotate Tests ----


class TestNaturalLanguageServiceAnnotate:
    def test_annotate_text(self, service, sample_annotate_response):
        mock_documents = service.service.documents()
        mock_documents.annotateText().execute.return_value = (
            sample_annotate_response
        )

        features = {
            "extractSyntax": True,
            "extractEntities": True,
            "extractDocumentSentiment": True,
            "classifyText": True,
        }
        result = service.annotate_text("Google is great.", features=features)
        assert isinstance(result, NLResult)
        assert result.sentences is not None
        assert result.tokens is not None
        assert result.entities is not None
        assert result.sentiment is not None
        assert result.categories is not None

    def test_annotate_text_with_language(
        self, service, sample_annotate_response
    ):
        mock_documents = service.service.documents()
        mock_documents.annotateText().execute.return_value = (
            sample_annotate_response
        )

        features = {"extractEntities": True}
        result = service.annotate_text(
            "Google is great.", features=features, language="en"
        )
        assert isinstance(result, NLResult)

    def test_annotate_text_api_error(self, service):
        mock_documents = service.service.documents()
        mock_documents.annotateText().execute.side_effect = (
            _make_http_error(500)
        )

        with pytest.raises(APIError):
            service.annotate_text(
                "test", features={"extractEntities": True}
            )


# ---- Service Initialization Tests ----


class TestNaturalLanguageServiceInit:
    def test_service_init(self, service):
        assert service.project_id == "test-project"
        assert service.service_name == "language"
        assert service.version == "v1"
        assert service.resource_model == NLResult
