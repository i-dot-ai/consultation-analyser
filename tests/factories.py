import factory
import yaml
import random
from consultation_analyser.consultations import models

import faker as _faker

faker = _faker.Faker()

default_multiple_choice_options = ["Yes", "No", "Not sure"]


class FakeConsultationData:
    def __init__(self):
        with open("./tests/examples/questions.yml", "r") as f:
            questions = yaml.safe_load(f)
            slugs = [q["slug"] for q in questions]
            self.questions = dict(zip(slugs, questions))

    def question(self):
        return random.choice(list(self.questions.values()))

    def get_free_text_answer(self, slug):
        q = self.questions[slug]
        return random.choice(q["answers"])

    def get_multiple_choice_answer(self, slug):
        q = self.questions[slug]
        return random.choice(q["multiple_choice_options"])

    def all_questions(self):
        return list(self.questions.values())


class ConsultationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Consultation
        skip_postgeneration_save = True

    name = faker.sentence()
    slug = faker.slug()

    @factory.post_generation
    def with_question(consultation, creation_strategy, value, **kwargs):
        if value is True:
            SectionFactory(
                consultation=consultation,
                with_question=True,
                with_question__with_answer=kwargs.get("with_answer"),
                with_question__with_multiple_choice=kwargs.get("with_multiple_choice"),
            )


class SectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Section
        skip_postgeneration_save = True

    name = faker.sentence()
    slug = faker.slug()
    consultation = factory.SubFactory("tests.factories.ConsultationFactory")

    class Params:
        with_questions = factory.Trait(questions=[factory.SubFactory("tests.factories.QuestionFactory")])

    @factory.post_generation
    def with_question(section, creation_strategy, value, **kwargs):
        if value is True:
            QuestionFactory(
                section=section,
                with_answer=kwargs.get("with_answer"),
                with_multiple_choice=kwargs.get("with_multiple_choice"),
            )


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Question
        skip_postgeneration_save = False

    text = factory.LazyAttribute(lambda o: o.question["text"])
    slug = factory.LazyAttribute(lambda o: o.question["slug"])
    multiple_choice_options = factory.LazyAttribute(lambda o: o.question["multiple_choice_options"])
    has_free_text = factory.LazyAttribute(lambda o: o.question["has_free_text"])
    section = factory.SubFactory(SectionFactory)

    class Params:
        question = FakeConsultationData().question()

    @factory.post_generation
    def with_answer(question, creation_strategy, value, **kwargs):
        if value is True:
            AnswerFactory(question=question, with_multiple_choice=kwargs.get("with_multiple_choice"))

    @factory.post_generation
    def with_multiple_choice(question, creation_strategy, value, **kwargs):
        if value is True and question.multiple_choice_options is None:
            question.multiple_choice_options = default_multiple_choice_options


class ConsultationResponseFactory(factory.django.DjangoModelFactory):
    consultation = factory.SubFactory(ConsultationFactory)

    class Meta:
        model = models.ConsultationResponse


class ThemeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Theme

    # TODO - may need to be changed once ML pipeline is in
    label = faker.sentence()
    summary = f"Summary: {label}"
    keywords = label.lower().strip(".").split(" ")


class AnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Answer

    multiple_choice_responses = factory.LazyAttribute(
        lambda o: FakeConsultationData().get_multiple_choice_answer(o.question.slug)
        if o.question.multiple_choice_options
        else None
    )

    free_text = factory.LazyAttribute(
        lambda o: FakeConsultationData().get_free_text_answer(o.question.slug) if o.question.has_free_text else None
    )

    question = factory.SubFactory(QuestionFactory)
    consultation_response = factory.SubFactory(ConsultationResponseFactory)
    theme = factory.SubFactory(ThemeFactory)

    @factory.post_generation
    def with_multiple_choice(answer, creation_strategy, value, **kwargs):
        if answer.multiple_choice_responses is None:
            answer.multiple_choice_responses = random.choice(default_multiple_choice_options)
