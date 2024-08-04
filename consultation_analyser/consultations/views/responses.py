from typing import Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from .. import models
from .consultations import NO_THEMES_YET_MESSAGE
from .decorators import user_can_see_consultation
from .filters import get_applied_filters, get_filtered_responses


@user_can_see_consultation
@login_required
def index(
    request: HttpRequest,
    consultation_slug: str,
    section_slug: str,
    question_slug: str,
    processing_run_slug: Optional[str] = None,
):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    processing_run_id = request.GET.get("run")
    if processing_run_id:
        processing_run = models.ProcessingRun.objects.get(id=processing_run_id)
        kwargs = {
            "consultation_slug": consultation_slug,
            "processing_run_slug": processing_run.slug,
            "section_slug": section_slug,
            "question_slug": question_slug,
        }
        return redirect("question_responses_runs", **kwargs)
    else:
        try:
            processing_run = consultation.get_processing_run(
                processing_run_slug=processing_run_slug
            )
        except models.ProcessingRun.DoesNotExist:
            return Http404
    all_runs_for_consultation = models.ProcessingRun.objects.filter(consultation=consultation)

    question = models.Question.objects.get(
        slug=question_slug,
        section__slug=section_slug,
        section__consultation__slug=consultation_slug,
    )
    if processing_run:
        themes_for_question = processing_run.get_themes_for_question(question_id=question.id)
    else:
        themes_for_question = models.Theme.objects.none()
        messages.info(request, NO_THEMES_YET_MESSAGE)
    total_responses = models.Answer.objects.filter(question=question).count()
    applied_filters = get_applied_filters(request)
    responses = get_filtered_responses(question, applied_filters)

    # pagination
    pagination = Paginator(responses, 5)
    page_index = request.GET.get("page", "1")
    current_page = pagination.page(page_index)
    paginated_responses = current_page.object_list

    context = {
        "consultation_name": consultation.name,
        "consultation_slug": consultation_slug,
        "processing_run": processing_run,
        "question": question,
        "responses": paginated_responses,
        "total_responses": total_responses,
        "applied_filters": applied_filters,
        "themes": themes_for_question,
        "pagination": current_page,
        "all_runs": all_runs_for_consultation,
    }

    return render(request, "consultations/responses/index.html", context)
