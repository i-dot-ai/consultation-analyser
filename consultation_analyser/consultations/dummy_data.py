from consultation_analyser.hosting_environment import HostingEnvironment
from tests.factories import (
    FakeConsultationData,
    QuestionFactory,
    ConsultationFactory,
    SectionFactory,
    AnswerFactory,
    ConsultationResponseFactory,
    ThemeFactory,
)
import random


class DummyConsultation:
    def __init__(self, responses=10, blank_themes=False, **options):
        if not HostingEnvironment.is_local():
            raise RuntimeError("Dummy data generation should only be run in development")

        consultation = ConsultationFactory(**options)
        section = SectionFactory(name="Base section", consultation=consultation)
        questions = [QuestionFactory(question=q, section=section) for q in FakeConsultationData().all_questions()]
        for r in range(responses):
            response = ConsultationResponseFactory(consultation=consultation)
            if blank_themes:
                _answers = [AnswerFactory(question=q, consultation_response=response, theme=None) for q in questions]

            else:
                _answers = [AnswerFactory(question=q, consultation_response=response) for q in questions]

                # Set themes per question, multiple answers with the same theme
                for q in questions:
                    themes = [ThemeFactory() for _ in range(2, 6)]
                    for a in _answers:
                        random_theme = random.choice(themes)
                        a.theme = random_theme
                        a.save()
