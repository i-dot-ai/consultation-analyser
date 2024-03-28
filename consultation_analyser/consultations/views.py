from django.shortcuts import render
from django.http import HttpRequest
from django.db.models import Count, Max
from . import models
from django.core.paginator import Paginator


def home(request: HttpRequest):
    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions}
    return render(request, "home.html", context)


def show_question(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    question = models.Question.objects.get(
        slug=question_slug, section__slug=section_slug, section__consultation__slug=consultation_slug
    )
    themes_for_question = models.Theme.objects.filter(answer__question=question).annotate(answer_count=Count("answer"))

    # Get counts
    total_responses = models.Answer.objects.filter(question=question).count()
    highest_theme_count = themes_for_question.aggregate(Max("answer_count"))["answer_count__max"]

    # Get closed question responses (if the question has any)
    multiple_choice = []
    if question.multiple_choice_options:
        multiple_choice = [
            {
                "label": option,
                "count": models.Answer.objects.filter(multiple_choice_responses=option, question=question).count(),
            }
            for option in question.multiple_choice_options
        ]

    context = {
        "question": question,
        "themes": themes_for_question,
        "highest_theme_count": highest_theme_count,
        "total_responses": total_responses,
        "multiple_choice": multiple_choice,
    }
    return render(request, "show_question.html", context)


def get_applied_filters(request: HttpRequest):
    return {
        "keyword": request.GET.get("keyword", ""),
        "theme": request.GET.get("theme", "All"),
        "opinion": request.GET.get("opinion", "All"),
    }


def get_filtered_responses(question: models.Question, applied_filters):
    queryset = models.Answer.objects.filter(question=question, free_text__icontains=applied_filters["keyword"])
    if applied_filters["theme"] != "All" and applied_filters["theme"] != "No theme":
        queryset = queryset.filter(theme=applied_filters["theme"])
    # TO DO: handle answers with "No theme"
    if applied_filters["opinion"] != "All":
        queryset = queryset.filter(multiple_choice_responses=applied_filters["opinion"])
    return queryset


def show_responses(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    question = models.Question.objects.get(
        slug=question_slug, section__slug=section_slug, section__consultation__slug=consultation_slug
    )
    themes_for_question = models.Theme.objects.filter(answer__question=question)
    total_responses = models.Answer.objects.filter(question=question).count()
    applied_filters = get_applied_filters(request)
    responses = get_filtered_responses(question, applied_filters)

    # pagination
    pagination = Paginator(responses, 5)
    page_index = request.GET.get("page", "1")
    current_page = pagination.page(page_index)
    paginated_responses = current_page.object_list

    context = {
        "question": question,
        "responses": paginated_responses,
        "total_responses": total_responses,
        "applied_filters": applied_filters,
        "themes_for_question": themes_for_question,
        "pagination": current_page,
    }
    return render(request, "show_responses.html", context)
