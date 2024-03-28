from django.urls import path

from .views import static_pages, schema, questions

urlpatterns = [
    path("", static_pages.home),
    path("schema", schema.show),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>",
        questions.show,
        name="show_question",
    ),
]
