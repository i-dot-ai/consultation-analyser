import uuid
from dataclasses import dataclass

import pydantic
from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.db import models

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import public_schema


class MultipleChoiceSchemaValidator(BaseValidator):
    def compare(self, value, _limit_value):
        if not value:
            return
        try:
            public_schema.MultipleChoice(value)
        except pydantic.ValidationError as e:
            raise ValidationError(e.json())


class UUIDPrimaryKeyModel(models.Model):
    class Meta:
        abstract = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    modified_at = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        abstract = True
        ordering = ["created_at"]


class Consultation(UUIDPrimaryKeyModel, TimeStampedModel):
    name = models.CharField(max_length=256)
    slug = models.CharField(null=False, max_length=256)
    users = models.ManyToManyField(User)

    def has_processing_run(self):
        return ProcessingRun.objects.filter(consultation=self).exists()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["slug"], name="unique_consultation_slug"),
        ]

    def delete(self, *args, **kwargs):
        """
        Delete Related theme objects that can become orphans
        because deletes will not cascade from Answer because
        the Theme in question could still be associated with
        another Answer
        """
        Theme.objects.filter(answer__question__section__consultation=self).delete()

        super().delete(*args, **kwargs)

    @property
    def latest_processing_run(self):
        processing_runs = ProcessingRun.objects.filter(consultation=self).order_by("created_at")
        latest = processing_runs.last() if processing_runs else None
        return latest


class Section(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    name = models.TextField()
    slug = models.CharField(null=False, max_length=256)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "consultation"], name="unique_section_consultation"
            ),
        ]


class Question(UUIDPrimaryKeyModel, TimeStampedModel):
    text = models.CharField(
        null=False, max_length=None
    )  # no idea what's a sensible value for max_length
    slug = models.CharField(null=False, max_length=256)
    has_free_text = models.BooleanField(default=False)
    multiple_choice_options = models.JSONField(
        null=True, blank=True, validators=[MultipleChoiceSchemaValidator(limit_value=None)]
    )
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    @dataclass
    class MultipleChoiceResponseCount:
        answer: str
        count: int
        percent: float

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=["slug", "section"], name="unique_question_section"),
        ]


class ConsultationResponse(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(editable=False, null=False)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


class ProcessingRun(UUIDPrimaryKeyModel, TimeStampedModel):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    # TODO - add more processing run metadata

    @property
    def themes(self):
        return Theme.objects.filter(processing_run=self).distinct()

    def get_themes_for_answer(self, answer_id):
        # At the moment, at most one theme per answer and run but
        # likely to change in future.
        return self.themes.filter(answer__id=answer_id)

    def get_themes_for_question(self, question_id):
        return self.themes.filter(processing_run=self, answer__question_id=question_id).distinct()

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


class TopicModelMetadata(UUIDPrimaryKeyModel, TimeStampedModel):
    # TODO -  Some other metadata on the model TBC and link to saved model

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass


class Theme(UUIDPrimaryKeyModel, TimeStampedModel):
    processing_run = models.ForeignKey(ProcessingRun, on_delete=models.CASCADE, null=True)
    # Topic model, keywords and ID come from BERTopic
    topic_model_metadata = models.ForeignKey(
        TopicModelMetadata, on_delete=models.CASCADE, null=True
    )
    topic_keywords = models.JSONField(default=list)
    topic_id = models.IntegerField(null=True)  # Topic ID from BERTopic
    is_outlier = models.GeneratedField(
        expression=models.Q(topic_id=-1), output_field=models.BooleanField(), db_persist=True
    )
    # LLM generates short_description and summary
    short_description = models.TextField(blank=True)
    summary = models.TextField(blank=True)  # More detailed description

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["topic_id", "topic_model_metadata"], name="unique_id_per_model"
            ),
        ]


class AnswerQuerySet(models.QuerySet):
    MULTIPLE_CHOICE_QUERY = """
        EXISTS (
            SELECT 1
            FROM jsonb_array_elements(multiple_choice) AS elem,
                 jsonb_array_elements_text(elem -> 'options') AS opt
            WHERE elem ->> 'question_text' = %s
              AND opt = %s
        )
    """

    def filter_multiple_choice(self, question, answer):
        return self.extra(where=[self.MULTIPLE_CHOICE_QUERY], params=[question, answer])  # nosec


class Answer(UUIDPrimaryKeyModel, TimeStampedModel):
    objects = AnswerQuerySet.as_manager()

    multiple_choice = models.JSONField(
        null=True, blank=True, validators=[MultipleChoiceSchemaValidator(limit_value=None)]
    )
    free_text = models.TextField(null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    consultation_response = models.ForeignKey(ConsultationResponse, on_delete=models.CASCADE)
    themes = models.ManyToManyField(Theme)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        pass

    def save_theme_to_answer(
        self,
        topic_keywords: list,
        topic_id: int,
        processing_run: ProcessingRun,
        topic_model_metadata: TopicModelMetadata,
    ):
        theme, _ = Theme.objects.get_or_create(
            topic_keywords=topic_keywords,
            topic_id=topic_id,
            processing_run=processing_run,
            topic_model_metadata=topic_model_metadata,
        )
        self.themes.add(theme)
        self.save()
