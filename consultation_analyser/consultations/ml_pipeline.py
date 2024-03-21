from uuid import UUID
from typing import List, NamedTuple

from umap.umap_ import UMAP
from sentence_transformers import SentenceTransformer
from hdbscan import HDBSCAN
from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from django.db.models import QuerySet
import pandas as pd

from consultation_analyser.consultations import models


def get_embeddings_for_question(
    free_text_responses: List, embedding_model_name: str = "thenlper/gte-small"
) -> np.ndarray:
    embedding_model = SentenceTransformer(embedding_model_name)
    embeddings = embedding_model.encode(free_text_responses)
    return embeddings


def get_topic_model(free_text_responses_list: List, embeddings: np.ndarray) -> BERTopic:
    umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=12)
    hdbscan_model = HDBSCAN(
        min_cluster_size=3, metric="euclidean", cluster_selection_method="eom", prediction_data=True
    )
    vectorizer_model = CountVectorizer(stop_words="english")
    ctfidf_model = ClassTfidfTransformer()
    topic_model = BERTopic(
        umap_model=umap_model, hdbscan_model=hdbscan_model, vectorizer_model=vectorizer_model, ctfidf_model=ctfidf_model
    )
    topic_model.fit_transform(free_text_responses_list, embeddings=embeddings)
    return topic_model


def get_answers_and_topics(topic_model: BERTopic, answers_qs: QuerySet) -> pd.DataFrame:
    # Answers/IDs need to be in the same order - answers_qs has been sorted
    free_text_responses = list(answers_qs.values_list("free_text", flat=True))
    answers_id_list = answers_qs.values_list("id", flat=True)
    # Assign topics to answers
    answers_df = topic_model.get_document_info(free_text_responses)
    answers_df["id"] = answers_id_list
    answers_df = answers_df[["id", "Topic", "Name", "Representation"]]
    return answers_df


def get_or_create_theme_for_question(question: models.Question, label: str, keywords: str) -> models.Theme:
    # Themes should be unique up to question and label (and keywords)
    # TODO - how can we enforce this?
    # TODO - This isn't working
    try:
        theme = models.Theme.objects.get(answer__question=question, keywords=keywords, label=label)
    except models.Theme.DoesNotExist:
        theme = models.Theme(keywords=keywords, label=label)
        theme.save()
    return theme


# TODO - sort out mypy error
def save_answer_theme(answer_row: NamedTuple) -> models.Answer:
    # Row of answer_df with free_text answers and topic classification
    answer = models.Answer.objects.get(id=answer_row.id)  # type: ignore
    theme = get_or_create_theme_for_question(answer.question, label=answer_row.Name, keywords=answer_row.Representation)  # type: ignore
    answer.theme = theme
    answer.save()
    return answer


def save_themes_to_answers(answers_topics_df: pd.DataFrame) -> None:
    for row in answers_topics_df.itertuples():
        save_answer_theme(row)


def save_themes_for_question(question_id: UUID) -> None:
    # Need to fix order
    answers_qs = models.Answer.objects.filter(question__id=question_id).order_by("created_at")
    free_text_responses = list(answers_qs.values_list("free_text", flat=True))
    embeddings = get_embeddings_for_question(free_text_responses)
    topic_model = get_topic_model(free_text_responses, embeddings)
    answers_topics_df = get_answers_and_topics(topic_model, answers_qs)
    print("answers_topics_df")
    print(answers_topics_df)
    print("====")
    save_themes_to_answers(answers_topics_df)


def save_themes_for_consultation(consultation_id: UUID) -> None:
    questions = models.Question.objects.filter(section__consultation__id=consultation_id, has_free_text=True)
    for question in questions:
        save_themes_for_question(question.id)


# TODO - what to do with topic -1 (outliers)
# https://github.com/MaartenGr/BERTopic


# TODO - Generate theme summaries using LLM
