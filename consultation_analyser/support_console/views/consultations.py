from uuid import UUID

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from consultation_analyser.consultations import models
from consultation_analyser.consultations.download_consultation import consultation_to_json
from consultation_analyser.consultations.dummy_data import create_dummy_data
from consultation_analyser.hosting_environment import HostingEnvironment
from consultation_analyser.pipeline.backends.types import (
    NO_SUMMARY_STR,
)
from consultation_analyser.pipeline.processing import run_processing_pipeline


@staff_member_required
def index(request: HttpRequest) -> HttpResponse:
    if request.POST:
        try:
            consultation = create_dummy_data(include_themes=False, number_questions=10)
            user = request.user
            consultation.users.add(user)
            messages.success(request, "A dummy consultation has been generated")
        except RuntimeError as error:
            messages.error(request, error.args[0])
    consultations = models.Consultation.objects.all()
    context = {"consultations": consultations, "production_env": HostingEnvironment.is_production()}
    return render(request, "support_console/consultations/index.html", context=context)


@staff_member_required
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


@staff_member_required
def show(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    consultation = models.Consultation.objects.get(id=consultation_id)
    try:
        if "generate_themes" in request.POST:
            run_processing_pipeline(consultation)
            messages.success(request, "Consultation data has been sent for processing")
        elif "download_json" in request.POST:
            consultation_json = consultation_to_json(consultation)
            response = HttpResponse(consultation_json, content_type="application/json")
            response["Content-Disposition"] = f"attachment; filename={consultation.slug}.json"

            return response

    except RuntimeError as error:
        messages.error(request, error.args[0])
    themes_for_consultation = models.Theme.objects.filter(
        answer__question__section__consultation=consultation
    ).distinct()
    number_of_themes = themes_for_consultation.count()
    number_of_themes_with_summaries = (
        themes_for_consultation.exclude(summary="").exclude(summary=NO_SUMMARY_STR).count()
    )
    number_of_themes_unable_to_summarise = themes_for_consultation.filter(
        summary=NO_SUMMARY_STR
    ).count()
    number_of_themes_not_yet_summarised = themes_for_consultation.filter(summary="").count()
    context = {
        "consultation": consultation,
        "users": consultation.users.all(),
        "number_of_themes": number_of_themes,
        "number_of_themes_with_summaries": number_of_themes_with_summaries,
        "number_of_themes_unable_to_summarise": number_of_themes_unable_to_summarise,
        "number_of_themes_not_yet_summarised": number_of_themes_not_yet_summarised,
    }
    return render(request, "support_console/consultations/show.html", context=context)
