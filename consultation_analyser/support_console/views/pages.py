from django.contrib.auth import logout
from django.http import HttpRequest
from django.shortcuts import redirect


# @support_login_required
def sign_out(request: HttpRequest):
    logout(request)
    return redirect("/")
