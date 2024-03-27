"""
Simple class and functions to deploy and monitor AWS Batch jobs. 
"""

import boto3
import os

# load env variables
BATCH_JOB_QUEUE = os.environ.get("BATCH_JOB_QUEUE")
BATCH_JOB_DEFINITION = os.environ.get("BATCH_JOB_DEFINITION")


class BatchJobHandler:

    def submit_job_batch(self, jobName: str, containerOverrides: dict) -> None:
        client = boto3.client("batch")
        job = client.submit_job(
            jobName=jobName,
            jobQueue=BATCH_JOB_QUEUE,
            jobDefinition=BATCH_JOB_DEFINITION,
            containerOverrides=containerOverrides,
        )
        return "The job has been submitted successfully with job id: " + job["jobId"]

    def get_job_status(self, jobId: str) -> str:
        client = boto3.client("batch")

        job = client.describe_jobs(jobs=[jobId])
        return job["jobs"][0]["status"]

    def get_job_list(self) -> list:
        client = boto3.client("batch")
        jobs = client.list_jobs(jobQueue=BATCH_JOB_QUEUE)

        while jobs["nextToken"] is not None:
            jobs = client.list_jobs(
                jobQueue=BATCH_JOB_QUEUE, nextToken=jobs["nextToken"]
            )

        return jobs["jobSummaryList"]

    def cancel_job(self, jobId: str) -> None:
        client = boto3.client("batch")
        client.cancel_job(jobId=jobId)
        return "The job has been cancelled successfully."
