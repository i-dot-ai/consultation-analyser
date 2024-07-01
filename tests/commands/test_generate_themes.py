import json

import pytest
from django.conf import settings
from django.core.management import call_command

from consultation_analyser.consultations.models import Question, Theme
from consultation_analyser.consultations.public_schema import ConsultationWithResponsesAndThemes
from consultation_analyser.factories import (
    AnswerFactory,
    ConsultationFactory,
    ConsultationResponseFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_generate_themes(tmp_path):
    UserFactory(email="email@example.com")

    file_path = settings.BASE_DIR / "tests" / "examples" / "chocolate.json"

    call_command(
        "generate_themes", input_file=file_path, embedding_model="fake", output_dir=tmp_path
    )

    json_with_themes_path = tmp_path / "consultation_with_themes.json"

    with_themes = json.loads(open(json_with_themes_path).read())

    # Bail if it's invalid
    ConsultationWithResponsesAndThemes(**with_themes)


@pytest.mark.django_db
def test_generate_themes_clean(tmp_path):
    UserFactory(email="email@example.com")

    file_path = settings.BASE_DIR / "tests" / "examples" / "chocolate.json"

    # should not throw
    call_command(
        "generate_themes",
        input_file=file_path,
        embedding_model="fake",
        clean=True,
        output_dir=tmp_path,
    )

    # we're OK if we make it this far
    assert True


@pytest.mark.django_db
def test_generate_themes_with_consultation_slug(tmp_path):
    UserFactory(email="email@example.com")
    file_path = settings.BASE_DIR / "tests" / "examples" / "chocolate.json"

    consultation = ConsultationFactory(slug="test-slug", with_question=True)
    response = ConsultationResponseFactory(consultation=consultation)
    AnswerFactory(consultation_response=response, question=Question.objects.first(), theme=None)

    assert Theme.objects.count() == 0

    with pytest.raises(Exception, match="specify either --input_file or --consultation_slug"):
        call_command(
            "generate_themes",
            consultation_slug="test-slug",
            input_file=file_path,
            embedding_model="fake",
            clean=True,
            output_dir=tmp_path,
        )

    with pytest.raises(Exception, match="specify either --input_file or --consultation_slug"):
        call_command("generate_themes", embedding_model="fake", clean=True, output_dir=tmp_path)

    call_command(
        "generate_themes",
        consultation_slug="test-slug",
        embedding_model="fake",
        clean=True,
        output_dir=tmp_path,
    )

    assert Theme.objects.count() == 1
