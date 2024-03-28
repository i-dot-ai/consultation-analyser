import unittest
from unittest.mock import patch, MagicMock
from batch_call import BatchJobHandler


@patch("boto3.client")
class TestBatchCall(unittest.TestCase):
    def test_submit_job_batch(self, mock_boto_client):
        # Arrange
        mock_job = MagicMock()
        mock_job.submit_job.return_value = {"jobId": "1234"}
        mock_boto_client.return_value = mock_job

        batch_call = BatchJobHandler()
        job_name = "test_job"
        container_overrides = {"command": ["echo", "hello"]}

        # Act
        result = batch_call.submit_job_batch(job_name, container_overrides)

        # Assert
        expected_message = "The job has been submitted successfully with job id: 1234"
        assert result == expected_message
        mock_boto_client.assert_called_once_with("batch")
        mock_job.submit_job.assert_called_once_with(
            jobName=job_name,
            jobQueue=None,
            jobDefinition=None,
            containerOverrides=container_overrides,
        )

    def test_get_job_status(self, mock_boto_client):
        # Arrange
        mock_job = MagicMock()
        mock_job.describe_jobs.return_value = {"jobs": [{"status": "RUNNABLE"}]}
        mock_boto_client.return_value = mock_job

        batch_call = BatchJobHandler()
        mock_job_id = "1234"

        # Act
        result = batch_call.get_job_status(mock_job_id)

        # Assert
        assert result == "RUNNABLE"
        mock_boto_client.assert_called_once_with("batch")
        mock_job.describe_jobs.assert_called_once_with(jobs=[mock_job_id])

    def test_get_job_list(self, mock_boto_client):
        # Arrange
        mock_job = MagicMock()
        mock_job.list_jobs.return_value = {"jobSummaryList": [], "nextToken": None}
        mock_boto_client.return_value = mock_job

        batch_call = BatchJobHandler()

        # Act
        result = batch_call.get_job_list()

        # Assert
        assert result == []
        mock_boto_client.assert_called_once_with("batch")
        mock_job.list_jobs.assert_called()

    def test_cancel_job(self, mock_boto_client):
        # Arrange
        mock_job = MagicMock()
        mock_boto_client.return_value = mock_job

        batch_call = BatchJobHandler()
        mock_job_id = "1234"

        # Act
        result = batch_call.cancel_job(mock_job_id)

        # Assert
        assert result == "The job has been cancelled successfully."
        mock_boto_client.assert_called_once_with("batch")
        mock_job.cancel_job.assert_called_once_with(jobId=mock_job_id)
