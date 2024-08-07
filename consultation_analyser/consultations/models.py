import itertools
import uuid
from dataclasses import dataclass

import faker as _faker
import pydantic
from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.db import connection, models

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import public_schema

faker = _faker.Faker()


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

    def get_processing_run(self, processing_run_slug=None):
        # If None, get latest run if exists
        if processing_run_slug:
            processing_run = ProcessingRun.objects.get(consultation=self, slug=processing_run_slug)
        else:
            processing_run = self.latest_processing_run
        return processing_run


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


class MultipleChoiceNotProportionalError(Exception):
    pass


@dataclass
class MultipleChoiceQuestionStats:
    question: str
    counts: dict[str, int]
    total_responses: int
    has_multiple_selections: bool

    def percentages(self):
        if self.has_multiple_selections:
            raise MultipleChoiceNotProportionalError(
                "It does not make sense to calculate percentages for a multiple choice question supporting multiple selections"
            )
        else:
            return {
                option: round((float(count) / self.total_responses) * 100)
                for option, count in self.counts.items()
            }


class Question(UUIDPrimaryKeyModel, TimeStampedModel):
    MULTIPLE_CHOICE_COUNTS_QUERY = """
        SELECT question_id as id, elem ->> 'question_text' as question, option, COUNT(*) as count
        FROM    consultations_answer,
                jsonb_array_elements(multiple_choice) AS elem,
                jsonb_array_elements_text(elem -> 'options') AS option
        WHERE question_id = %s
        GROUP BY question_id, option, question
        ORDER BY question, option ASC
    """

    # until we explicitly annotate these questions, use the presence
    # of multiple selections to infer whether they're supported
    HAS_MULTIPLE_SELECTIONS_QUERY = """
        SELECT EXISTS (
            SELECT 1
            FROM consultations_answer,
                 jsonb_array_elements(multiple_choice) AS elem
            WHERE question_id = %s
            AND elem ->> 'question_text' = %s
            AND jsonb_array_length(elem -> 'options') > 1
        ) AS has_multiple_selections;
    """

    def multiple_choice_stats(self) -> list[MultipleChoiceQuestionStats]:
        counts = type(self).objects.raw(self.MULTIPLE_CHOICE_COUNTS_QUERY, params=[str(self.id)])

        values = [
            {"question": count.question, "option": count.option, "count": count.count}
            for count in counts
        ]

        output = []
        for q, stats in itertools.groupby(values, lambda group: group["question"]):
            statsl = list(stats)  # necessary as we need to iterate over this generator twice

            counts = {opt["option"]: opt["count"] for opt in statsl}
            total_responses = sum(counts.values())

            with connection.cursor() as cursor:
                # it's a bit inefficient to do another query here but I've preferred
                # two small simple queries over one big complicated query
                cursor.execute(self.HAS_MULTIPLE_SELECTIONS_QUERY, [str(self.id), q])
                has_multiple_selections = cursor.fetchone()[0]

            output.append(
                MultipleChoiceQuestionStats(
                    question=q,
                    counts=counts,
                    total_responses=total_responses,
                    has_multiple_selections=has_multiple_selections,
                )
            )

        return output

    text = models.CharField(
        null=False, max_length=None
    )  # no idea what's a sensible value for max_length
    slug = models.CharField(null=False, max_length=None)
    has_free_text = models.BooleanField(default=False)
    multiple_choice_options = models.JSONField(
        null=True, blank=True, validators=[MultipleChoiceSchemaValidator(limit_value=None)]
    )
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

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
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    slug = models.SlugField(null=True)

    @property
    def themes(self):
        return Theme.objects.filter(processing_run=self).distinct()

    @property
    def topic_model_metadatas(self):
        topic_model_meta_ids = self.themes.values_list("topic_model_metadata", flat=True)
        return TopicModelMetadata.objects.filter(id__in=topic_model_meta_ids).distinct()

    def get_themes_for_answer(self, answer_id):
        # At the moment, at most one theme per answer and run but
        # likely to change in future.
        return self.themes.filter(answer__id=answer_id)

    def get_themes_for_question(self, question_id):
        return self.themes.filter(processing_run=self, answer__question_id=question_id).distinct()

    def save(self, *args, **kwargs):
        if not self.slug:
            generated_slug = faker.slug()
            while ProcessingRun.objects.filter(
                slug=generated_slug, consultation=self.consultation
            ).exists():
                generated_slug = faker.slug()
            self.slug = generated_slug
        super(ProcessingRun, self).save(*args, **kwargs)

    class Meta(UUIDPrimaryKeyModel.Meta, TimeStampedModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "consultation"], name="unique_slug_consultation"
            ),
        ]


class TopicModelMetadata(UUIDPrimaryKeyModel, TimeStampedModel):
    scatter_plot_data = models.JSONField(default=dict)

    def add_llm_summarisation_detail(self):
        """
        Appends extra data from LLM summarisation onto the scatter plot data.
        """
        if "data" not in self.scatter_plot_data:
            return

        data = self.scatter_plot_data["data"]
        related_themes_qs = Theme.objects.filter(topic_model_metadata=self).distinct()
        updated_data = []
        for coordinate in data:
            topic_id = coordinate["topic_id"]
            try:
                theme = related_themes_qs.get(topic_id=topic_id)
            except Theme.DoesNotExist:
                theme = None
            if theme:
                updated_coordinate = coordinate
                updated_coordinate["short_description"] = theme.short_description
                updated_coordinate["summary"] = theme.summary
                updated_data.append(updated_coordinate)

        self.scatter_plot_data = {"data": updated_data}
        self.save()
        return

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
    multiple_choice = models.JSONField(
        null=True, blank=True, validators=[MultipleChoiceSchemaValidator(limit_value=None)]
    )

    objects = AnswerQuerySet.as_manager()

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
