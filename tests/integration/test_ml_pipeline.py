import pytest

from consultation_analyser.consultations.ml_pipeline import (
    save_themes_for_consultation,
)
from consultation_analyser.consultations import models
from tests import factories


@pytest.mark.django_db
def test_save_themes_for_consultation():
    consultation = factories.ConsultationFactory(name="My new consultation")
    section = factories.SectionFactory(name="Base section", consultation=consultation)
    free_text_question1 = factories.QuestionFactory(section=section, has_free_text=True, slug="mars-bar-recipe-change")
    free_text_question2 = factories.QuestionFactory(section=section, has_free_text=True, slug="is-crunchie-too-sweet")
    no_free_text_question = factories.QuestionFactory(
        section=section, has_free_text=False, slug="favorite-cadbury-chocolate-bar"
    )

    questions = [free_text_question1, free_text_question2, no_free_text_question]
    for r in range(10):
        response = factories.ConsultationResponseFactory(consultation=consultation)
        [factories.AnswerFactory(question=q, consultation_response=response, theme=None) for q in questions]

    save_themes_for_consultation(consultation.id)

    # Check we've generated themes for questions with full text responses, and check fields populated
    for q in [free_text_question1, free_text_question2]:
        themes_for_q = models.Theme.objects.filter(answer__question=q)
        assert themes_for_q.exists()
    example_theme = themes_for_q.first()
    assert example_theme.keywords
    assert example_theme.label
    # Summary will be populated in a separate step

    # Check no themes for question with no free text
    themes_for_q = models.Theme.objects.filter(answer__question=no_free_text_question)
    assert not themes_for_q.exists()
