"""Session class for creating GCP service clients (boto3-style)."""

import importlib
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Registry mapping service names to their service classes
_SERVICE_REGISTRY: Dict[str, tuple] = {}  # name -> (module_path, class_name)


def _register_services():
    """Register all known services."""
    services = {
        "storage": ("gcpoto.services.storage", "StorageService"),
        "bigquery": ("gcpoto.services.bigquery", "BigQueryService"),
        "billing": ("gcpoto.services.billing", "BillingService"),
        "pubsub": ("gcpoto.services.pubsub", "PubSubService"),
        "compute": ("gcpoto.services.compute", "ComputeService"),
        "resource_manager": (
            "gcpoto.services.resource_manager",
            "ResourceManagerService",
        ),
        "dns": ("gcpoto.services.dns", "DNSService"),
        "secret_manager": (
            "gcpoto.services.secret_manager",
            "SecretManagerService",
        ),
        "kms": ("gcpoto.services.kms", "KMSService"),
        "iam": ("gcpoto.services.iam", "IAMService"),
        "cloud_sql": ("gcpoto.services.cloud_sql", "CloudSQLService"),
        "cloud_functions": (
            "gcpoto.services.cloud_functions",
            "CloudFunctionsService",
        ),
        "cloud_run": ("gcpoto.services.cloud_run", "CloudRunServiceManager"),
        "cloud_tasks": ("gcpoto.services.cloud_tasks", "CloudTasksService"),
        "scheduler": ("gcpoto.services.scheduler", "SchedulerService"),
        "logging": ("gcpoto.services.logging_service", "LoggingService"),
        "networking": ("gcpoto.services.networking", "NetworkingService"),
        "dataflow": ("gcpoto.services.dataflow", "DataflowService"),
        "dataproc": ("gcpoto.services.dataproc", "DataprocService"),
        "gke": ("gcpoto.services.gke", "GKEService"),
        "firestore": ("gcpoto.services.firestore", "FirestoreService"),
        "spanner": ("gcpoto.services.spanner", "SpannerService"),
        "bigtable": ("gcpoto.services.bigtable", "BigtableService"),
        "artifact_registry": (
            "gcpoto.services.artifact_registry",
            "ArtifactRegistryService",
        ),
        "monitoring": ("gcpoto.services.monitoring", "MonitoringService"),
        "memorystore": ("gcpoto.services.memorystore", "MemorystoreService"),
        "eventarc": ("gcpoto.services.eventarc", "EventarcService"),
        "workflows": ("gcpoto.services.workflows", "WorkflowsService"),
        "filestore": ("gcpoto.services.filestore", "FilestoreService"),
        "transfer": ("gcpoto.services.transfer", "TransferService"),
        "armor": ("gcpoto.services.armor", "CloudArmorService"),
        "cdn": ("gcpoto.services.cdn", "CDNService"),
        "vertex_ai": ("gcpoto.services.vertex_ai", "VertexAIService"),
        "api_gateway": ("gcpoto.services.api_gateway", "APIGatewayService"),
        "alloydb": ("gcpoto.services.alloydb", "AlloyDBService"),
        "batch": ("gcpoto.services.batch", "BatchService"),
        "binary_auth": ("gcpoto.services.binary_auth", "BinaryAuthService"),
        "certificate_manager": (
            "gcpoto.services.certificate_manager",
            "CertificateManagerService",
        ),
        "cloud_build": ("gcpoto.services.cloud_build", "CloudBuildService"),
        "cloud_deploy": ("gcpoto.services.cloud_deploy", "CloudDeployService"),
        "cloud_nat": ("gcpoto.services.cloud_nat", "CloudNATService"),
        "composer": ("gcpoto.services.composer", "ComposerService"),
        "data_catalog": ("gcpoto.services.data_catalog", "DataCatalogService"),
        "datastream": ("gcpoto.services.datastream", "DatastreamService"),
        "dialogflow": ("gcpoto.services.dialogflow", "DialogflowService"),
        "document_ai": ("gcpoto.services.document_ai", "DocumentAIService"),
        "endpoints": ("gcpoto.services.endpoints", "EndpointsService"),
        "error_reporting": (
            "gcpoto.services.error_reporting",
            "ErrorReportingService",
        ),
        "natural_language": (
            "gcpoto.services.natural_language",
            "NaturalLanguageService",
        ),
        "profiler": ("gcpoto.services.profiler", "ProfilerService"),
        "pubsub_lite": ("gcpoto.services.pubsub_lite", "PubSubLiteService"),
        "security_center": (
            "gcpoto.services.security_center",
            "SecurityCenterService",
        ),
        "service_directory": (
            "gcpoto.services.service_directory",
            "ServiceDirectoryService",
        ),
        "speech": ("gcpoto.services.speech", "SpeechService"),
        "trace": ("gcpoto.services.trace", "TraceService"),
        "translation": ("gcpoto.services.translation", "TranslationService"),
        "vision": ("gcpoto.services.vision", "VisionService"),
        "vpn": ("gcpoto.services.vpn", "VPNService"),
        "apigee": ("gcpoto.services.apigee", "ApigeeService"),
        "data_fusion": ("gcpoto.services.data_fusion", "DataFusionService"),
        "vmware_engine": (
            "gcpoto.services.vmware_engine",
            "VMwareEngineService",
        ),
        "datastore": ("gcpoto.services.datastore", "DatastoreService"),
        "network_security": (
            "gcpoto.services.network_security",
            "NetworkSecurityService",
        ),
        "web_security_scanner": (
            "gcpoto.services.web_security_scanner",
            "WebSecurityScannerService",
        ),
        "api_keys": ("gcpoto.services.api_keys", "APIKeysService"),
        "bare_metal": ("gcpoto.services.bare_metal", "BareMetalService"),
        "dataplex": ("gcpoto.services.dataplex", "DataplexService"),
        "interconnect": (
            "gcpoto.services.interconnect",
            "InterconnectService",
        ),
        "looker": ("gcpoto.services.looker", "LookerService"),
        "media_cdn": ("gcpoto.services.media_cdn", "MediaCDNService"),
        "network_connectivity": (
            "gcpoto.services.network_connectivity",
            "NetworkConnectivityService",
        ),
        "recaptcha": ("gcpoto.services.recaptcha", "RecaptchaService"),
        "recommendations_ai": (
            "gcpoto.services.recommendations_ai",
            "RecommendationsAIService",
        ),
        "source_repos": (
            "gcpoto.services.source_repos",
            "SourceReposService",
        ),
        "video_ai": ("gcpoto.services.video_ai", "VideoAIService"),
    }
    _SERVICE_REGISTRY.update(services)


# Populate registry on module import
_register_services()


class Session:
    """A boto3-inspired session that creates GCP service clients.

    The Session manages configuration (project, credentials, region) and
    acts as a factory for service client instances. Created clients are
    cached so that repeated calls to ``client()`` with the same service
    name return the same instance.

    Example::

        session = Session(project_id="my-project")
        storage = session.client("storage")
        dns = session.client("dns")
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_file: Optional[str] = None,
        region: Optional[str] = None,
        zone: Optional[str] = None,
    ):
        """Initialize the session.

        Args:
            project_id: The GCP project ID to use for API calls.
            credentials_file: Optional path to a service account credentials
                JSON file.
            region: Optional default GCP region (e.g. ``us-central1``).
            zone: Optional default GCP zone (e.g. ``us-central1-a``).
        """
        self.project_id = project_id
        self.credentials_file = credentials_file
        self.region = region
        self.zone = zone
        self._clients: Dict[str, Any] = {}

        logger.info(
            "Created session for project %s (region=%s, zone=%s)",
            self.project_id,
            self.region,
            self.zone,
        )

    def client(self, service_name: str) -> Any:
        """Create or retrieve a cached service client.

        The service class is lazy-imported the first time a particular
        service is requested. Subsequent calls with the same
        ``service_name`` return the cached instance.

        Args:
            service_name: The name of the service (e.g. ``"storage"``,
                ``"dns"``, ``"api_gateway"``).

        Returns:
            An instance of the requested service class.

        Raises:
            ValueError: If ``service_name`` is not in the registry.
            ValueError: If ``project_id`` has not been set on the session.
            ImportError: If the service module cannot be imported.
        """
        if service_name in self._clients:
            logger.debug("Returning cached client for %s", service_name)
            return self._clients[service_name]

        if service_name not in _SERVICE_REGISTRY:
            raise ValueError(
                f"Unknown service: '{service_name}'. "
                f"Available services: {', '.join(sorted(_SERVICE_REGISTRY))}"
            )

        if not self.project_id:
            raise ValueError(
                "project_id is required to create a service client. "
                "Pass it to Session() or set it before calling client()."
            )

        module_path, class_name = _SERVICE_REGISTRY[service_name]

        logger.info("Creating client for service %s", service_name)

        module = importlib.import_module(module_path)
        service_class = getattr(module, class_name)

        instance = service_class(
            project_id=self.project_id,
            credentials_file=self.credentials_file,
        )

        self._clients[service_name] = instance
        return instance

    def get_available_services(self) -> List[str]:
        """Return a sorted list of all registered service names.

        Returns:
            A sorted list of service name strings.
        """
        return sorted(_SERVICE_REGISTRY.keys())

    def get_credentials(self) -> Optional[str]:
        """Return the configured credentials file path.

        Returns:
            The path to the credentials file, or ``None`` if not set.
        """
        return self.credentials_file
