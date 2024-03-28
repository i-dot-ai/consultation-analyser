from django.shortcuts import render
from django.http import HttpRequest
from . import models


def home(request: HttpRequest):
    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions}
    return render(request, "home.html", context)


def consultation(request: HttpRequest):
    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions}
    return render(request, "consultation.html", context)


def show_question(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    question = models.Question.objects.get(
        slug=question_slug, section__slug=section_slug, section__consultation__slug=consultation_slug
    )
    themes_for_question = models.Theme.objects.filter(answer__question=question)
    # TODO - probably want counts etc.
    context = {"question": question, "themes": themes_for_question}
    return render(request, "show_question.html", context)
