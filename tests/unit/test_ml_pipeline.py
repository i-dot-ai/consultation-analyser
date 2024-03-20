import pytest

from consultation_analyser.consultations.ml_pipeline import get_themes_for_consultation
from consultation_analyser.consultations import models
from tests import factories


@pytest.mark.django_db
def test_get_themes_for_consultation():
    # TODO - generate this in a neater way - can we fix to specific consultations?
    consultation = factories.ConsultationFactory(name="My new consultation")
    section = factories.SectionFactory(name="Base section", consultation=consultation)
    questions = [
        factories.QuestionFactory(question=q, section=section) for q in factories.FakeConsultationData().all_questions()
    ]
    for r in range(10):
        response = factories.ConsultationResponseFactory()
        _answers = [factories.AnswerFactory(question=q, consultation_response=response) for q in questions]

    get_themes_for_consultation(consultation.id)

    free_text_questions = models.Question.objects.filter(section__consultation=consultation, has_free_text=True)
    no_free_text_questions = models.Question.objects.filter(section__consultation=consultation, has_free_text=False)

    # Check we've generated themes for questions with full text responses, and check fields populated
    for q in free_text_questions:
        themes_for_q = models.Theme.objects.filter(question=q)
        assert themes_for_q.exists()
    example_theme = themes_for_q.first()
    assert example_theme.keywords
    assert example_theme.label
    # Summary not populated yet

    # Check no themes for questions with no free text
    for q in no_free_text_questions:
        themes_for_q = models.Theme.objects.filter(question=q)
        assert not themes_for_q.exists()
