"""Service implementation for Google Cloud KMS."""

import base64
import logging
from typing import List, Optional, Dict, Any


from gcpoto.services.base import GCPService
from gcpoto.models.kms import KeyRing, CryptoKey, CryptoKeyVersion

from gcpoto.utils import format_key_ring_path, format_crypto_key_path

logger = logging.getLogger(__name__)

class KMSService(GCPService[KeyRing]):
    """Service for interacting with Google Cloud KMS."""

    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the KMS service.

        Args:
            project_id: The GCP project ID to use for API calls
            credentials_file: Optional path to a service account credentials file
            **kwargs: Additional arguments to pass to the service constructor
        """
        super().__init__(
            project_id=project_id,
            service_name="cloudkms",
            version="v1",
            credentials_file=credentials_file,
            resource_model=KeyRing,
            **kwargs,
        )

    def list_key_rings(self, location: str) -> List[KeyRing]:
        """List key rings in a location.

        Args:
            location: The GCP location (e.g. 'global', 'us-east1')

        Returns:
            A list of KeyRing instances
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug("Listing key rings in %s", parent)

        key_rings = []
        request = (
            self.service.projects()
            .locations()
            .keyRings()
            .list(parent=parent)
        )

        while request is not None:
            response = self._execute(request)
            for kr_data in response.get("keyRings", []):
                key_rings.append(
                    KeyRing.from_api_response(kr_data, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .keyRings()
                .list_next(request, response)
            )

        return key_rings

    def get_key_ring(self, location: str, key_ring_id: str) -> KeyRing:
        """Get a specific key ring.

        Args:
            location: The GCP location (e.g. 'global', 'us-east1')
            key_ring_id: The key ring ID

        Returns:
            A KeyRing instance
        """
        name = format_key_ring_path(self.project_id, location, key_ring_id)
        logger.debug("Getting key ring %s", name)

        request = (
            self.service.projects()
            .locations()
            .keyRings()
            .get(name=name)
        )
        response = self._execute(request)

        return KeyRing.from_api_response(response, self.project_id)

    def create_key_ring(self, location: str, key_ring_id: str) -> KeyRing:
        """Create a new key ring.

        Args:
            location: The GCP location (e.g. 'global', 'us-east1')
            key_ring_id: The key ring ID to create

        Returns:
            A KeyRing instance for the newly created key ring
        """
        parent = f"projects/{self.project_id}/locations/{location}"
        logger.debug("Creating key ring %s in %s", key_ring_id, parent)

        request = (
            self.service.projects()
            .locations()
            .keyRings()
            .create(parent=parent, keyRingId=key_ring_id, body={})
        )
        response = self._execute(request)

        return KeyRing.from_api_response(response, self.project_id)

    def list_crypto_keys(
        self, location: str, key_ring_id: str
    ) -> List[CryptoKey]:
        """List crypto keys in a key ring.

        Args:
            location: The GCP location
            key_ring_id: The key ring ID

        Returns:
            A list of CryptoKey instances
        """
        parent = format_key_ring_path(self.project_id, location, key_ring_id)
        logger.debug("Listing crypto keys in %s", parent)

        crypto_keys = []
        request = (
            self.service.projects()
            .locations()
            .keyRings()
            .cryptoKeys()
            .list(parent=parent)
        )

        while request is not None:
            response = self._execute(request)
            for ck_data in response.get("cryptoKeys", []):
                crypto_keys.append(
                    CryptoKey.from_api_response(ck_data, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .keyRings()
                .cryptoKeys()
                .list_next(request, response)
            )

        return crypto_keys

    def get_crypto_key(
        self, location: str, key_ring_id: str, key_id: str
    ) -> CryptoKey:
        """Get a specific crypto key.

        Args:
            location: The GCP location
            key_ring_id: The key ring ID
            key_id: The crypto key ID

        Returns:
            A CryptoKey instance
        """
        name = format_crypto_key_path(
            self.project_id, location, key_ring_id, key_id
        )
        logger.debug("Getting crypto key %s", name)

        request = (
            self.service.projects()
            .locations()
            .keyRings()
            .cryptoKeys()
            .get(name=name)
        )
        response = self._execute(request)

        return CryptoKey.from_api_response(response, self.project_id)

    def create_crypto_key(
        self,
        location: str,
        key_ring_id: str,
        key_id: str,
        purpose: str = "ENCRYPT_DECRYPT",
        algorithm: Optional[str] = None,
        rotation_period: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> CryptoKey:
        """Create a new crypto key.

        Args:
            location: The GCP location
            key_ring_id: The key ring ID
            key_id: The crypto key ID to create
            purpose: The key purpose (ENCRYPT_DECRYPT, ASYMMETRIC_SIGN,
                ASYMMETRIC_DECRYPT, MAC)
            algorithm: Optional algorithm for the key version template
            rotation_period: Optional rotation period (e.g. '7776000s')
            labels: Optional labels to apply

        Returns:
            A CryptoKey instance for the newly created crypto key
        """
        parent = format_key_ring_path(self.project_id, location, key_ring_id)
        logger.debug("Creating crypto key %s in %s", key_id, parent)

        body: Dict[str, Any] = {"purpose": purpose}

        if algorithm:
            body["versionTemplate"] = {"algorithm": algorithm}

        if rotation_period:
            body["rotationPeriod"] = rotation_period

        if labels:
            body["labels"] = labels

        request = (
            self.service.projects()
            .locations()
            .keyRings()
            .cryptoKeys()
            .create(parent=parent, cryptoKeyId=key_id, body=body)
        )
        response = self._execute(request)

        return CryptoKey.from_api_response(response, self.project_id)

    def update_crypto_key(
        self,
        location: str,
        key_ring_id: str,
        key_id: str,
        labels: Optional[Dict[str, str]] = None,
        rotation_period: Optional[str] = None,
        next_rotation_time: Optional[str] = None,
    ) -> CryptoKey:
        """Update an existing crypto key.

        Args:
            location: The GCP location
            key_ring_id: The key ring ID
            key_id: The crypto key ID to update
            labels: Optional labels to set
            rotation_period: Optional new rotation period
            next_rotation_time: Optional next rotation time

        Returns:
            The updated CryptoKey instance
        """
        name = format_crypto_key_path(
            self.project_id, location, key_ring_id, key_id
        )
        logger.debug("Updating crypto key %s", name)

        body: Dict[str, Any] = {}
        update_mask_fields = []

        if labels is not None:
            body["labels"] = labels
            update_mask_fields.append("labels")

        if rotation_period is not None:
            body["rotationPeriod"] = rotation_period
            update_mask_fields.append("rotationPeriod")

        if next_rotation_time is not None:
            body["nextRotationTime"] = next_rotation_time
            update_mask_fields.append("nextRotationTime")

        update_mask = ",".join(update_mask_fields)

        request = (
            self.service.projects()
            .locations()
            .keyRings()
            .cryptoKeys()
            .patch(name=name, updateMask=update_mask, body=body)
        )
        response = self._execute(request)

        return CryptoKey.from_api_response(response, self.project_id)

    def encrypt(
        self,
        location: str,
        key_ring_id: str,
        key_id: str,
        plaintext: bytes,
    ) -> bytes:
        """Encrypt data using a crypto key.

        Args:
            location: The GCP location
            key_ring_id: The key ring ID
            key_id: The crypto key ID
            plaintext: The data to encrypt

        Returns:
            The encrypted ciphertext as bytes
        """
        name = format_crypto_key_path(
            self.project_id, location, key_ring_id, key_id
        )
        logger.debug("Encrypting data with key %s", name)

        body = {"plaintext": base64.b64encode(plaintext).decode("utf-8")}

        request = (
            self.service.projects()
            .locations()
            .keyRings()
            .cryptoKeys()
            .encrypt(name=name, body=body)
        )
        response = self._execute(request)

        return base64.b64decode(response["ciphertext"])

    def decrypt(
        self,
        location: str,
        key_ring_id: str,
        key_id: str,
        ciphertext: bytes,
    ) -> bytes:
        """Decrypt data using a crypto key.

        Args:
            location: The GCP location
            key_ring_id: The key ring ID
            key_id: The crypto key ID
            ciphertext: The encrypted data to decrypt

        Returns:
            The decrypted plaintext as bytes
        """
        name = format_crypto_key_path(
            self.project_id, location, key_ring_id, key_id
        )
        logger.debug("Decrypting data with key %s", name)

        body = {"ciphertext": base64.b64encode(ciphertext).decode("utf-8")}

        request = (
            self.service.projects()
            .locations()
            .keyRings()
            .cryptoKeys()
            .decrypt(name=name, body=body)
        )
        response = self._execute(request)

        return base64.b64decode(response["plaintext"])

    def list_crypto_key_versions(
        self, location: str, key_ring_id: str, key_id: str
    ) -> List[CryptoKeyVersion]:
        """List versions of a crypto key.

        Args:
            location: The GCP location
            key_ring_id: The key ring ID
            key_id: The crypto key ID

        Returns:
            A list of CryptoKeyVersion instances
        """
        parent = format_crypto_key_path(
            self.project_id, location, key_ring_id, key_id
        )
        logger.debug("Listing crypto key versions for %s", parent)

        versions = []
        request = (
            self.service.projects()
            .locations()
            .keyRings()
            .cryptoKeys()
            .cryptoKeyVersions()
            .list(parent=parent)
        )

        while request is not None:
            response = self._execute(request)
            for v_data in response.get("cryptoKeyVersions", []):
                versions.append(
                    CryptoKeyVersion.from_api_response(v_data, self.project_id)
                )
            request = (
                self.service.projects()
                .locations()
                .keyRings()
                .cryptoKeys()
                .cryptoKeyVersions()
                .list_next(request, response)
            )

        return versions

    def destroy_crypto_key_version(
        self,
        location: str,
        key_ring_id: str,
        key_id: str,
        version_id: str,
    ) -> CryptoKeyVersion:
        """Schedule a crypto key version for destruction.

        Args:
            location: The GCP location
            key_ring_id: The key ring ID
            key_id: The crypto key ID
            version_id: The version ID to destroy

        Returns:
            The updated CryptoKeyVersion instance
        """
        name = (
            f"{format_crypto_key_path(self.project_id, location, key_ring_id, key_id)}"
            f"/cryptoKeyVersions/{version_id}"
        )
        logger.debug("Destroying crypto key version %s", name)

        request = (
            self.service.projects()
            .locations()
            .keyRings()
            .cryptoKeys()
            .cryptoKeyVersions()
            .destroy(name=name, body={})
        )
        response = self._execute(request)

        return CryptoKeyVersion.from_api_response(response, self.project_id)
