import pytest
import pandas as pd

from consultation_analyser.consultations.ml_pipeline import (
    save_themes_for_consultation,
    get_or_create_theme_for_question,
    save_themes_for_question,
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


@pytest.mark.django_db
def test_get_or_create_theme_for_question():
    question = factories.QuestionFactory(has_free_text=True)
    factories.AnswerFactory(question=question, theme=None)
    keywords = ["key", "lock"]
    label = "0_key_lock"
    # Check theme created
    theme = get_or_create_theme_for_question(question, keywords=keywords, label=label)
    themes_qs = models.Theme.objects.filter(keywords=keywords, label=label)
    assert themes_qs.count() == 1
    assert theme.keywords == keywords
    assert theme.label == label
    # Check no duplicate created
    get_or_create_theme_for_question(question, keywords=keywords, label=label)
    themes_qs = models.Theme.objects.filter(keywords=keywords, label=label)
    assert themes_qs.count() == 1


@pytest.mark.django_db
def test_save_themes_for_question():
    question = factories.QuestionFactory()
    answer1 = factories.AnswerFactory(question=question)
    answer2 = factories.AnswerFactory(question=question)
    answer3 = factories.AnswerFactory(question=question)
    df = pd.DataFrame(
        {
            "id": [answer1.id, answer2.id, answer3.id],
            "Topic": [-1, 0, 0],
            "Name": ["-1_x_y", "0_m_n", "0_m_n"],
            "Representation": [["x", "y"], ["m", "n"], ["m", "n"]],
        }
    )
    save_themes_for_question(df)
    assert answer1.theme.label == "-1_x_y"
    assert answer2.theme.keywords == ["m", "n"]
    themes_for_question = models.Theme.objects.filter(answer__question=question)
    assert themes_for_question.count() == 2
