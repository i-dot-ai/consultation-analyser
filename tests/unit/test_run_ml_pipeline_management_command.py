# Tests for dummy ML pipeline
from io import StringIO

import pytest

from consultation_analyser.consultations.models import Consultation
from django.core.management import call_command


@pytest.mark.django_db
def test_command_with_valid_slug():
    Consultation.objects.create(slug="test-consultation", name="Test Consultation")
    out = StringIO()
    call_command("run_ml_pipeline", consultation_slug="test-consultation", stdout=out)
    assert "Test Consultation" in out.getvalue(), out.getvalue()


@pytest.mark.django_db
def test_command_with_invalid_slug():
    out = StringIO()
    call_command("run_ml_pipeline", consultation_slug="invalid-slug", stdout=out)
    assert "enter a valid slug" in out.getvalue(), out.getvalue()


@pytest.mark.django_db
def test_command_without_slug():
    out = StringIO()
    call_command("run_ml_pipeline", stdout=out)
    assert "enter the slug" in out.getvalue(), out.getvalue()
