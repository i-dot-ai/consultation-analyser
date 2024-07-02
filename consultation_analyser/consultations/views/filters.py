from django.db.models import Count, QuerySet
from django.http import HttpRequest

from .. import models


def get_applied_filters(request: HttpRequest) -> dict[str, str]:
    return {
        "keyword": request.GET.get("keyword", ""),
        "theme": request.GET.get("theme", "All"),
    }


# TODO: rename this to Answers
def get_filtered_responses(question: models.Question, applied_filters: dict[str, str]) -> QuerySet:
    queryset = models.Answer.objects.filter(question=question)
    if (
        applied_filters["keyword"]
        and applied_filters["keyword"] != "All"
        and applied_filters["keyword"] != ""
    ):
        queryset = queryset.filter(free_text__contains=applied_filters["keyword"])
    if applied_filters["theme"] != "All":
        queryset = queryset.filter(themes=applied_filters["theme"])
    return queryset


def get_filtered_themes(
    question: models.Question, applied_filters: dict[str, str], processing_run: models.ProcessingRun
) -> QuerySet:
    if processing_run:
        queryset = processing_run.get_themes_for_question(question_id=question.id)
    else:
        queryset = models.Theme.objects.none()
    queryset = queryset.annotate(answer_count=Count("answer"))
    if applied_filters["theme"] != "All":
        queryset = queryset.filter(id=applied_filters["theme"])
    return queryset
