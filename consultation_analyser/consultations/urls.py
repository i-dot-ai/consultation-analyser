from django.urls import include, path
from magic_link import urls as magic_link_urls

from .views import consultations, pages, questions, responses, root, schema, sessions

urlpatterns = [
    path("", root.root),
    path("how-it-works/", pages.how_it_works),
    path("schema/", schema.show),
    path("data-sharing/", pages.data_sharing),
    path("get-involved/", pages.get_involved),
    path("privacy/", pages.privacy),
    path("consultations/", consultations.index, name="consultations"),
    path("consultations/new/", consultations.new, name="new_consultation"),
    path("consultations/<str:consultation_slug>/", consultations.show, name="consultation"),
    path(
        "consultations/<str:consultation_slug>/runs/<str:processing_run_slug>/",
        consultations.show,
        name="consultation_run",
    ),
    path("schema/<str:schema_name>.json", schema.raw_schema),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>/",
        questions.show,
        name="show_question",
    ),
    path(
        "consultations/<str:consultation_slug>/runs/<str:processing_run_slug>/sections/<str:section_slug>/questions/<str:question_slug>/",
        questions.show,
        name="show_question_runs",
    ),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/responses/<str:question_slug>/",
        responses.index,
        name="question_responses",
    ),
    path(
        "consultations/<str:consultation_slug>/runs/<str:processing_run_slug>/sections/<str:section_slug>/responses/<str:question_slug>/",
        responses.index,
        name="question_responses_runs",
    ),
    # authentication
    path("sign-in/", sessions.new),
    path("sign-out/", sessions.destroy),
    path("magic-link/", include(magic_link_urls)),
]
