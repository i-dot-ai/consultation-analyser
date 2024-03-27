from django.shortcuts import render
from django.http import HttpRequest
from django.db.models import Count, Max
from . import models


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
