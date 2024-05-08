from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from consultation_analyser.authentication.models import User

from ..forms.edit_user_form import EditUserForm
from ..forms.new_user_form import NewUserForm


@staff_member_required
def index(request: HttpRequest):
    users = User.objects.all().order_by("-created_at")
    return render(request, "support_console/all-users.html", {"users": users})


@staff_member_required
def new(request: HttpRequest):
    if not request.POST:
        form = NewUserForm()
    else:
        form = NewUserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            User.objects.create_user(email=email)
            messages.success(request, "User added")
            return redirect("/support/users")

    return render(request, "support_console/new-user.html", {"form": form})


@staff_member_required
def show(request: HttpRequest, user_id: int):
    user = get_object_or_404(User, pk=user_id)
    consultations = user.consultation_set.all()

    if not request.POST:
        form = EditUserForm({"user_id": user_id, "is_staff": user.is_staff})
    else:
        form = EditUserForm(request.POST, current_user=request.user)
        if form.is_valid():
            is_staff = form.cleaned_data["is_staff"]
            user.is_staff = is_staff
            user.save()
            messages.success(request, "User updated")
            return redirect(request.path_info)

    return render(request, "support_console/user.html", {"user": user, "consultations": consultations, "form": form})
