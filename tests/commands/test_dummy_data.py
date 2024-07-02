import os
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from consultation_analyser.consultations import models


@pytest.mark.django_db
@patch("consultation_analyser.hosting_environment.HostingEnvironment.is_local", return_value=True)
def test_name_parameter_sets_consultation_name(mock_is_local):
    call_command(
        "generate_dummy_data",
        name="My special consultation",
        stdout=StringIO(),  # we'll ignore this
    )

    assert models.Consultation.objects.count() == 1
    assert models.Question.objects.count() == 10
    assert models.Answer.objects.count() >= 100

    assert models.Theme.objects.filter(is_outlier=True).exists()

    assert models.Consultation.objects.first().name == "My special consultation"
    assert models.Consultation.objects.first().slug == "my-special-consultation"


@pytest.mark.django_db
@pytest.mark.parametrize("environment", ["prod"])
def test_the_tool_will_only_run_in_dev(environment):
    with patch.dict(os.environ, {"ENVIRONMENT": environment}):
        with pytest.raises(
            Exception, match=r"Dummy data generation should not be run in production"
        ):
            call_command(
                "generate_dummy_data",
                name="My special consultation",
                stdout=StringIO(),  # we'll ignore this
            )
