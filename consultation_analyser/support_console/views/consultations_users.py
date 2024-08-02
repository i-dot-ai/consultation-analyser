from uuid import UUID

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from consultation_analyser.consultations import models
from consultation_analyser.support_console.decorators import support_login_required
from consultation_analyser.support_console.forms.add_users_to_consultation_form import (
    AddUsersToConsultationForm,
)


# @support_login_required
def new(request: HttpRequest, consultation_id: UUID):
    consultation = models.Consultation.objects.get(id=consultation_id)
    users = models.User.objects.exclude(id__in=[u.id for u in consultation.users.all()]).all()

    if request.POST:
        form = AddUsersToConsultationForm(request.POST, users=users, consultation=consultation)
        if form.is_valid():
            users = form.cleaned_data["users"]
            for user in users:
                consultation.users.add(user)
            messages.success(request, "Users updated")
            return redirect(
                reverse("support_consultation", kwargs={"consultation_id": consultation.id})
            )
    else:
        form = AddUsersToConsultationForm(users=users, consultation=consultation)

    context = {"form": form}

    return render(request, "support_console/consultations_users/new.html", context=context)


# @support_login_required
def delete(request: HttpRequest, consultation_id: UUID, user_id: UUID) -> HttpResponse:
    consultation = models.Consultation.objects.get(id=consultation_id)
    user = models.User.objects.get(id=user_id)

    context = {
        "consultation": consultation,
        "user": user,
    }

    if request.POST:
        if "confirm_removal" in request.POST:
            consultation.users.remove(user)
            messages.success(request, f"{user.email} has been removed from this consultation")
            return redirect(
                reverse("support_consultation", kwargs={"consultation_id": consultation.id})
            )

    return render(request, "support_console/consultations_users/delete.html", context=context)
