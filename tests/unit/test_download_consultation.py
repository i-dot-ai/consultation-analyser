import io
import json

import pytest
from django.conf import settings

from consultation_analyser.consultations.download_consultation import consultation_to_json
from consultation_analyser.consultations.upload_consultation import upload_consultation
from consultation_analyser.factories import ProcessingRunFactory, UserFactory
from consultation_analyser.pipeline.backends.dummy_topic_backend import DummyTopicBackend
from consultation_analyser.pipeline.ml_pipeline import save_themes_for_processing_run


@pytest.mark.django_db
def test_consultation_to_json(django_app):
    user = UserFactory()
    file = open(settings.BASE_DIR / "tests" / "examples" / "upload.json", "rb")

    consultation = upload_consultation(file, user)
    processing_run = ProcessingRunFactory(consultation=consultation)
    save_themes_for_processing_run(DummyTopicBackend(), processing_run=processing_run)

    consultation_json = json.loads(consultation_to_json(consultation))

    assert consultation_json["consultation"]["name"] == "My consultation"

    assert len(consultation_json["consultation"]["sections"]) == 1
    assert len(consultation_json["consultation"]["sections"][0]["questions"]) == 3

    assert len(consultation_json["consultation_responses"]) == 2
    assert len(consultation_json["consultation_responses"][0]["answers"]) == 3

    # dummy theme process assigns on theme per question
    # and we'll only create themes for free_text answers,
    # of which there are 4 in the test data
    assert len(consultation_json["themes"]) == 4

    consultation_json["consultation"]["name"] = "My consultation reuploaded"

    reuploadable_without_themes = consultation_json.copy()
    reuploadable_without_themes.pop("themes")
    file_to_reupload = io.StringIO(json.dumps(reuploadable_without_themes))

    # This will bail if anything goes wrong
    reuploaded = upload_consultation(file_to_reupload, user)

    assert reuploaded
