from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import render

from .. import models
from .consultations import NO_THEMES_YET_MESSAGE
from .decorators import user_can_see_consultation
from .filters import get_applied_filters, get_filtered_responses


@user_can_see_consultation
@login_required
def index(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    question = models.Question.objects.get(
        slug=question_slug,
        section__slug=section_slug,
        section__consultation__slug=consultation_slug,
    )

    consultation = question.section.consultation
    if not consultation.has_themes():
        messages.info(request, NO_THEMES_YET_MESSAGE)

    themes_for_question = models.Theme.objects.filter(answer__question=question).distinct()
    total_responses = models.Answer.objects.filter(question=question).count()
    applied_filters = get_applied_filters(request)
    responses = get_filtered_responses(question, applied_filters)

    # pagination
    pagination = Paginator(responses, 5)
    page_index = request.GET.get("page", "1")
    current_page = pagination.page(page_index)
    paginated_responses = current_page.object_list

    context = {
        "consultation_slug": consultation_slug,
        "question": question,
        "responses": paginated_responses,
        "total_responses": total_responses,
        "applied_filters": applied_filters,
        "themes": themes_for_question,
        "pagination": current_page,
    }

    return render(request, "consultations/responses/index.html", context)
