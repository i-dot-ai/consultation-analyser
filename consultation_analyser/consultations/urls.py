from django.urls import path

from . import views

urlpatterns = [
    path("", views.home),
    path("consultations", views.consultation),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>",
        views.show_question,
        name="show_question",
    ),
]
