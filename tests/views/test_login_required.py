import pytest
from django.urls import reverse

from consultation_analyser import factories
from consultation_analyser.consultations.urls import urlpatterns

PUBLIC_URL_NAMES = [
    "root",
    "how_it_works",
    "schema",
    "data_sharing",
    "get_involved",
    "privacy",
]
RAW_SCHEMA_URL_NAMES = ["raw_schema"]
GENERIC_CONSULTATION_URL_NAMES = ["consultations", "new_consultation"]
AUTHENTICATION_URL_NAMES = [
    "sign_in",
    "sign_out",
    "magic_link",
]  # No tests - tested elsewhere, all public

URL_NAMES_TO_EXCLUDE = (
    PUBLIC_URL_NAMES
    + RAW_SCHEMA_URL_NAMES
    + GENERIC_CONSULTATION_URL_NAMES
    + AUTHENTICATION_URL_NAMES
)


@pytest.mark.django_db
def test_access_public_urls_no_login(client):
    for url_name in PUBLIC_URL_NAMES:
        url = reverse(url_name)
        response = client.get(url)
        assert response.status_code == 200
    # There are more schema names, won't include them all
    for schema_name in ["consultation_with_responses_schema", "consultation_schema"]:
        url = reverse("raw_schema", kwargs={"schema_name": schema_name})
        response = client.get(url, format="json")
        assert response.status_code == 200


@pytest.mark.django_db
def test_access_generic_consultation_urls(client):
    for url_name in GENERIC_CONSULTATION_URL_NAMES:
        url = reverse(url_name)
        # No login should redirect
        response = client.get(url)
        assert response.status_code == 302
        # Any logged in user should be able to access pages
        user = factories.UserFactory()
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == 200
        client.logout()


def set_up_consultation(user):
    question = factories.QuestionFactory()
    section = question.section
    consultation = section.consultation
    processing_run = factories.ProcessingRunFactory(consultation=consultation)
    consultation.users.add(user)
    consultation.save()
    possible_args = {
        "consultation_slug": consultation.slug,
        "processing_run_slug": processing_run.slug,
        "section_slug": section.slug,
        "question_slug": question.slug,
    }
    return possible_args


def check_expected_status_code(client, url, expected_status_code):
    response = client.get(url)
    assert response.status_code == expected_status_code


def get_url_for_pattern(url_pattern, possible_args):
    # Get a dictionary of any args that might occur
    url_str = str(url_pattern)
    kwargs = {}
    for key in possible_args:
        if key in url_str:
            kwargs[key] = possible_args[key]
    url = reverse(url_pattern.name, kwargs=kwargs)
    return url


@pytest.mark.django_db
def test_consultations_urls_login_required(client):
    """
    This tests all URLs by default unless deliberately excluded (special cases).

    This tests that login is required AND that only users who can see the consultation
    can access pages.

    If you have added a new URL and this test is failing either:
        (1) it should pass and your view is wrong or
        (2) add it as a special case to be excluded and write a separate test.
    """

    user = factories.UserFactory()
    non_consultation_user = factories.UserFactory()
    possible_args = set_up_consultation(user)

    # Get all URLs that haven't explicitly been excluded.
    # Exclude magic links in separate step as potentially more than one.
    url_patterns_excluding_magic_link = [
        url_pattern
        for url_pattern in urlpatterns
        if not str(url_pattern.pattern).startswith("magic-link")
    ]
    url_patterns_to_test = [
        url_pattern
        for url_pattern in url_patterns_excluding_magic_link
        if url_pattern.name not in URL_NAMES_TO_EXCLUDE
    ]

    for url_pattern in url_patterns_to_test:
        url = get_url_for_pattern(url_pattern, possible_args)

        # Not logged in - should 404
        check_expected_status_code(client, url, expected_status_code=404)

        # Logged in with a user for this consultation - 200
        client.force_login(user)
        check_expected_status_code(client, url, 200)
        client.logout()

        # Logged in with a different user - 404
        client.force_login(non_consultation_user)
        check_expected_status_code(client, url, 404)
        client.logout()
