from django.http import HttpResponseRedirect


class SupportAppStaffRequiredMiddleware:
    """Require staff users only for support app."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith("/support/"):
            # if isinstance(request.user, AnonymousUser):
            if not request.user:
                return HttpResponseRedirect("/")
            elif not request.user.is_staff:
                return HttpResponseRedirect("/")
        return None
