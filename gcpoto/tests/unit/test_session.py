"""Tests for the Session class."""

from unittest import mock

import pytest

from gcpoto.session import Session, _SERVICE_REGISTRY


class TestSessionInit:
    """Tests for Session initialization."""

    def test_init_defaults(self):
        """Test creating a session with default parameters."""
        session = Session()

        assert session.project_id is None
        assert session.credentials_file is None
        assert session.region is None
        assert session.zone is None

    def test_init_with_params(self):
        """Test creating a session with all parameters."""
        session = Session(
            project_id="my-project",
            credentials_file="/path/to/creds.json",
            region="us-central1",
            zone="us-central1-a",
        )

        assert session.project_id == "my-project"
        assert session.credentials_file == "/path/to/creds.json"
        assert session.region == "us-central1"
        assert session.zone == "us-central1-a"


class TestSessionClient:
    """Tests for Session.client()."""

    def test_client_unknown_service(self):
        """Test that requesting an unknown service raises ValueError."""
        session = Session(project_id="test-project")

        with pytest.raises(ValueError, match="Unknown service"):
            session.client("nonexistent_service")

    def test_client_no_project_id(self):
        """Test that calling client without project_id raises ValueError."""
        session = Session()

        with pytest.raises(ValueError, match="project_id is required"):
            session.client("dns")

    @mock.patch("gcpoto.session.importlib.import_module")
    def test_client_creates_instance(self, mock_import):
        """Test that client() creates and returns a service instance."""
        mock_module = mock.MagicMock()
        mock_service_class = mock.MagicMock()
        mock_instance = mock.MagicMock()
        mock_service_class.return_value = mock_instance
        mock_module.DNSService = mock_service_class
        mock_import.return_value = mock_module
        setattr(mock_module, "DNSService", mock_service_class)

        session = Session(
            project_id="test-project",
            credentials_file="/path/to/creds.json",
        )
        result = session.client("dns")

        mock_import.assert_called_once_with("gcpoto.services.dns")
        mock_service_class.assert_called_once_with(
            project_id="test-project",
            credentials_file="/path/to/creds.json",
        )
        assert result is mock_instance

    @mock.patch("gcpoto.session.importlib.import_module")
    def test_client_caches_instances(self, mock_import):
        """Test that repeated client() calls return the same instance."""
        mock_module = mock.MagicMock()
        mock_service_class = mock.MagicMock()
        mock_instance = mock.MagicMock()
        mock_service_class.return_value = mock_instance
        setattr(mock_module, "DNSService", mock_service_class)
        mock_import.return_value = mock_module

        session = Session(project_id="test-project")
        first = session.client("dns")
        second = session.client("dns")

        assert first is second
        # import_module should only be called once
        mock_import.assert_called_once()
        mock_service_class.assert_called_once()

    @mock.patch("gcpoto.session.importlib.import_module")
    def test_client_different_services(self, mock_import):
        """Test creating clients for different services."""
        mock_module_dns = mock.MagicMock()
        mock_dns_class = mock.MagicMock()
        mock_dns_instance = mock.MagicMock()
        mock_dns_class.return_value = mock_dns_instance
        setattr(mock_module_dns, "DNSService", mock_dns_class)

        mock_module_kms = mock.MagicMock()
        mock_kms_class = mock.MagicMock()
        mock_kms_instance = mock.MagicMock()
        mock_kms_class.return_value = mock_kms_instance
        setattr(mock_module_kms, "KMSService", mock_kms_class)

        def side_effect(module_path):
            if module_path == "gcpoto.services.dns":
                return mock_module_dns
            elif module_path == "gcpoto.services.kms":
                return mock_module_kms
            raise ImportError(f"No module {module_path}")

        mock_import.side_effect = side_effect

        session = Session(project_id="test-project")
        dns_client = session.client("dns")
        kms_client = session.client("kms")

        assert dns_client is mock_dns_instance
        assert kms_client is mock_kms_instance
        assert dns_client is not kms_client


class TestGetAvailableServices:
    """Tests for Session.get_available_services()."""

    def test_returns_sorted_list(self):
        """Test that available services are returned sorted."""
        session = Session()
        services = session.get_available_services()

        assert isinstance(services, list)
        assert services == sorted(services)

    def test_contains_known_services(self):
        """Test that known services are in the list."""
        session = Session()
        services = session.get_available_services()

        assert "dns" in services
        assert "storage" in services
        assert "bigquery" in services
        assert "api_gateway" in services
        assert "compute" in services
        assert "alloydb" in services
        assert "cloud_build" in services
        assert "vertex_ai" in services
        assert "vpn" in services

    def test_matches_registry(self):
        """Test that the list matches the registry keys."""
        session = Session()
        services = session.get_available_services()

        assert set(services) == set(_SERVICE_REGISTRY.keys())


class TestGetCredentials:
    """Tests for Session.get_credentials()."""

    def test_returns_none_when_not_set(self):
        """Test that None is returned when no credentials file is set."""
        session = Session()

        assert session.get_credentials() is None

    def test_returns_credentials_file(self):
        """Test that the credentials file path is returned."""
        session = Session(credentials_file="/path/to/creds.json")

        assert session.get_credentials() == "/path/to/creds.json"


class TestServiceRegistry:
    """Tests for the service registry."""

    def test_registry_populated(self):
        """Test that the service registry is populated on import."""
        assert len(_SERVICE_REGISTRY) > 0

    def test_registry_entries_are_tuples(self):
        """Test that registry entries are (module_path, class_name) tuples."""
        for name, entry in _SERVICE_REGISTRY.items():
            assert isinstance(entry, tuple), f"{name} is not a tuple"
            assert len(entry) == 2, f"{name} does not have 2 elements"
            module_path, class_name = entry
            assert isinstance(module_path, str)
            assert isinstance(class_name, str)
            assert module_path.startswith("gcpoto.services.")

    def test_api_gateway_in_registry(self):
        """Test that api_gateway is registered."""
        assert "api_gateway" in _SERVICE_REGISTRY
        module_path, class_name = _SERVICE_REGISTRY["api_gateway"]
        assert module_path == "gcpoto.services.api_gateway"
        assert class_name == "APIGatewayService"
