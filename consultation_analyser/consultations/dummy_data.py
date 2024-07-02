import datetime
import random

from consultation_analyser.factories import (
    AnswerFactory,
    ConsultationFactory,
    ConsultationResponseFactory,
    FakeConsultationData,
    ProcessingRunFactory,
    QuestionFactory,
    SectionFactory,
    ThemeFactory,
    TopicModelMetadataFactory,
)
from consultation_analyser.hosting_environment import HostingEnvironment


def create_dummy_data(responses=10, include_themes=True, number_questions=10, **options):
    if number_questions > 10:
        raise RuntimeError("You can't have more than 10 questions")
    if HostingEnvironment.is_production():
        raise RuntimeError("Dummy data generation should not be run in production")

    # Timestamp to avoid duplicates - set these as default options
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if "name" not in options:
        options["name"] = f"Dummy consultation generated at {timestamp}"
    if "slug" not in options:
        options["slug"] = f"consultation-slug-{timestamp}"

    consultation = ConsultationFactory(**options)
    section = SectionFactory(name="Base section", consultation=consultation)
    fake_consultation_data = FakeConsultationData()
    all_questions = fake_consultation_data.all_questions()
    questions_to_include = all_questions[:number_questions]

    questions = [
        QuestionFactory(
            text=q["text"],
            slug=q["slug"],
            multiple_choice_questions=[
                (x["question_text"], x["options"]) for x in (q.get("multiple_choice") or [])
            ],
            has_free_text=q["has_free_text"],
            section=section,
        )
        for q in questions_to_include
    ]
    for r in range(responses):
        response = ConsultationResponseFactory(consultation=consultation)
        answers = []
        for q in questions:
            if q.has_free_text:
                free_text_answer = fake_consultation_data.get_free_text_answer(q.slug)
                answers.append(
                    AnswerFactory(
                        question=q,
                        consultation_response=response,
                        free_text=free_text_answer,
                    )
                )
                # Force some answers to have no free text response
                if random.randrange(1, 4) == 1:
                    ans = AnswerFactory(
                        question=q,
                        consultation_response=response,
                        free_text="",
                    )
                    ans.themes.clear()
                    answers.append(ans)
            else:
                ans = AnswerFactory(question=q, consultation_response=response)
                ans.themes.clear()
                answers.append(ans)

        if include_themes:
            # Set themes per question, multiple answers with the same theme
            processing_run = ProcessingRunFactory(consultation=consultation)
            for q in questions:
                tm = TopicModelMetadataFactory()
                themes = [
                    ThemeFactory(topic_model_metadata=tm, topic_id=i, processing_run=processing_run)
                    for i in range(-1, 4)
                ]
                for a in answers[1:]:
                    random_theme = random.choice(themes)
                    a.themes.add(random_theme)
                    a.save()
            # Force at least one answer to be an outlier
            answers[0].themes.add(themes[0])
            answers[0].save()
    return consultation
