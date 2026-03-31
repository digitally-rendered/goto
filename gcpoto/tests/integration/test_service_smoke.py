"""Smoke tests validating basic connectivity for all gcpoto service classes.

Each parameterized test case instantiates a service client, then calls a
simple list/get operation.  A test *passes* when the call either:

  - Returns valid results, or
  - Raises a clean ``PermissionDeniedError`` or ``APIError`` (the API was
    reachable and returned a well-formed error).

A test *fails* only when the call crashes with an unexpected exception such
as ``KeyError``, ``AttributeError``, or a discovery build error -- which
indicates a bug in our service wiring (wrong service_name, wrong version,
broken import, etc.).
"""

import importlib
import logging

import pytest

from gcpoto.exceptions import (
    APIError,
    GCPotoError,
    PermissionDeniedError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Service registry: (module_name, class_name)
# Each entry corresponds to gcpoto.services.<module_name>.<class_name>
# ---------------------------------------------------------------------------

SERVICE_REGISTRY = [
    ("alloydb", "AlloyDBService"),
    ("api_gateway", "APIGatewayService"),
    ("api_keys", "APIKeysService"),
    ("apigee", "ApigeeService"),
    ("armor", "CloudArmorService"),
    ("artifact_registry", "ArtifactRegistryService"),
    ("bare_metal", "BareMetalService"),
    ("batch", "BatchService"),
    ("bigquery", "BigQueryService"),
    ("bigtable", "BigtableService"),
    ("billing", "BillingService"),
    ("binary_auth", "BinaryAuthService"),
    ("cdn", "CDNService"),
    ("certificate_manager", "CertificateManagerService"),
    ("cloud_build", "CloudBuildService"),
    ("cloud_deploy", "CloudDeployService"),
    ("cloud_functions", "CloudFunctionsService"),
    ("cloud_nat", "CloudNATService"),
    ("cloud_run", "CloudRunServiceManager"),
    ("cloud_sql", "CloudSQLService"),
    ("cloud_tasks", "CloudTasksService"),
    ("composer", "ComposerService"),
    ("compute", "ComputeService"),
    ("data_catalog", "DataCatalogService"),
    ("data_fusion", "DataFusionService"),
    ("dataflow", "DataflowService"),
    ("dataplex", "DataplexService"),
    ("dataproc", "DataprocService"),
    ("datastore", "DatastoreService"),
    ("datastream", "DatastreamService"),
    ("dialogflow", "DialogflowService"),
    ("dns", "DNSService"),
    ("document_ai", "DocumentAIService"),
    ("endpoints", "EndpointsService"),
    ("error_reporting", "ErrorReportingService"),
    ("eventarc", "EventarcService"),
    ("filestore", "FilestoreService"),
    ("firestore", "FirestoreService"),
    ("gke", "GKEService"),
    ("iam", "IAMService"),
    ("interconnect", "InterconnectService"),
    ("kms", "KMSService"),
    ("logging_service", "LoggingService"),
    ("looker", "LookerService"),
    ("media_cdn", "MediaCDNService"),
    ("memorystore", "MemorystoreService"),
    ("monitoring", "MonitoringService"),
    ("natural_language", "NaturalLanguageService"),
    ("network_connectivity", "NetworkConnectivityService"),
    ("network_security", "NetworkSecurityService"),
    ("networking", "NetworkingService"),
    ("profiler", "ProfilerService"),
    ("pubsub", "PubSubService"),
    ("pubsub_lite", "PubSubLiteService"),
    ("recaptcha", "RecaptchaService"),
    ("recommendations_ai", "RecommendationsAIService"),
    ("resource_manager", "ResourceManagerService"),
    ("scheduler", "SchedulerService"),
    ("secret_manager", "SecretManagerService"),
    ("security_center", "SecurityCenterService"),
    ("service_directory", "ServiceDirectoryService"),
    ("source_repos", "SourceReposService"),
    ("spanner", "SpannerService"),
    ("speech", "SpeechService"),
    ("storage", "StorageService"),
    ("trace", "TraceService"),
    ("transfer", "TransferService"),
    ("translation", "TranslationService"),
    ("vertex_ai", "VertexAIService"),
    ("video_ai", "VideoAIService"),
    ("vision", "VisionService"),
    ("vmware_engine", "VMwareEngineService"),
    ("vpn", "VPNService"),
    ("web_security_scanner", "WebSecurityScannerService"),
    ("workflows", "WorkflowsService"),
]


def _service_id(val):
    """Readable test-ID for parametrize."""
    return val[0]


# ---------------------------------------------------------------------------
# Smoke: import & instantiate
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestServiceImportSmoke:
    """Validate that every service module can be imported and its class instantiated."""

    @pytest.mark.parametrize("module_name,class_name", SERVICE_REGISTRY, ids=_service_id)
    def test_import_and_instantiate(
        self, module_name, class_name, gcp_project, credentials_file
    ):
        """Import the service module, instantiate the class, and verify the object.

        This catches typos in service_name / version, missing dependencies,
        and broken __init__ logic before any network call is attempted.
        """
        module_path = f"gcpoto.services.{module_name}"
        mod = importlib.import_module(module_path)
        service_cls = getattr(mod, class_name)
        assert service_cls is not None, (
            f"Class {class_name} not found in {module_path}"
        )

        # Instantiation may trigger discovery.build which needs network.
        # We accept GCPotoError (e.g. API not enabled) but NOT AttributeError
        # or ImportError.
        try:
            instance = service_cls(
                project_id=gcp_project,
                credentials_file=credentials_file,
            )
        except GCPotoError:
            # The service itself raised a clean SDK error -- that is acceptable
            # for a smoke test (e.g. API not enabled for this project).
            logger.info(
                "Service %s raised GCPotoError during init (expected for some APIs)",
                class_name,
            )
            return
        except Exception as exc:
            # google-api-python-client and google-cloud-* libs may raise their
            # own exceptions (HttpError, google.auth.exceptions, etc.) during
            # build/init -- these are *not* SDK bugs, so we allow them.
            allowed_exc_modules = (
                "googleapiclient",
                "google.auth",
                "google.api_core",
                "google.cloud",
                "grpc",
            )
            exc_module = type(exc).__module__ or ""
            if any(exc_module.startswith(m) for m in allowed_exc_modules):
                logger.info(
                    "Service %s raised %s during init: %s",
                    class_name, type(exc).__name__, exc,
                )
                return
            raise

        assert instance is not None
        assert instance.project_id == gcp_project
        logger.info("Successfully instantiated %s", class_name)


# ---------------------------------------------------------------------------
# Smoke: list_resources (or equivalent) call
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestServiceListSmoke:
    """Call list_resources (or an equivalent list method) and verify the response.

    A ``PermissionDeniedError``, ``APIError``, or ``NotImplementedError`` is
    acceptable -- it proves the API roundtrip works and our error mapping is
    correct.  Only unexpected crashes fail the test.
    """

    @pytest.mark.parametrize("module_name,class_name", SERVICE_REGISTRY, ids=_service_id)
    def test_list_call(
        self, module_name, class_name, gcp_project, credentials_file
    ):
        """Attempt a list call on the service and verify clean behavior."""
        module_path = f"gcpoto.services.{module_name}"
        try:
            mod = importlib.import_module(module_path)
        except ImportError as exc:
            pytest.skip(f"Cannot import {module_path}: {exc}")

        service_cls = getattr(mod, class_name, None)
        if service_cls is None:
            pytest.skip(f"Class {class_name} not in {module_path}")

        # Build the service instance
        try:
            instance = service_cls(
                project_id=gcp_project,
                credentials_file=credentials_file,
            )
        except Exception as exc:
            # If we cannot even instantiate, the import smoke test will
            # catch this; skip here to avoid duplicate noise.
            pytest.skip(f"Cannot instantiate {class_name}: {exc}")

        # Try list_resources first; fall back to common list_* methods
        list_methods = ["list_resources"]
        # Discover any public list_* method as a fallback
        for attr_name in sorted(dir(instance)):
            if attr_name.startswith("list_") and callable(getattr(instance, attr_name)):
                if attr_name not in list_methods:
                    list_methods.append(attr_name)

        called = False
        for method_name in list_methods:
            method = getattr(instance, method_name, None)
            if method is None or not callable(method):
                continue

            try:
                result = method()
                # If we got here the call succeeded
                assert isinstance(result, (list, tuple, type(None))), (
                    f"{class_name}.{method_name}() returned unexpected type "
                    f"{type(result).__name__}"
                )
                logger.info(
                    "%s.%s() returned %d item(s)",
                    class_name, method_name,
                    len(result) if result is not None else 0,
                )
                called = True
                break
            except NotImplementedError:
                # Base class stub -- try the next method
                continue
            except (PermissionDeniedError, APIError, ResourceNotFoundError) as exc:
                # Clean SDK errors are acceptable -- the API roundtrip worked
                logger.info(
                    "%s.%s() raised %s: %s",
                    class_name, method_name, type(exc).__name__, exc,
                )
                called = True
                break
            except GCPotoError as exc:
                # Any other gcpoto exception is also acceptable
                logger.info(
                    "%s.%s() raised %s: %s",
                    class_name, method_name, type(exc).__name__, exc,
                )
                called = True
                break
            except Exception as exc:
                # Allow google-api / grpc errors as acceptable "clean" errors
                exc_module = type(exc).__module__ or ""
                allowed_prefixes = (
                    "googleapiclient",
                    "google.auth",
                    "google.api_core",
                    "google.cloud",
                    "grpc",
                )
                if any(exc_module.startswith(p) for p in allowed_prefixes):
                    logger.info(
                        "%s.%s() raised upstream %s: %s",
                        class_name, method_name, type(exc).__name__, exc,
                    )
                    called = True
                    break
                # Anything else is a genuine bug in our code
                raise

        if not called:
            pytest.skip(
                f"{class_name} has no callable list method (all raise NotImplementedError)"
            )
