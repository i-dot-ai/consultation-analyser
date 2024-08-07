from django.shortcuts import redirect
from django.urls import path

from .views import api, consultations, consultations_users, pages, users

urlpatterns = [
    path("", lambda request: redirect("/support/consultations/")),
    path("sign-out/", pages.sign_out),
    path("users/", users.index),
    path("users/new/", users.new),
    path("users/<int:user_id>/", users.show),
    path("me/", users.my_account),
    path("consultations/", consultations.index),
    path("consultations/<uuid:consultation_id>/", consultations.show, name="support_consultation"),
    path(
        "consultations/<uuid:consultation_id>/delete/",
        consultations.delete,
        name="delete_consultation",
    ),
    path(
        "consultations/<uuid:consultation_id>/users/<int:user_id>/remove/",
        consultations_users.delete,
        name="remove_user",
    ),
    path(
        "consultations/<uuid:consultation_id>/users/new/",
        consultations_users.new,
        name="add_user",
    ),
    path(
        "download/consultations/<str:consultation_slug>/processing_run/<str:processing_run_slug>/",
        consultations.download,
        name="download_consultation",
    ),
    # api
    path("api/hello-world/", api.hello_world),
    path("api/upload-data/", api.upload_json_data),
]
