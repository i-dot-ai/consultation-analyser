import logging
import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from consultation_analyser.consultations.upload_consultation import upload_consultation

from .. import models
from ..forms.consultation_upload_form import ConsultationUploadForm
from .decorators import user_can_see_consultation

logger = logging.getLogger("django.server")

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
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug)

    context = {"questions": questions, "consultation": consultation}

    if not consultation.has_themes():
        messages.info(request, NO_THEMES_YET_MESSAGE)

    return render(request, "consultations/consultations/show.html", context)


@login_required
def new(request: HttpRequest):
    if not request.POST:
        form = ConsultationUploadForm()
    else:
        stime = time.time()
        logger.info("Upload received")
        form = ConsultationUploadForm(request.POST, request.FILES)
        if form.is_valid():
            logger.info("Running upload_consultation")
            upload_consultation(request.FILES["consultation_json"], request.user)
            etime = time.time()
            logger.info(f"Total upload time: {etime - stime}s")
            return render(request, "consultations/consultations/uploaded.html", {})

    return render(request, "consultations/consultations/new.html", {"form": form})
