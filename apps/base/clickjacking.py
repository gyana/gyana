from functools import wraps
from urllib.parse import urlparse

from django.urls import Resolver404, resolve

ALLOWLIST = ["web:home", "teams:pricing"]


def xframe_options_sameorigin_allowlist(view_func):
    """
    Fork of https://github.com/django/django/blob/main/django/views/decorators/clickjacking.py
    with an allowlist of referrer domains. Original docstring:

    Modify a view function so its response has the X-Frame-Options HTTP
    header set to 'SAMEORIGIN' as long as the response doesn't already have
    that header set. Usage:
    @xframe_options_sameorigin
    def some_view(request):
        ...
    """

    def wrapped_view(request, *args, **kwargs):
        resp = view_func(request, *args, **kwargs)

        try:
            referer = request.headers.get("Referer")
            if referer:
                referrer_view_name = resolve(urlparse(referer).path).view_name
                if (
                    referrer_view_name in ALLOWLIST
                    and resp.get("X-Frame-Options") is None
                ):
                    resp["X-Frame-Options"] = "SAMEORIGIN"

        except Resolver404:
            pass

        return resp

    return wraps(view_func)(wrapped_view)
