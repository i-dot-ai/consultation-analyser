import re

import pytest
from freezegun import freeze_time

from consultation_analyser.factories import (
    ConsultationBuilder,
    ConsultationWithAnswersFactory,
    ProcessingRunFactory,
    UserFactory,
)
from tests.helpers import sign_in


@pytest.mark.django_db
def test_get_question_summary_page(django_app):
    user = UserFactory()
    consultation_builder = ConsultationBuilder(user=(user))
    consultation = consultation_builder.consultation
    question = consultation_builder.add_question(
        multiple_choice_questions=[("Do you agree?", ["Yes", "No", "Maybe"])]
    )
    theme = consultation_builder.add_theme(topic_id=1)  # prevent outlier

    for a in [
        [("Do you agree?", ["Yes"])],
        [("Do you agree?", ["No"])],
        [("Do you agree?", ["No"])],
        [("Do you agree?", ["Maybe"])],
    ]:
        answer = consultation_builder.add_answer(question, multiple_choice_answers=a)
        answer.themes.add(theme)

    sign_in(django_app, user.email)

    question_summary_url = f"/consultations/{consultation.slug}/sections/{question.section.slug}/questions/{question.slug}/"

    question_page = django_app.get(question_summary_url)

    assert question.text in question_page
    assert theme.short_description in question_page

    for item in question.multiple_choice_options:
        for opt in item["options"]:
            assert opt in question_page

    for keyword in theme.topic_keywords:
        assert keyword in question_page

    assert re.search(r"Yes\s+1\s+25%", question_page.html.text)
    assert re.search(r"No\s+2\s+50%", question_page.html.text)
    assert re.search(r"Maybe\s+1\s+25%", question_page.html.text)


@pytest.mark.django_db
def test_consultation_page_multiple_runs(django_app):
    user = UserFactory()
    consultation = ConsultationWithAnswersFactory(users=(user))
    section = consultation.section_set.first()
    question = section.question_set.first()
    freezer = freeze_time("2023-01-01 12:30:10")
    freezer.start()
    processing_run_1 = ProcessingRunFactory(consultation=consultation)
    freezer.stop()

    # Now generate another processing run
    freezer = freeze_time("2024-03-02 11:00:03")
    freezer.start()
    ProcessingRunFactory(consultation=consultation)
    freezer.stop()

    sign_in(django_app, user.email)

    consultation_slug = consultation.slug
    homepage_default = django_app.get(
        f"/consultations/{consultation_slug}/sections/{section.slug}/questions/{question.slug}/"
    )  # latest run
    assert "Themes generated at" in homepage_default.text
    assert "2 March 2024 at 11:00" in homepage_default.text

    response = django_app.get(
        f"/consultations/{consultation_slug}/sections/{section.slug}/questions/{question.slug}/?run={processing_run_1.id}",
    )
    assert response.status_code == 302
    assert processing_run_1.slug in str(response.url)  # redirect to the correct processing run
    new_page = response.follow()
    assert "1 January 2023 at 12:30" in new_page.text
