"""
For now, dummy code to test consultation flow.
"""

import datetime
import random

from . import models


def save_themes_for_question(question: models.Question) -> None:
    # TODO - this is dummy code to be replaced
    # This generates junk themes for us to test things
    answers_qs = models.Answer.objects.filter(question=question)
    made_up_themes = []
    for i in range(3):
        label = f"Theme {i}: {question.slug} : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        words = question.text.split()
        keywords = [random.choice(words), random.choice(words)]
        theme = models.Theme(keywords=keywords, label=label)
        theme.save()
        made_up_themes.append(theme)
    for answer in answers_qs:
        answer.theme = random.choice(made_up_themes)
        answer.save()


def save_themes_for_consultation(consultation_slug: str) -> None:
    # Only add themes for questions with free text responses.
    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug, has_free_text=True)
    for question in questions:
        save_themes_for_question(question)


def get_summary_for_theme(theme: models.Theme) -> str:
    # TODO - replace this dummy code with LLM calls
    summary = f"summary: {theme.keywords.join(",")}"
    return summary


def save_theme_summaries_for_question(question: models.Question) -> None:
    # TODO: replace with non-dummy code!
    themes_qs = models.Theme.objects.filter(answer__question=question)
    for theme in themes_qs:
        summary = get_summary_for_theme(theme)
        theme.summary = summary
        theme.save()


def save_theme_summaries_for_consultation(consultation_slug: str) -> None:
    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug, has_free_text=True)
    for question in questions:
        save_theme_summaries_for_question(question)
