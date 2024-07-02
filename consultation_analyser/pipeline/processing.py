from typing import Optional

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from consultation_analyser.consultations.models import ProcessingRun
from consultation_analyser.hosting_environment import HostingEnvironment
from consultation_analyser.pipeline.backends.bertopic import BERTopicBackend
from consultation_analyser.pipeline.backends.dummy_llm_backend import DummyLLMBackend
from consultation_analyser.pipeline.backends.ollama_llm_backend import OllamaLLMBackend
from consultation_analyser.pipeline.backends.sagemaker_llm_backend import SagemakerLLMBackend
from consultation_analyser.pipeline.batch_calls import BatchJobHandler
from consultation_analyser.pipeline.llm_summariser import (
    create_llm_summaries_for_processing_run,
)
from consultation_analyser.pipeline.ml_pipeline import save_themes_for_processing_run


def get_llm_backend(llm_identifier: Optional[str] = None):
    """Get the LLM backend configured for this env.

    Will resolve llm_identifier to be settings.LLM_BACKEND unless llm_identifier is passed.

    Args:
        llm_identifier: A string, either "fake", "sagemaker" or "ollama/$model_name". Optional.

    Raises:
        ImproperlyConfigured: the resolved llm_identifier does not belong to the above list of possible identifiers.
    """

    if not llm_identifier and settings.LLM_BACKEND is not None:
        llm_identifier = settings.LLM_BACKEND

    if llm_identifier == "fake" or not llm_identifier:
        return DummyLLMBackend()
    elif llm_identifier == "sagemaker":
        return SagemakerLLMBackend()
    elif llm_identifier.startswith("ollama"):
        model = llm_identifier.split("/")[1]
        return OllamaLLMBackend(model)
    else:
        raise ImproperlyConfigured(
            f"Invalid llm specified: {llm_identifier}. Check settings.LLM_BACKEND or the caller of get_llm_backend()."
        )


def process_consultation_themes(consultation, topic_backend=None, llm_backend=None):
    processing_run = ProcessingRun(consultation=consultation)
    processing_run.save()
    # TODO - add more metadata to processing run

    if not topic_backend:
        topic_backend = BERTopicBackend()

    if not llm_backend:
        llm_backend = get_llm_backend(llm_backend)

    save_themes_for_processing_run(topic_backend, processing_run)
    create_llm_summaries_for_processing_run(llm_backend, processing_run)


def run_processing_pipeline(consultation):
    if HostingEnvironment.is_deployed():
        job_name = f"generate-themes-{consultation.slug}"[:128]  # Must be <=128 , no spaces
        command = {
            "command": [
                "venv/bin/django-admin",
                "run_ml_pipeline",
                "--consultation_slug",
                consultation.slug,
            ]
        }
        batch_handler = BatchJobHandler()
        batch_handler.submit_job_batch(jobName=job_name, containerOverrides=command)
    else:
        process_consultation_themes(consultation)
