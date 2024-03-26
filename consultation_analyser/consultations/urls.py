from django.urls import path

from . import views

urlpatterns = [
    path("", views.home),
    path("schema", views.schema),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>",
        views.show_question,
        name="show_question",
    ),
]
