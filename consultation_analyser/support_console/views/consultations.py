from uuid import UUID

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from consultation_analyser.consultations import models
from consultation_analyser.consultations.download_consultation import consultation_to_json
from consultation_analyser.consultations.dummy_data import create_dummy_data
from consultation_analyser.hosting_environment import HostingEnvironment
from consultation_analyser.pipeline.backends.types import (
    NO_SUMMARY_STR,
)
from consultation_analyser.pipeline.processing import run_llm_summariser, run_processing_pipeline
from consultation_analyser.support_console.decorators import support_login_required


# @support_login_required
def index(request: HttpRequest) -> HttpResponse:
    if request.POST:
        try:
            consultation = create_dummy_data()
            user = request.user
            consultation.users.add(user)
            messages.success(request, "A dummy consultation has been generated")
        except RuntimeError as error:
            messages.error(request, error.args[0])
    consultations = models.Consultation.objects.all()
    context = {"consultations": consultations, "production_env": HostingEnvironment.is_production()}
    return render(request, "support_console/consultations/index.html", context=context)


# @support_login_required
def delete(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    consultation = models.Consultation.objects.get(id=consultation_id)
    context = {
        "consultation": consultation,
    }

    if request.POST:
        if "confirm_deletion" in request.POST:
            consultation.delete()
            messages.success(request, "The consultation has been deleted")
            return redirect("/support/consultations/")

    return render(request, "support_console/consultations/delete.html", context=context)


def get_number_themes_for_processing_run(processing_run):
    """
    Get total themes for processing run.
    If processing_run not specified, get the latest processing run if exists.
    """
    if not processing_run:
        return 0, 0
    total_themes = processing_run.themes.count()
    total_with_summaries = (
        processing_run.themes.exclude(summary="").exclude(summary=NO_SUMMARY_STR).count()
    )
    return total_themes, total_with_summaries


@support_login_required
def show(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    consultation = models.Consultation.objects.get(id=consultation_id)
    try:
        if "generate_themes" in request.POST:
            run_processing_pipeline(consultation)
            messages.success(request, "Consultation data has been sent for processing")
        elif "llm_summarisation" in request.POST:
            if not consultation.latest_processing_run:
                messages.error(request, "Cannot run LLM summarisation as no topics created")
            else:
                run_llm_summariser(consultation)
                messages.success(
                    request, "(Re-)running LLM summarisation on the latest processing run"
                )
        elif "download_json" in request.POST:
            consultation_json = consultation_to_json(consultation)
            response = HttpResponse(consultation_json, content_type="application/json")
            response["Content-Disposition"] = f"attachment; filename={consultation.slug}.json"
            return response

    except RuntimeError as error:
        messages.error(request, error.args[0])

    # For display, just take latest themes
    total_themes, total_with_summaries = get_number_themes_for_processing_run(
        consultation.latest_processing_run
    )
    processing_runs = consultation.processingrun_set.all().order_by("created_at")

    context = {
        "consultation": consultation,
        "processing_runs": processing_runs,
        "users": consultation.users.all(),
        "total_themes": total_themes,
        "total_with_summaries": total_with_summaries,
    }
    return render(request, "support_console/consultations/show.html", context=context)


@support_login_required
def download(request: HttpRequest, consultation_slug: str, processing_run_slug: str):
    # If no processing_run, defaults to latest if exists
    consultation = models.Consultation.objects.get(slug=consultation_slug)
    processing_run = models.ProcessingRun.objects.get(
        consultation=consultation, slug=processing_run_slug
    )
    consultation_json = consultation_to_json(
        consultation=consultation, processing_run=processing_run
    )
    response = HttpResponse(consultation_json, content_type="application/json")
    response["Content-Disposition"] = f"attachment; filename={consultation.slug}.json"
    return response
