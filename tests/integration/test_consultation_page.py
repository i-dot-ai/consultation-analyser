import pytest

from consultation_analyser.factories import (
    ConsultationWithAnswersFactory,
    UserFactory,
)
from tests.helpers import sign_in


@pytest.mark.django_db
def test_consultation_page(django_app):
    user = UserFactory()
    consultation = ConsultationWithAnswersFactory(users=(user))

    sign_in(django_app, user.email)

    consultation_slug = consultation.slug
    question = consultation.section_set.first().question_set.first()
    homepage = django_app.get(f"/consultations/{consultation_slug}/")
    assert "Themes generated at" not in homepage.text  # No themes yet
    question_page = homepage.click("Question summary")

    assert "Question summary" in question_page
    assert f"{question.text}" in question_page
