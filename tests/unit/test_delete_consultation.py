import pytest

from consultation_analyser.consultations import models
from consultation_analyser.factories import (
    AnswerFactory,
    ConsultationResponseFactory,
    ProcessingRunFactory,
    QuestionFactory,
    ThemeFactory,
)


@pytest.mark.django_db
def test_delete_consultation():
    question = QuestionFactory()
    consultation = question.section.consultation
    consultation_response = ConsultationResponseFactory(consultation=consultation)
    answer = AnswerFactory(question=question, consultation_response=consultation_response)
    processing_run = ProcessingRunFactory(consultation=consultation)
    theme = ThemeFactory(processing_run=processing_run)
    answer.themes.add(theme)

    assert models.Consultation.objects.count() == 1
    assert models.ConsultationResponse.objects.count() == 1
    assert models.Section.objects.count() == 1
    assert models.Question.objects.count() == 1
    assert models.Answer.objects.count() == 1
    assert models.Theme.objects.count() == 1

    consultation.delete()

    assert models.Consultation.objects.count() == 0
    assert models.ConsultationResponse.objects.count() == 0
    assert models.Section.objects.count() == 0
    assert models.Question.objects.count() == 0
    assert models.Answer.objects.count() == 0
    assert models.Theme.objects.count() == 0
