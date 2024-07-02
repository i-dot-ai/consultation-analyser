import string

import pytest
import tiktoken

from consultation_analyser.factories import (
    AnswerFactory,
    ConsultationFactory,
    ConsultationResponseFactory,
    ProcessingRunFactory,
    QuestionFactory,
    SectionFactory,
    ThemeFactory,
    TopicModelMetadataFactory,
)
from consultation_analyser.pipeline.backends.langchain_llm_backend import (
    get_random_sample_of_responses_for_theme,
)


@pytest.mark.django_db
def test_get_random_sample_of_responses_for_theme():
    encoding = tiktoken.get_encoding("cl100k_base")  # Use arbitrary encoding model
    consultation = ConsultationFactory()
    consultation_response = ConsultationResponseFactory(consultation=consultation)
    section = SectionFactory(consultation=consultation)
    question = QuestionFactory(has_free_text=True, section=section)
    processing_run = ProcessingRunFactory(consultation=consultation)
    theme = ThemeFactory(processing_run=processing_run)
    text = "Here are my strong opinions on chocolate. I love KitKats."  # 14 tokens
    answer = AnswerFactory(
        question=question, free_text=text, consultation_response=consultation_response
    )
    answer.themes.add(theme)
    combined_responses = get_random_sample_of_responses_for_theme(
        theme, encoding=encoding, max_tokens=40
    )
    assert combined_responses.strip() == text

    # Now test that we combine multiple responses but don't exceed limit.
    for i in range(3):
        answer = AnswerFactory(
            question=question,
            free_text=text,
            consultation_response=consultation_response,
        )
        answer.themes.add(theme)
    combined_responses = get_random_sample_of_responses_for_theme(
        theme, encoding=encoding, max_tokens=40
    )
    assert len(encoding.encode(combined_responses)) < 30, combined_responses
    assert combined_responses.count(text) > 1, combined_responses


@pytest.mark.django_db
def test_get_random_sample_of_responses_for_theme_does_not_repeat():
    encoding = tiktoken.get_encoding("cl100k_base")  # Use arbitrary encoding model
    consultation = ConsultationFactory()
    consultation_response = ConsultationResponseFactory(consultation=consultation)
    section = SectionFactory(consultation=consultation)
    question = QuestionFactory(has_free_text=True, section=section)
    processing_run = ProcessingRunFactory(consultation=consultation)
    topic_model_meta = TopicModelMetadataFactory()
    theme = ThemeFactory(processing_run=processing_run, topic_model_metadata=topic_model_meta)

    answers = list(string.ascii_lowercase)  # get 27 distinct answers
    for a in answers:
        answer = AnswerFactory(
            question=question, free_text=a, consultation_response=consultation_response
        )
        answer.themes.add(theme)

    combined_responses = get_random_sample_of_responses_for_theme(
        theme, encoding=encoding, max_tokens=100
    )

    selected_answers = "".join(combined_responses.splitlines())
    assert len(selected_answers) == len(set(selected_answers))
