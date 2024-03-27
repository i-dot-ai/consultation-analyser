import pytest
import pandas as pd

from consultation_analyser.consultations import models

from tests import factories


@pytest.mark.django_db
def test_get_or_create_theme_for_question():
    question = factories.QuestionFactory(has_free_text=True)
    factories.AnswerFactory(question=question, theme=None)
    keywords = ["key", "lock"]
    label = "0_key_lock"
    # Check theme created
    theme, created = models.Theme.objects.get_or_create(question=question, keywords=keywords, label=label)
    themes_qs = models.Theme.objects.filter(keywords=keywords, label=label)
    assert themes_qs.count() == 1
    assert theme.keywords == keywords
    assert theme.label == label
    assert created
    # Check no duplicate created
    theme, created = models.Theme.objects.get_or_create(question=question, keywords=keywords, label=label)
    themes_qs = models.Theme.objects.filter(keywords=keywords, label=label)
    assert themes_qs.count() == 1


@pytest.mark.django_db
def test_save_themes_to_answers():
    question = factories.QuestionFactory()
    answer1 = factories.AnswerFactory(question=question, theme=None)
    answer2 = factories.AnswerFactory(question=question, theme=None)
    answer3 = factories.AnswerFactory(question=question, theme=None)
    df = pd.DataFrame(
        {
            "id": [answer1.id, answer2.id, answer3.id],
            "Topic": [-1, 0, 0],
            "Name": ["-1_x_y", "0_m_n", "0_m_n"],
            "Representation": [["x", "y"], ["m", "n"], ["m", "n"]],
        }
    )
    assert answer1.theme.label == "-1_x_y"
    assert answer2.theme.keywords == ["m", "n"]
    themes_for_question = models.Theme.objects.filter(answer__question=question)
    assert themes_for_question.count() == 2
