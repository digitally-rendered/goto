"""Tests for the Dataproc service implementation."""

import unittest.mock as mock
import pytest

from gcpoto.services.dataproc import DataprocService
from gcpoto.models.dataproc import DataprocCluster, DataprocJob


@pytest.fixture
def mock_discovery():
    """Mock the Google API discovery build function."""
    with mock.patch("googleapiclient.discovery.build") as mock_build:
        mock_service = mock.MagicMock()
        mock_build.return_value = mock_service
        yield mock_build, mock_service


SAMPLE_CLUSTER_RESPONSE = {
    "clusterName": "my-cluster",
    "projectId": "test-project",
    "clusterUuid": "abc-123-def-456",
    "config": {
        "masterConfig": {
            "numInstances": 1,
            "machineTypeUri": "n1-standard-4",
            "diskConfig": {
                "bootDiskSizeGb": 500,
                "bootDiskType": "pd-standard",
            },
        },
        "workerConfig": {
            "numInstances": 2,
            "machineTypeUri": "n1-standard-4",
            "diskConfig": {
                "bootDiskSizeGb": 500,
                "bootDiskType": "pd-standard",
            },
        },
        "softwareConfig": {
            "imageVersion": "2.1-debian11",
        },
        "gceClusterConfig": {
            "zoneUri": "us-central1-a",
            "networkUri": "default",
        },
    },
    "status": {
        "state": "RUNNING",
        "stateStartTime": "2025-01-01T00:00:00Z",
    },
    "statusHistory": [
        {
            "state": "CREATING",
            "stateStartTime": "2025-01-01T00:00:00Z",
        },
    ],
    "labels": {"env": "test", "team": "data"},
}

SAMPLE_JOB_RESPONSE = {
    "reference": {
        "projectId": "test-project",
        "jobId": "job-12345",
    },
    "placement": {
        "clusterName": "my-cluster",
    },
    "sparkJob": {
        "mainJarFileUri": "gs://my-bucket/my-jar.jar",
        "args": ["arg1", "arg2"],
    },
    "status": {
        "state": "RUNNING",
        "stateStartTime": "2025-01-02T10:00:00Z",
    },
    "scheduling": {
        "maxFailuresPerHour": 3,
        "maxFailuresTotal": 10,
    },
    "driverOutputResourceUri": "gs://my-bucket/output",
    "region": "us-central1",
    "labels": {"job-type": "etl"},
}


class TestDataprocServiceInit:
    """Tests for DataprocService initialization."""

    def test_initialization(self, mock_discovery):
        mock_build, _ = mock_discovery
        service = DataprocService(
            project_id="test-project", credentials_file=None
        )

        assert service.project_id == "test-project"
        assert service.service_name == "dataproc"
        assert service.version == "v1"
        assert service.credentials_file is None
        assert service.resource_model == DataprocCluster
        mock_build.assert_called_once_with("dataproc", "v1", credentials=None)


class TestDataprocClusterModel:
    """Tests for the DataprocCluster model."""

    def test_from_api_response(self):
        cluster = DataprocCluster.from_api_response(SAMPLE_CLUSTER_RESPONSE)

        assert cluster.id == "abc-123-def-456"
        assert cluster.name == "my-cluster"
        assert cluster.type == "dataproc.cluster"
        assert cluster.project == "test-project"
        assert cluster.cluster_name == "my-cluster"
        assert cluster.cluster_uuid == "abc-123-def-456"
        assert cluster.config["masterConfig"]["numInstances"] == 1
        assert cluster.config["workerConfig"]["numInstances"] == 2
        assert cluster.status["state"] == "RUNNING"
        assert len(cluster.status_history) == 1
        assert cluster.status_history[0]["state"] == "CREATING"
        assert cluster.labels == {"env": "test", "team": "data"}
        assert cluster.location == "us-central1-a"

    def test_from_api_response_minimal(self):
        response = {"clusterName": "bare-cluster", "projectId": "p"}
        cluster = DataprocCluster.from_api_response(response)

        assert cluster.name == "bare-cluster"
        assert cluster.cluster_name == "bare-cluster"
        assert cluster.config == {}
        assert cluster.status == {}
        assert cluster.status_history is None
        assert cluster.cluster_uuid is None
        assert cluster.location == ""

    def test_get_tag(self):
        cluster = DataprocCluster.from_api_response(SAMPLE_CLUSTER_RESPONSE)
        assert cluster.get_tag("env") == "test"
        assert cluster.get_tag("team") == "data"
        assert cluster.get_tag("missing") == ""
        assert cluster.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        response = {"clusterName": "bare", "projectId": "p"}
        cluster = DataprocCluster.from_api_response(response)
        assert cluster.get_tag("env") == ""
        assert cluster.get_tag("env", "fallback") == "fallback"


class TestDataprocJobModel:
    """Tests for the DataprocJob model."""

    def test_from_api_response(self):
        job = DataprocJob.from_api_response(SAMPLE_JOB_RESPONSE)

        assert job.id == "job-12345"
        assert job.name == "job-12345"
        assert job.type == "dataproc.job"
        assert job.project == "test-project"
        assert job.cluster_name == "my-cluster"
        assert job.job_type == "spark"
        assert job.status["state"] == "RUNNING"
        assert job.placement["clusterName"] == "my-cluster"
        assert job.scheduling["maxFailuresPerHour"] == 3
        assert job.driver_output_resource_uri == "gs://my-bucket/output"
        assert job.location == "us-central1"
        assert job.labels == {"job-type": "etl"}

    def test_from_api_response_minimal(self):
        response = {
            "reference": {"jobId": "j-1", "projectId": "p"},
            "status": {"state": "PENDING"},
        }
        job = DataprocJob.from_api_response(response)

        assert job.id == "j-1"
        assert job.name == "j-1"
        assert job.cluster_name == ""
        assert job.job_type == ""
        assert job.placement is None
        assert job.scheduling is None
        assert job.driver_output_resource_uri is None

    def test_from_api_response_pyspark_job(self):
        response = {
            "reference": {"jobId": "j-2", "projectId": "p"},
            "placement": {"clusterName": "c"},
            "pysparkJob": {"mainPythonFileUri": "gs://bucket/main.py"},
            "status": {"state": "DONE"},
        }
        job = DataprocJob.from_api_response(response)
        assert job.job_type == "pyspark"

    def test_from_api_response_hive_job(self):
        response = {
            "reference": {"jobId": "j-3", "projectId": "p"},
            "placement": {"clusterName": "c"},
            "hiveJob": {"queryFileUri": "gs://bucket/query.hql"},
            "status": {"state": "DONE"},
        }
        job = DataprocJob.from_api_response(response)
        assert job.job_type == "hive"

    def test_get_tag(self):
        job = DataprocJob.from_api_response(SAMPLE_JOB_RESPONSE)
        assert job.get_tag("job-type") == "etl"
        assert job.get_tag("missing") == ""
        assert job.get_tag("missing", "default") == "default"

    def test_get_tag_no_tags(self):
        response = {
            "reference": {"jobId": "j-1", "projectId": "p"},
            "status": {},
        }
        job = DataprocJob.from_api_response(response)
        assert job.get_tag("any") == ""
        assert job.get_tag("any", "fb") == "fb"


class TestDataprocServiceClusters:
    """Tests for cluster-related methods."""

    def _get_clusters_mock(self, mock_service):
        """Helper to set up clusters mock chain."""
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_regions = mock.MagicMock()
        mock_projects.regions.return_value = mock_regions
        mock_clusters = mock.MagicMock()
        mock_regions.clusters.return_value = mock_clusters
        return mock_clusters

    def test_list_clusters(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = self._get_clusters_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {
            "clusters": [SAMPLE_CLUSTER_RESPONSE],
        }
        mock_clusters.list_next.return_value = None

        service = DataprocService(project_id="test-project")
        results = service.list_clusters("us-central1")

        mock_clusters.list.assert_called_once_with(
            projectId="test-project", region="us-central1"
        )
        assert len(results) == 1
        assert isinstance(results[0], DataprocCluster)
        assert results[0].name == "my-cluster"
        assert results[0].cluster_uuid == "abc-123-def-456"

    def test_list_clusters_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = self._get_clusters_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {}
        mock_clusters.list_next.return_value = None

        service = DataprocService(project_id="test-project")
        results = service.list_clusters("us-central1")

        assert results == []

    def test_list_clusters_pagination(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = self._get_clusters_mock(mock_service)

        mock_list = mock.MagicMock()
        mock_clusters.list.return_value = mock_list
        mock_list.execute.return_value = {
            "clusters": [SAMPLE_CLUSTER_RESPONSE],
        }

        second_cluster = {
            **SAMPLE_CLUSTER_RESPONSE,
            "clusterName": "second-cluster",
            "clusterUuid": "xyz-789",
        }
        mock_list_next = mock.MagicMock()
        mock_clusters.list_next.side_effect = [mock_list_next, None]
        mock_list_next.execute.return_value = {
            "clusters": [second_cluster],
        }

        service = DataprocService(project_id="test-project")
        results = service.list_clusters("us-central1")

        assert len(results) == 2
        assert results[0].name == "my-cluster"
        assert results[1].name == "second-cluster"

    def test_get_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = self._get_clusters_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_clusters.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = DataprocService(project_id="test-project")
        result = service.get_cluster("us-central1", "my-cluster")

        mock_clusters.get.assert_called_once_with(
            projectId="test-project",
            region="us-central1",
            clusterName="my-cluster",
        )
        assert isinstance(result, DataprocCluster)
        assert result.name == "my-cluster"
        assert result.status["state"] == "RUNNING"

    def test_create_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = self._get_clusters_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_clusters.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        config = {
            "masterConfig": {"numInstances": 1, "machineTypeUri": "n1-standard-4"},
            "workerConfig": {"numInstances": 2, "machineTypeUri": "n1-standard-4"},
        }
        service = DataprocService(project_id="test-project")
        result = service.create_cluster(
            "us-central1", "my-cluster", config=config, labels={"env": "test"}
        )

        mock_clusters.create.assert_called_once_with(
            projectId="test-project",
            region="us-central1",
            body={
                "clusterName": "my-cluster",
                "projectId": "test-project",
                "config": config,
                "labels": {"env": "test"},
            },
        )
        assert isinstance(result, DataprocCluster)
        assert result.name == "my-cluster"

    def test_create_cluster_no_config(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = self._get_clusters_mock(mock_service)
        mock_create = mock.MagicMock()
        mock_clusters.create.return_value = mock_create
        mock_create.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        service = DataprocService(project_id="test-project")
        service.create_cluster("us-central1", "my-cluster")

        call_args = mock_clusters.create.call_args
        body = call_args[1]["body"]
        assert body["config"] == {}
        assert "labels" not in body

    def test_update_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = self._get_clusters_mock(mock_service)
        mock_patch = mock.MagicMock()
        mock_clusters.patch.return_value = mock_patch
        mock_patch.execute.return_value = SAMPLE_CLUSTER_RESPONSE

        cluster_config = {
            "config": {
                "workerConfig": {"numInstances": 5},
            },
        }
        service = DataprocService(project_id="test-project")
        result = service.update_cluster(
            "us-central1",
            "my-cluster",
            "config.worker_config.num_instances",
            cluster_config,
        )

        mock_clusters.patch.assert_called_once_with(
            projectId="test-project",
            region="us-central1",
            clusterName="my-cluster",
            updateMask="config.worker_config.num_instances",
            body=cluster_config,
        )
        assert isinstance(result, DataprocCluster)
        assert result.name == "my-cluster"

    def test_delete_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = self._get_clusters_mock(mock_service)
        mock_delete = mock.MagicMock()
        mock_clusters.delete.return_value = mock_delete
        mock_delete.execute.return_value = {}

        service = DataprocService(project_id="test-project")
        result = service.delete_cluster("us-central1", "my-cluster")

        mock_clusters.delete.assert_called_once_with(
            projectId="test-project",
            region="us-central1",
            clusterName="my-cluster",
        )
        mock_delete.execute.assert_called_once()
        assert result is True

    def test_start_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = self._get_clusters_mock(mock_service)
        mock_start = mock.MagicMock()
        mock_clusters.start.return_value = mock_start
        operation_response = {"name": "operation-start-123", "done": False}
        mock_start.execute.return_value = operation_response

        service = DataprocService(project_id="test-project")
        result = service.start_cluster("us-central1", "my-cluster")

        mock_clusters.start.assert_called_once_with(
            projectId="test-project",
            region="us-central1",
            clusterName="my-cluster",
            body={},
        )
        assert result == operation_response

    def test_stop_cluster(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_clusters = self._get_clusters_mock(mock_service)
        mock_stop = mock.MagicMock()
        mock_clusters.stop.return_value = mock_stop
        operation_response = {"name": "operation-stop-123", "done": False}
        mock_stop.execute.return_value = operation_response

        service = DataprocService(project_id="test-project")
        result = service.stop_cluster("us-central1", "my-cluster")

        mock_clusters.stop.assert_called_once_with(
            projectId="test-project",
            region="us-central1",
            clusterName="my-cluster",
            body={},
        )
        assert result == operation_response


class TestDataprocServiceJobs:
    """Tests for job-related methods."""

    def _get_jobs_mock(self, mock_service):
        """Helper to set up jobs mock chain."""
        mock_projects = mock.MagicMock()
        mock_service.projects.return_value = mock_projects
        mock_regions = mock.MagicMock()
        mock_projects.regions.return_value = mock_regions
        mock_jobs = mock.MagicMock()
        mock_regions.jobs.return_value = mock_jobs
        return mock_jobs

    def test_submit_job(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_jobs = self._get_jobs_mock(mock_service)
        mock_submit = mock.MagicMock()
        mock_jobs.submit.return_value = mock_submit
        mock_submit.execute.return_value = SAMPLE_JOB_RESPONSE

        job_config = {
            "placement": {"clusterName": "my-cluster"},
            "sparkJob": {
                "mainJarFileUri": "gs://my-bucket/my-jar.jar",
                "args": ["arg1", "arg2"],
            },
        }

        service = DataprocService(project_id="test-project")
        result = service.submit_job("us-central1", job_config)

        mock_jobs.submit.assert_called_once_with(
            projectId="test-project",
            region="us-central1",
            body={"job": job_config},
        )
        assert isinstance(result, DataprocJob)
        assert result.id == "job-12345"
        assert result.job_type == "spark"
        assert result.cluster_name == "my-cluster"

    def test_get_job(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_jobs = self._get_jobs_mock(mock_service)
        mock_get = mock.MagicMock()
        mock_jobs.get.return_value = mock_get
        mock_get.execute.return_value = SAMPLE_JOB_RESPONSE

        service = DataprocService(project_id="test-project")
        result = service.get_job("us-central1", "job-12345")

        mock_jobs.get.assert_called_once_with(
            projectId="test-project",
            region="us-central1",
            jobId="job-12345",
        )
        assert isinstance(result, DataprocJob)
        assert result.id == "job-12345"
        assert result.status["state"] == "RUNNING"

    def test_list_jobs(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_jobs = self._get_jobs_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_jobs.list.return_value = mock_list
        mock_list.execute.return_value = {
            "jobs": [SAMPLE_JOB_RESPONSE],
        }
        mock_jobs.list_next.return_value = None

        service = DataprocService(project_id="test-project")
        results = service.list_jobs("us-central1")

        mock_jobs.list.assert_called_once_with(
            projectId="test-project", region="us-central1"
        )
        assert len(results) == 1
        assert isinstance(results[0], DataprocJob)
        assert results[0].id == "job-12345"

    def test_list_jobs_empty(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_jobs = self._get_jobs_mock(mock_service)
        mock_list = mock.MagicMock()
        mock_jobs.list.return_value = mock_list
        mock_list.execute.return_value = {}
        mock_jobs.list_next.return_value = None

        service = DataprocService(project_id="test-project")
        results = service.list_jobs("us-central1")

        assert results == []

    def test_list_jobs_pagination(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_jobs = self._get_jobs_mock(mock_service)

        mock_list = mock.MagicMock()
        mock_jobs.list.return_value = mock_list
        mock_list.execute.return_value = {
            "jobs": [SAMPLE_JOB_RESPONSE],
        }

        second_job = {
            **SAMPLE_JOB_RESPONSE,
            "reference": {"projectId": "test-project", "jobId": "job-67890"},
        }
        mock_list_next = mock.MagicMock()
        mock_jobs.list_next.side_effect = [mock_list_next, None]
        mock_list_next.execute.return_value = {
            "jobs": [second_job],
        }

        service = DataprocService(project_id="test-project")
        results = service.list_jobs("us-central1")

        assert len(results) == 2
        assert results[0].id == "job-12345"
        assert results[1].id == "job-67890"

    def test_cancel_job(self, mock_discovery):
        _, mock_service = mock_discovery
        mock_jobs = self._get_jobs_mock(mock_service)
        mock_cancel = mock.MagicMock()
        mock_jobs.cancel.return_value = mock_cancel
        cancelled_response = {
            **SAMPLE_JOB_RESPONSE,
            "status": {"state": "CANCELLED", "stateStartTime": "2025-01-02T11:00:00Z"},
        }
        mock_cancel.execute.return_value = cancelled_response

        service = DataprocService(project_id="test-project")
        result = service.cancel_job("us-central1", "job-12345")

        mock_jobs.cancel.assert_called_once_with(
            projectId="test-project",
            region="us-central1",
            jobId="job-12345",
            body={},
        )
        assert isinstance(result, DataprocJob)
        assert result.status["state"] == "CANCELLED"
