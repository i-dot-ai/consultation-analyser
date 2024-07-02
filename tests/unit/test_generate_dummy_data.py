import os
from unittest.mock import patch

import pytest

from consultation_analyser.consultations.dummy_data import create_dummy_data
from consultation_analyser.consultations.models import Answer, Consultation, Question


@pytest.mark.django_db
@patch("consultation_analyser.hosting_environment.HostingEnvironment.is_local", return_value=True)
def test_a_consultation_is_generated(settings):
    assert Consultation.objects.count() == 0

    create_dummy_data()

    assert Consultation.objects.count() == 1
    assert Question.objects.count() == 10
    assert Answer.objects.count() >= 100

    qs = Answer.objects.filter(themes__is_outlier=True)
    assert qs.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("environment", ["prod"])
def test_the_tool_will_only_run_in_dev(environment):
    with patch.dict(os.environ, {"ENVIRONMENT": environment}):
        with pytest.raises(
            Exception, match=r"Dummy data generation should not be run in production"
        ):
            create_dummy_data()
