import datetime

from django.shortcuts import render, redirect, reverse
from django.http import HttpRequest

from . import models
from consultation_analyser.consultations import ml_pipeline
from consultation_analyser.consultations.dummy_data import DummyConsultation


# TODO - this is placeholder for homepage - useful things to help us test
def home(request: HttpRequest):
    consultations = models.Consultation.objects.all()
    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions, "consultations": consultations}
    if request.POST:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%D-%H:%M:%S")
        name = f"Dummy Consultation generated at {timestamp}"
        DummyConsultation(name=name, blank_themes=True)  # TODO - how to run when not local?
        consultation = models.Consultation.objects.get(name=name)
        return redirect(reverse("show_consultation", args=(consultation.slug,)))
    return render(request, "home.html", context)


def show_question(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    question = models.Question.objects.get(
        slug=question_slug, section__slug=section_slug, section__consultation__slug=consultation_slug
    )
    themes_for_question = models.Theme.objects.filter(answer__question=question)
    # TODO - probably want counts etc.
    context = {"question": question, "themes": themes_for_question}
    return render(request, "show_question.html", context)


# TODO - replace with a proper view! This is for testing.
def show_consultation(request: HttpRequest, consultation_slug: str):
    if request.POST:
        ml_pipeline.dummy_save_themes_for_consultation(consultation_slug)
    consultation = models.Consultation.objects.get(slug=consultation_slug)
    questions = models.Question.objects.filter(section__consultation=consultation)
    context = {"consultation": consultation, "questions": questions}
    return render(request, "show_consultation.html", context)
