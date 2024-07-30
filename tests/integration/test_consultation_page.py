import pytest
from freezegun import freeze_time

from consultation_analyser.factories import (
    ConsultationWithAnswersFactory,
    ProcessingRunFactory,
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


@pytest.mark.django_db
def test_consultation_page_multiple_runs(django_app):
    user = UserFactory()
    consultation = ConsultationWithAnswersFactory(users=(user))
    freezer = freeze_time("2023-01-01 12:30:10")
    freezer.start()
    processing_run_1 = ProcessingRunFactory(consultation=consultation)
    freezer.stop()
    freezer = freeze_time("2024-03-02 11:00:03")
    freezer.start()
    ProcessingRunFactory(consultation=consultation)
    freezer.stop()
    sign_in(django_app, user.email)

    consultation_slug = consultation.slug
    homepage_default = django_app.get(f"/consultations/{consultation_slug}/")
    assert "Themes generated at" in homepage_default.text
    assert "1 January 2023 at 12:30" in homepage_default.text
    homepage_first_run = django_app.get(
        f"/consultations/{consultation_slug}/?run={processing_run_1.id}"
    )
    assert "2 March 2024 at 11:00" in homepage_first_run.text
