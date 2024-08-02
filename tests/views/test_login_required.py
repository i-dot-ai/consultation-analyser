import pytest
from django.urls import reverse


PUBLIC_URL_NAMES = [
    "root",
    "how_it_works",
    "schema",
    "data_sharing",
    "get_involved",
    "privacy",
]


@pytest.mark.django_db
def test_access_public_urls_no_login(client):
    for url_name in PUBLIC_URL_NAMES:
        url = reverse(url_name)
        response = client.get(url)
        assert response.status_code == 200
