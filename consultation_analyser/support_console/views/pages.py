from django.contrib.auth import logout
from django.http import HttpRequest
from django.shortcuts import redirect


def sign_out(request: HttpRequest):
    logout(request)
    return redirect("/")
