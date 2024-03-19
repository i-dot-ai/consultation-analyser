from uuid import UUID
from typing import List

from umap.umap_ import UMAP
from sentence_transformers import SentenceTransformer
from hdbscan import HDBSCAN
from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from django.db.models import QuerySet

from consultation_analyser.consultations import models


def get_embeddings_for_question(
    free_text_responses: List, embedding_model_name: str = "thenlper/gte-small"
) -> np.ndarray:
    embedding_model = SentenceTransformer(embedding_model_name)
    embeddings = embedding_model.encode(free_text_responses)
    return embeddings


def get_topics(free_text_responses_list: List, embeddings: np.ndarray) -> BERTopic:
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


def save_themes(topic_model: BERTopic, question_id: UUID) -> None:
    question = models.Question.objects.get(id=question_id)
    topic_df = topic_model.get_topic_info()
    for row in topic_df.itertuples():
        theme = models.Theme(keywords=row["Representation"], label=["Name"], question=question)
        theme.save()


def save_answers(topic_model: BERTopic, question_id: UUID, answers_qs: QuerySet) -> None:
    free_text_responses = answers_qs.values_list("free_text", flat=True)
    answers_id_list = answers_qs.values_list("id", flat=True)
    # Assign topics to answers
    answers_df = topic_model.get_document_info(free_text_responses)
    # TODO - seems a bit fragile, relies on answers staying in the same order
    answers_df["id"] = answers_id_list
    for row in answers_df.itertuples():
        theme = models.Theme.objects.get(question__id=question_id, label=row["Name"])
        answer = models.Answer.objects.get(id=row["id"])
        answer.theme = theme
        answer.save()


def get_themes_for_question(question_id: UUID) -> None:
    answers_qs = models.Answer.objects.filter(question__id=question_id).order_by("created_at")
    free_text_responses = answers_qs.values_list("free_text", flat=True)
    embeddings = get_embeddings_for_question(free_text_responses)
    topic_model = get_topics(free_text_responses, embeddings)
    save_themes(topic_model, question_id)
    save_answers(topic_model, question_id, answers_qs)


def get_themes_for_consultation(consultation_id: UUID) -> None:
    questions = models.Question.objects.filter(section__consultation__id=consultation_id, has_free_text=True)
    for question in questions:
        get_themes_for_question(question)


# TODO - what to do with topic -1 (outliers)
# https://github.com/MaartenGr/BERTopic


# TODO - Generate theme summaries using LLM
