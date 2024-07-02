import pytest
from django.conf import settings
from webtest import Upload

from consultation_analyser.factories import ProcessingRunFactory, UserFactory
from consultation_analyser.pipeline.backends.dummy_topic_backend import DummyTopicBackend
from consultation_analyser.pipeline.ml_pipeline import save_themes_for_processing_run
from tests.helpers import sign_in


@pytest.mark.django_db
def test_user_uploads_consultation(django_app):
    # given i am a user without a consultation
    user = UserFactory()

    # when I sign in
    consultations_page = sign_in(django_app, user.email)

    # and I click the link to upload
    upload_page = consultations_page.click("Upload a consultation")

    # then I should see an upload page
    assert "Upload a consultation" in upload_page

    with open(settings.BASE_DIR / "tests" / "examples" / "upload.json", "r") as f:
        binary_data = str.encode(f.read())

    # and when I provide my JSON and submit the form
    upload_page.form["consultation_json"] = Upload(
        "consultation.json", binary_data, "application/json"
    )
    success_page = upload_page.form.submit()

    # then I should see a success page
    assert "Consultation uploaded" in success_page

    # and when I visit the consultation again I shouldn't still see a processing message
    consultation = user.consultation_set.first()
    processing_run = ProcessingRunFactory(consultation=consultation)
    processing_page = django_app.get(f"/consultations/{consultation.slug}/")
    assert "processing your consultation" not in processing_page

    save_themes_for_processing_run(DummyTopicBackend(), processing_run)

    consultation_page = django_app.get(f"/consultations/{consultation.slug}/")
    assert consultation.name in consultation_page
