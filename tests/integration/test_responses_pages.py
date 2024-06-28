import html

import pytest

from consultation_analyser.factories import (
    AnswerFactory,
    ConsultationFactory,
    ConsultationResponseFactory,
    UserFactory,
)
from tests.helpers import sign_in


@pytest.mark.django_db
def test_get_question_responses_page(django_app):
    user = UserFactory(email="email@example.com")
    sign_in(django_app, "email@example.com")

    consultation = ConsultationFactory(
        user=user,
        with_question=True,
        with_question__with_multiple_choice=True,
        with_question__with_free_text=True,
    )

    consultation_response = ConsultationResponseFactory(consultation=consultation)

    section = consultation.section_set.first()
    question = section.question_set.first()

    answer = AnswerFactory(question=question, consultation_response=consultation_response)
    multiple_choice = answer.multiple_choice[0]

    question_responses_url = (
        f"/consultations/{consultation.slug}/sections/{section.slug}/responses/{question.slug}/"
    )
    responses_page = django_app.get(question_responses_url)
    page_content = html.unescape(str(responses_page.content))

    assert "Responses" in page_content
    assert f"{question.text}" in page_content

    # Check responses appear
    assert f"{answer.free_text}" in page_content
    assert (
        f"{multiple_choice["question_text"]}"
        in page_content
    )
    assert (
        f"{multiple_choice["options"][0]}"
        in page_content
    )
    if answer.free_text:
        assert f"{answer.theme.short_description}" in page_content

    # Check keyword filtering
    first_word_of_answer = answer.free_text.split()[0]
    keywords = ["ThisWordWontAppear", first_word_of_answer]
    for keyword in keywords:
        responses_page = django_app.get(f"{question_responses_url}?keyword={keyword}")
        page_content = html.unescape(str(responses_page.content))
        assert keyword in page_content
        if keyword == "ThisWordWontAppear":
            assert "Showing <strong>0</strong> of <strong>1</strong> reponses"
