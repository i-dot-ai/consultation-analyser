def test_get_public_schema_page(django_app):
    schema_page = django_app.get("/schema")

    assert "Data schema" in schema_page
