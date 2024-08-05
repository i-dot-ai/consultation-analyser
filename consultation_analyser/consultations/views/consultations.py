import logging
from typing import Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage as storage
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from consultation_analyser.consultations.jobs.upload_consultation import async_upload_consultation

from .. import models
from ..forms.consultation_upload_form import ConsultationUploadForm
from .decorators import user_can_see_consultation

logger = logging.getLogger("upload")


NO_THEMES_YET_MESSAGE = "We are processing your consultation. Themes have not been generated yet."


@login_required
def index(request: HttpRequest) -> HttpResponse:
    consultations = request.user.consultation_set.all()
    user = request.user
    is_staff = user.is_staff
    context = {"consultations": consultations, "is_staff": is_staff}
    return render(request, "consultations/consultations/index.html", context)


@user_can_see_consultation
@login_required
def show(
    request: HttpRequest, consultation_slug: str, processing_run_slug: Optional[str] = None
) -> HttpResponse:
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    all_runs_for_consultation = models.ProcessingRun.objects.filter(consultation=consultation)
    if all_runs_for_consultation.count() == 0:
        messages.info(request, NO_THEMES_YET_MESSAGE)
        processing_run = None
    else:
        try:
            processing_run = consultation.get_processing_run(processing_run_slug)
        except (
            models.ProcessingRun.DoesNotExist
        ):  # Should only have processing runs from that consultation
            return Http404

    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug)
    context = {
        "questions": questions,
        "consultation": consultation,
        "processing_run": processing_run,
        "all_runs": all_runs_for_consultation,
    }
    return render(request, "consultations/consultations/show.html", context)


@login_required
def new(request: HttpRequest):
    if not request.POST:
        form = ConsultationUploadForm()
    else:
        logger.info("Upload received")
        form = ConsultationUploadForm(request.POST, request.FILES)
        if form.is_valid():
            logger.info("Enqueueing upload_consultation job")
            file_path = storage.save(
                request.FILES["consultation_json"].name, request.FILES["consultation_json"]
            )
            async_upload_consultation.delay(file_path, request.user.id)
            return render(request, "consultations/consultations/uploaded.html", {})

    return render(request, "consultations/consultations/new.html", {"form": form})
