from uuid import UUID
from typing import List, NamedTuple

from umap.umap_ import UMAP
from sentence_transformers import SentenceTransformer
from hdbscan import HDBSCAN
from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import pandas as pd

from consultation_analyser.consultations import models


def get_embeddings_for_question(answers_list: List, embedding_model_name: str = "thenlper/gte-small") -> List:
    free_text_responses = [answer["free_text"] for answer in answers_list]
    embedding_model = SentenceTransformer(embedding_model_name)
    embeddings = embedding_model.encode(free_text_responses)
    z = zip(answers_list, embeddings)
    answers_list_with_embeddings = [dict(list(d.items()) + [("embedding", embedding)]) for d, embedding in z]
    return answers_list_with_embeddings


def get_topic_model(answers_list_with_embeddings: List) -> BERTopic:
    free_text_responses_list = [answer["free_text"] for answer in answers_list_with_embeddings]
    embeddings = [answer["embedding"] for answer in answers_list_with_embeddings]
    embeddings = np.array(embeddings)
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


def get_answers_and_topics(topic_model: BERTopic, answers_list: List) -> pd.DataFrame:
    # Answers free text/IDs need to be in the same order
    free_text_responses = [answer["free_text"] for answer in answers_list]
    answers_id_list = [answer["id"] for answer in answers_list]
    # Assign topics to answers
    answers_df = topic_model.get_document_info(free_text_responses)
    answers_df["id"] = answers_id_list
    answers_df = answers_df[["id", "Topic", "Name", "Representation"]]
    return answers_df


# TODO - sort out mypy error
def save_theme_to_answer(question: models.Question, answer_row: NamedTuple) -> models.Answer:
    # Row of answer_df with free_text answers and topic classification
    answer = models.Answer.objects.get(id=answer_row.id)  # type: ignore
    theme, _ = models.Theme.objects.get_or_create(
        question=question, label=answer_row.Name, keywords=answer_row.Representation
    )  # type: ignore
    print(f"theme: {theme}, created: {_}")
    answer.theme = theme
    answer.save()
    return answer


def save_themes_to_answers(question: models.Question, answers_topics_df: pd.DataFrame) -> None:
    print(f"answers_topics_df: {answers_topics_df}")
    for row in answers_topics_df.itertuples():
        save_theme_to_answer(question, row)


def save_themes_for_question(question: models.Question) -> None:
    # Need to fix order
    answers_qs = models.Answer.objects.filter(question=question).order_by("created_at")
    answers_list = list(answers_qs.values("id", "free_text"))
    answers_list_with_embeddings = get_embeddings_for_question(answers_list)
    topic_model = get_topic_model(answers_list_with_embeddings)
    answers_topics_df = get_answers_and_topics(topic_model, answers_list_with_embeddings)
    save_themes_to_answers(question, answers_topics_df)


def save_themes_for_consultation(consultation_id: UUID) -> None:
    questions = models.Question.objects.filter(section__consultation__id=consultation_id, has_free_text=True)
    for question in questions:
        save_themes_for_question(question)


# TODO - what to do with topic -1 (outliers)
# https://github.com/MaartenGr/BERTopic


# TODO - Generate theme summaries using LLM
