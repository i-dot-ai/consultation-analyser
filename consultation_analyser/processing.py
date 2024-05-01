from django.conf import settings

from consultation_analyser.batch_calls import BatchJobHandler
from consultation_analyser.consultations.llm_summariser import create_llm_summaries_for_consultation
from consultation_analyser.hosting_environment import HostingEnvironment


def process_consultation_themes(consultation):
    # Import only when needed
    from consultation_analyser.consultations.ml_pipeline import save_themes_for_consultation

    save_themes_for_consultation(consultation.id)
    create_llm_summaries_for_consultation(consultation)


def run_processing_pipeline(consultation):
    if HostingEnvironment.is_deployed():
        job_name = f"Theme processing pipeline for consultation: {consultation.slug}"
        command = {"command": ["venv/bin/django-admin", "run_ml_pipeline", "--slug", consultation.slug]}
        batch_handler = BatchJobHandler()
        batch_handler.submit_job_batch(jobName=job_name, containerOverrides=command)
    else:
        process_consultation_themes(consultation)