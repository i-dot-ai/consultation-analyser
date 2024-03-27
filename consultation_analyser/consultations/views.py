from django.shortcuts import render
from django.http import HttpRequest
from . import models
from . import public_schemas
from .decorators.renderable_schema import RenderableSchema


def home(request: HttpRequest):
    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions}
    return render(request, "home.html", context)


def schema(request: HttpRequest):
    schemas = [
        RenderableSchema(public_schemas.Consultation),
        RenderableSchema(public_schemas.Section),
        RenderableSchema(public_schemas.Question),
        RenderableSchema(public_schemas.Answer),
        RenderableSchema(public_schemas.ConsultationResponse),
    ]

    return render(request, "schema.html", {"schemas": schemas})


def show_question(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    question = models.Question.objects.get(
        slug=question_slug, section__slug=section_slug, section__consultation__slug=consultation_slug
    )
    themes_for_question = models.Theme.objects.filter(answer__question=question)
    # TODO - probably want counts etc.
    context = {"question": question, "themes": themes_for_question}
    return render(request, "show_question.html", context)
