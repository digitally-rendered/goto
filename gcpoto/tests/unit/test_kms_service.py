"""Tests for Cloud KMS service."""

import base64
from unittest import mock

import pytest
from googleapiclient.errors import HttpError

from gcpoto.services.kms import KMSService
from gcpoto.models.kms import KeyRing, CryptoKey, CryptoKeyVersion
from gcpoto.utils import format_key_ring_path, format_crypto_key_path


@pytest.fixture
def mock_google_client():
    """Mock Google API client."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service

        # Set up projects().locations().keyRings() chain
        mock_key_rings = mock.MagicMock()
        mock_service.projects.return_value.locations.return_value.keyRings.return_value = (
            mock_key_rings
        )

        # Set up projects().locations().keyRings().cryptoKeys() chain
        mock_crypto_keys = mock.MagicMock()
        mock_key_rings.cryptoKeys.return_value = mock_crypto_keys

        # Set up cryptoKeyVersions chain
        mock_versions = mock.MagicMock()
        mock_crypto_keys.cryptoKeyVersions.return_value = mock_versions

        yield mock_service


@pytest.fixture
def sample_key_ring_response():
    """Sample KMS key ring API response."""
    return {
        "name": "projects/test-project/locations/global/keyRings/test-ring",
        "createTime": "2025-01-15T10:00:00Z",
    }


@pytest.fixture
def sample_crypto_key_response():
    """Sample KMS crypto key API response."""
    return {
        "name": "projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key",
        "purpose": "ENCRYPT_DECRYPT",
        "primary": {
            "name": "projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key/cryptoKeyVersions/1",
            "state": "ENABLED",
            "algorithm": "GOOGLE_SYMMETRIC_ENCRYPTION",
            "protectionLevel": "SOFTWARE",
            "generateTime": "2025-01-15T10:00:00Z",
            "createTime": "2025-01-15T10:00:00Z",
        },
        "rotationPeriod": "7776000s",
        "nextRotationTime": "2025-04-15T10:00:00Z",
        "labels": {"env": "test", "team": "platform"},
        "createTime": "2025-01-15T10:00:00Z",
        "updateTime": "2025-01-15T10:00:00Z",
    }


@pytest.fixture
def sample_crypto_key_version_response():
    """Sample KMS crypto key version API response."""
    return {
        "name": "projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key/cryptoKeyVersions/1",
        "state": "ENABLED",
        "algorithm": "GOOGLE_SYMMETRIC_ENCRYPTION",
        "protectionLevel": "SOFTWARE",
        "generateTime": "2025-01-15T10:00:00Z",
        "createTime": "2025-01-15T10:00:00Z",
    }


class TestKMSServiceInit:
    """Tests for KMSService initialization."""

    def test_init(self, mock_google_client):
        """Test initializing the KMSService."""
        from googleapiclient.discovery import build

        service = KMSService(project_id="test-project")

        assert service.project_id == "test-project"
        assert service.service_name == "cloudkms"
        assert service.version == "v1"
        build.assert_called_once_with("cloudkms", "v1", credentials=None)


class TestKeyRingModel:
    """Tests for KeyRing model."""

    def test_from_api_response(self, sample_key_ring_response):
        """Test creating a KeyRing from an API response."""
        key_ring = KeyRing.from_api_response(sample_key_ring_response)

        assert key_ring.name == "test-ring"
        assert key_ring.project == "test-project"
        assert key_ring.location == "global"
        assert key_ring.type == "kms.keyRing"
        assert key_ring.id == "projects/test-project/locations/global/keyRings/test-ring"

    def test_from_api_response_with_project_id(self, sample_key_ring_response):
        """Test creating a KeyRing with an explicit project ID."""
        key_ring = KeyRing.from_api_response(
            sample_key_ring_response, project_id="override-project"
        )
        assert key_ring.project == "override-project"


class TestCryptoKeyModel:
    """Tests for CryptoKey model."""

    def test_from_api_response(self, sample_crypto_key_response):
        """Test creating a CryptoKey from an API response."""
        key = CryptoKey.from_api_response(sample_crypto_key_response)

        assert key.name == "test-key"
        assert key.project == "test-project"
        assert key.key_ring == "test-ring"
        assert key.purpose == "ENCRYPT_DECRYPT"
        assert key.algorithm == "GOOGLE_SYMMETRIC_ENCRYPTION"
        assert key.protection_level == "SOFTWARE"
        assert key.rotation_period == "7776000s"
        assert key.primary_version is not None
        assert key.primary_version["state"] == "ENABLED"
        assert key.labels == {"env": "test", "team": "platform"}

    def test_get_tag(self, sample_crypto_key_response):
        """Test get_tag method on CryptoKey."""
        key = CryptoKey.from_api_response(sample_crypto_key_response)

        assert key.get_tag("env") == "test"
        assert key.get_tag("team") == "platform"
        assert key.get_tag("nonexistent") == ""
        assert key.get_tag("nonexistent", "default") == "default"

    def test_from_api_response_no_primary(self):
        """Test creating a CryptoKey with no primary version."""
        response = {
            "name": "projects/p/locations/l/keyRings/kr/cryptoKeys/ck",
            "purpose": "ASYMMETRIC_SIGN",
        }
        key = CryptoKey.from_api_response(response)

        assert key.purpose == "ASYMMETRIC_SIGN"
        assert key.algorithm is None
        assert key.protection_level is None
        assert key.primary_version is None


class TestCryptoKeyVersionModel:
    """Tests for CryptoKeyVersion model."""

    def test_from_api_response(self, sample_crypto_key_version_response):
        """Test creating a CryptoKeyVersion from an API response."""
        version = CryptoKeyVersion.from_api_response(
            sample_crypto_key_version_response
        )

        assert version.name == "1"
        assert version.project == "test-project"
        assert version.crypto_key == "test-key"
        assert version.state == "ENABLED"
        assert version.algorithm == "GOOGLE_SYMMETRIC_ENCRYPTION"
        assert version.protection_level == "SOFTWARE"

    def test_from_api_response_destroyed(self):
        """Test creating a destroyed CryptoKeyVersion."""
        response = {
            "name": "projects/p/locations/l/keyRings/kr/cryptoKeys/ck/cryptoKeyVersions/2",
            "state": "DESTROYED",
            "algorithm": "GOOGLE_SYMMETRIC_ENCRYPTION",
            "protectionLevel": "SOFTWARE",
            "destroyTime": "2025-02-15T10:00:00Z",
            "destroyEventTime": "2025-02-15T10:00:00Z",
        }
        version = CryptoKeyVersion.from_api_response(response)

        assert version.state == "DESTROYED"
        assert version.name == "2"


class TestListKeyRings:
    """Tests for listing key rings."""

    def test_list_key_rings(self, mock_google_client, sample_key_ring_response):
        """Test listing key rings in a location."""
        mock_key_rings = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
        )
        mock_request = mock.MagicMock()
        mock_key_rings.list.return_value = mock_request
        mock_request.execute.return_value = {
            "keyRings": [sample_key_ring_response, sample_key_ring_response]
        }
        mock_key_rings.list_next.return_value = None

        service = KMSService(project_id="test-project")
        key_rings = service.list_key_rings("global")

        mock_key_rings.list.assert_called_once_with(
            parent="projects/test-project/locations/global"
        )
        assert len(key_rings) == 2
        assert isinstance(key_rings[0], KeyRing)
        assert key_rings[0].name == "test-ring"

    def test_list_key_rings_empty(self, mock_google_client):
        """Test listing key rings with no results."""
        mock_key_rings = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
        )
        mock_request = mock.MagicMock()
        mock_key_rings.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_key_rings.list_next.return_value = None

        service = KMSService(project_id="test-project")
        key_rings = service.list_key_rings("us-east1")

        assert key_rings == []

    def test_list_key_rings_pagination(
        self, mock_google_client, sample_key_ring_response
    ):
        """Test listing key rings with pagination."""
        mock_key_rings = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
        )

        # First page
        mock_request_1 = mock.MagicMock()
        mock_key_rings.list.return_value = mock_request_1
        mock_request_1.execute.return_value = {
            "keyRings": [sample_key_ring_response]
        }

        # Second page
        mock_request_2 = mock.MagicMock()
        mock_request_2.execute.return_value = {
            "keyRings": [sample_key_ring_response]
        }
        mock_key_rings.list_next.side_effect = [mock_request_2, None]

        service = KMSService(project_id="test-project")
        key_rings = service.list_key_rings("global")

        assert len(key_rings) == 2


class TestGetKeyRing:
    """Tests for getting a key ring."""

    def test_get_key_ring(self, mock_google_client, sample_key_ring_response):
        """Test getting a specific key ring."""
        mock_key_rings = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
        )
        mock_request = mock.MagicMock()
        mock_key_rings.get.return_value = mock_request
        mock_request.execute.return_value = sample_key_ring_response

        service = KMSService(project_id="test-project")
        key_ring = service.get_key_ring("global", "test-ring")

        mock_key_rings.get.assert_called_once_with(
            name="projects/test-project/locations/global/keyRings/test-ring"
        )
        assert isinstance(key_ring, KeyRing)
        assert key_ring.name == "test-ring"
        assert key_ring.location == "global"


class TestCreateKeyRing:
    """Tests for creating a key ring."""

    def test_create_key_ring(self, mock_google_client, sample_key_ring_response):
        """Test creating a new key ring."""
        mock_key_rings = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
        )
        mock_request = mock.MagicMock()
        mock_key_rings.create.return_value = mock_request
        mock_request.execute.return_value = sample_key_ring_response

        service = KMSService(project_id="test-project")
        key_ring = service.create_key_ring("global", "test-ring")

        mock_key_rings.create.assert_called_once_with(
            parent="projects/test-project/locations/global",
            keyRingId="test-ring",
            body={},
        )
        assert isinstance(key_ring, KeyRing)
        assert key_ring.name == "test-ring"


class TestListCryptoKeys:
    """Tests for listing crypto keys."""

    def test_list_crypto_keys(
        self, mock_google_client, sample_crypto_key_response
    ):
        """Test listing crypto keys in a key ring."""
        mock_crypto_keys = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
        )
        mock_request = mock.MagicMock()
        mock_crypto_keys.list.return_value = mock_request
        mock_request.execute.return_value = {
            "cryptoKeys": [sample_crypto_key_response]
        }
        mock_crypto_keys.list_next.return_value = None

        service = KMSService(project_id="test-project")
        keys = service.list_crypto_keys("global", "test-ring")

        mock_crypto_keys.list.assert_called_once_with(
            parent="projects/test-project/locations/global/keyRings/test-ring"
        )
        assert len(keys) == 1
        assert isinstance(keys[0], CryptoKey)
        assert keys[0].name == "test-key"
        assert keys[0].purpose == "ENCRYPT_DECRYPT"

    def test_list_crypto_keys_empty(self, mock_google_client):
        """Test listing crypto keys with no results."""
        mock_crypto_keys = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
        )
        mock_request = mock.MagicMock()
        mock_crypto_keys.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_crypto_keys.list_next.return_value = None

        service = KMSService(project_id="test-project")
        keys = service.list_crypto_keys("global", "test-ring")

        assert keys == []


class TestGetCryptoKey:
    """Tests for getting a crypto key."""

    def test_get_crypto_key(
        self, mock_google_client, sample_crypto_key_response
    ):
        """Test getting a specific crypto key."""
        mock_crypto_keys = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
        )
        mock_request = mock.MagicMock()
        mock_crypto_keys.get.return_value = mock_request
        mock_request.execute.return_value = sample_crypto_key_response

        service = KMSService(project_id="test-project")
        key = service.get_crypto_key("global", "test-ring", "test-key")

        mock_crypto_keys.get.assert_called_once_with(
            name="projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key"
        )
        assert isinstance(key, CryptoKey)
        assert key.name == "test-key"
        assert key.purpose == "ENCRYPT_DECRYPT"
        assert key.algorithm == "GOOGLE_SYMMETRIC_ENCRYPTION"


class TestCreateCryptoKey:
    """Tests for creating a crypto key."""

    def test_create_crypto_key_basic(
        self, mock_google_client, sample_crypto_key_response
    ):
        """Test creating a crypto key with default settings."""
        mock_crypto_keys = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
        )
        mock_request = mock.MagicMock()
        mock_crypto_keys.create.return_value = mock_request
        mock_request.execute.return_value = sample_crypto_key_response

        service = KMSService(project_id="test-project")
        key = service.create_crypto_key("global", "test-ring", "test-key")

        mock_crypto_keys.create.assert_called_once_with(
            parent="projects/test-project/locations/global/keyRings/test-ring",
            cryptoKeyId="test-key",
            body={"purpose": "ENCRYPT_DECRYPT"},
        )
        assert isinstance(key, CryptoKey)
        assert key.name == "test-key"

    def test_create_crypto_key_full(
        self, mock_google_client, sample_crypto_key_response
    ):
        """Test creating a crypto key with all options."""
        mock_crypto_keys = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
        )
        mock_request = mock.MagicMock()
        mock_crypto_keys.create.return_value = mock_request
        mock_request.execute.return_value = sample_crypto_key_response

        service = KMSService(project_id="test-project")
        key = service.create_crypto_key(
            location="global",
            key_ring_id="test-ring",
            key_id="test-key",
            purpose="ASYMMETRIC_SIGN",
            algorithm="RSA_SIGN_PSS_2048_SHA256",
            rotation_period="7776000s",
            labels={"env": "test"},
        )

        mock_crypto_keys.create.assert_called_once_with(
            parent="projects/test-project/locations/global/keyRings/test-ring",
            cryptoKeyId="test-key",
            body={
                "purpose": "ASYMMETRIC_SIGN",
                "versionTemplate": {"algorithm": "RSA_SIGN_PSS_2048_SHA256"},
                "rotationPeriod": "7776000s",
                "labels": {"env": "test"},
            },
        )
        assert isinstance(key, CryptoKey)


class TestUpdateCryptoKey:
    """Tests for updating a crypto key."""

    def test_update_crypto_key_labels(
        self, mock_google_client, sample_crypto_key_response
    ):
        """Test updating a crypto key's labels."""
        mock_crypto_keys = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
        )
        mock_request = mock.MagicMock()
        mock_crypto_keys.patch.return_value = mock_request
        mock_request.execute.return_value = sample_crypto_key_response

        service = KMSService(project_id="test-project")
        key = service.update_crypto_key(
            "global", "test-ring", "test-key", labels={"env": "prod"}
        )

        mock_crypto_keys.patch.assert_called_once_with(
            name="projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key",
            updateMask="labels",
            body={"labels": {"env": "prod"}},
        )
        assert isinstance(key, CryptoKey)

    def test_update_crypto_key_rotation(
        self, mock_google_client, sample_crypto_key_response
    ):
        """Test updating a crypto key's rotation settings."""
        mock_crypto_keys = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
        )
        mock_request = mock.MagicMock()
        mock_crypto_keys.patch.return_value = mock_request
        mock_request.execute.return_value = sample_crypto_key_response

        service = KMSService(project_id="test-project")
        key = service.update_crypto_key(
            "global",
            "test-ring",
            "test-key",
            rotation_period="15552000s",
            next_rotation_time="2025-07-15T10:00:00Z",
        )

        mock_crypto_keys.patch.assert_called_once_with(
            name="projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key",
            updateMask="rotationPeriod,nextRotationTime",
            body={
                "rotationPeriod": "15552000s",
                "nextRotationTime": "2025-07-15T10:00:00Z",
            },
        )

    def test_update_crypto_key_multiple_fields(
        self, mock_google_client, sample_crypto_key_response
    ):
        """Test updating multiple fields at once."""
        mock_crypto_keys = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
        )
        mock_request = mock.MagicMock()
        mock_crypto_keys.patch.return_value = mock_request
        mock_request.execute.return_value = sample_crypto_key_response

        service = KMSService(project_id="test-project")
        service.update_crypto_key(
            "global",
            "test-ring",
            "test-key",
            labels={"env": "staging"},
            rotation_period="7776000s",
        )

        mock_crypto_keys.patch.assert_called_once_with(
            name="projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key",
            updateMask="labels,rotationPeriod",
            body={
                "labels": {"env": "staging"},
                "rotationPeriod": "7776000s",
            },
        )


class TestEncryptDecrypt:
    """Tests for encrypt and decrypt operations."""

    def test_encrypt(self, mock_google_client):
        """Test encrypting data."""
        mock_crypto_keys = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
        )
        mock_request = mock.MagicMock()
        mock_crypto_keys.encrypt.return_value = mock_request

        # The API returns base64-encoded ciphertext
        ciphertext_b64 = base64.b64encode(b"encrypted-data").decode("utf-8")
        mock_request.execute.return_value = {"ciphertext": ciphertext_b64}

        service = KMSService(project_id="test-project")
        result = service.encrypt("global", "test-ring", "test-key", b"hello world")

        # Verify the API was called with base64-encoded plaintext
        plaintext_b64 = base64.b64encode(b"hello world").decode("utf-8")
        mock_crypto_keys.encrypt.assert_called_once_with(
            name="projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key",
            body={"plaintext": plaintext_b64},
        )

        # Verify the result is raw bytes (decoded from base64)
        assert result == b"encrypted-data"

    def test_decrypt(self, mock_google_client):
        """Test decrypting data."""
        mock_crypto_keys = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
        )
        mock_request = mock.MagicMock()
        mock_crypto_keys.decrypt.return_value = mock_request

        # The API returns base64-encoded plaintext
        plaintext_b64 = base64.b64encode(b"hello world").decode("utf-8")
        mock_request.execute.return_value = {"plaintext": plaintext_b64}

        service = KMSService(project_id="test-project")
        result = service.decrypt(
            "global", "test-ring", "test-key", b"encrypted-data"
        )

        # Verify the API was called with base64-encoded ciphertext
        ciphertext_b64 = base64.b64encode(b"encrypted-data").decode("utf-8")
        mock_crypto_keys.decrypt.assert_called_once_with(
            name="projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key",
            body={"ciphertext": ciphertext_b64},
        )

        # Verify the result is raw bytes (decoded from base64)
        assert result == b"hello world"

    def test_encrypt_decrypt_roundtrip(self, mock_google_client):
        """Test that encrypt and decrypt work as a roundtrip."""
        mock_crypto_keys = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
        )

        original_data = b"secret message for roundtrip test"

        # Mock encrypt
        mock_encrypt_request = mock.MagicMock()
        mock_crypto_keys.encrypt.return_value = mock_encrypt_request
        fake_ciphertext = b"fake-ciphertext-bytes"
        mock_encrypt_request.execute.return_value = {
            "ciphertext": base64.b64encode(fake_ciphertext).decode("utf-8")
        }

        # Mock decrypt
        mock_decrypt_request = mock.MagicMock()
        mock_crypto_keys.decrypt.return_value = mock_decrypt_request
        mock_decrypt_request.execute.return_value = {
            "plaintext": base64.b64encode(original_data).decode("utf-8")
        }

        service = KMSService(project_id="test-project")

        encrypted = service.encrypt(
            "global", "test-ring", "test-key", original_data
        )
        assert encrypted == fake_ciphertext

        decrypted = service.decrypt(
            "global", "test-ring", "test-key", encrypted
        )
        assert decrypted == original_data


class TestListCryptoKeyVersions:
    """Tests for listing crypto key versions."""

    def test_list_crypto_key_versions(
        self, mock_google_client, sample_crypto_key_version_response
    ):
        """Test listing crypto key versions."""
        mock_versions = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
            .cryptoKeyVersions.return_value
        )
        mock_request = mock.MagicMock()
        mock_versions.list.return_value = mock_request
        mock_request.execute.return_value = {
            "cryptoKeyVersions": [
                sample_crypto_key_version_response,
                sample_crypto_key_version_response,
            ]
        }
        mock_versions.list_next.return_value = None

        service = KMSService(project_id="test-project")
        versions = service.list_crypto_key_versions(
            "global", "test-ring", "test-key"
        )

        mock_versions.list.assert_called_once_with(
            parent="projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key"
        )
        assert len(versions) == 2
        assert isinstance(versions[0], CryptoKeyVersion)
        assert versions[0].state == "ENABLED"
        assert versions[0].algorithm == "GOOGLE_SYMMETRIC_ENCRYPTION"

    def test_list_crypto_key_versions_empty(self, mock_google_client):
        """Test listing crypto key versions with no results."""
        mock_versions = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
            .cryptoKeyVersions.return_value
        )
        mock_request = mock.MagicMock()
        mock_versions.list.return_value = mock_request
        mock_request.execute.return_value = {}
        mock_versions.list_next.return_value = None

        service = KMSService(project_id="test-project")
        versions = service.list_crypto_key_versions(
            "global", "test-ring", "test-key"
        )

        assert versions == []


class TestDestroyCryptoKeyVersion:
    """Tests for destroying a crypto key version."""

    def test_destroy_crypto_key_version(
        self, mock_google_client, sample_crypto_key_version_response
    ):
        """Test scheduling a crypto key version for destruction."""
        mock_versions = (
            mock_google_client.projects.return_value
            .locations.return_value
            .keyRings.return_value
            .cryptoKeys.return_value
            .cryptoKeyVersions.return_value
        )
        mock_request = mock.MagicMock()
        mock_versions.destroy.return_value = mock_request

        destroyed_response = sample_crypto_key_version_response.copy()
        destroyed_response["state"] = "DESTROY_SCHEDULED"
        destroyed_response["destroyTime"] = "2025-02-15T10:00:00Z"
        mock_request.execute.return_value = destroyed_response

        service = KMSService(project_id="test-project")
        version = service.destroy_crypto_key_version(
            "global", "test-ring", "test-key", "1"
        )

        mock_versions.destroy.assert_called_once_with(
            name="projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key/cryptoKeyVersions/1",
            body={},
        )
        assert isinstance(version, CryptoKeyVersion)
        assert version.state == "DESTROY_SCHEDULED"


class TestPathHelpers:
    """Tests for KMS path helper utilities."""

    def test_format_key_ring_path(self):
        """Test formatting a key ring path."""
        path = format_key_ring_path("my-project", "us-east1", "my-ring")
        assert path == "projects/my-project/locations/us-east1/keyRings/my-ring"

    def test_format_key_ring_path_global(self):
        """Test formatting a key ring path with global location."""
        path = format_key_ring_path("my-project", "global", "my-ring")
        assert path == "projects/my-project/locations/global/keyRings/my-ring"

    def test_format_crypto_key_path(self):
        """Test formatting a crypto key path."""
        path = format_crypto_key_path(
            "my-project", "us-east1", "my-ring", "my-key"
        )
        assert (
            path
            == "projects/my-project/locations/us-east1/keyRings/my-ring/cryptoKeys/my-key"
        )
