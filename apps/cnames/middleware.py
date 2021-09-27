from apps.dashboards.models import Dashboard
from django.conf import settings
from django.http import HttpResponseForbidden
from django.http.request import split_domain_port, validate_host
from django.urls import resolve

from .models import CName

CNAME_ALLOWED = [
    "dashboards:public",
    "dashboard_widgets:output",
]


class HostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # adapted from django/http/request.py

        host = request._get_raw_host()

        # Allow variants of localhost if ALLOWED_HOSTS is empty and DEBUG=True.
        allowed_hosts = settings.CNAME_ALLOWED_HOSTS
        if settings.DEBUG and not allowed_hosts:
            allowed_hosts = [".localhost", "127.0.0.1", "[::1]"]

        domain, port = split_domain_port(host)
        if domain and validate_host(domain, allowed_hosts):
            return self.get_response(request)

        cname = CName.objects.filter(domain=host).first()
        if not cname:
            return HttpResponseForbidden()

        # only public dashboards owned by team are available
        resolver_match = resolve(request.path_info)
        route_name = f"{':'.join(resolver_match.app_names)}:{resolver_match.url_name}"

        if route_name in CNAME_ALLOWED:

            dashboard_exists_in_team = Dashboard.objects.filter(
                shared_id=resolver_match.kwargs.get("shared_id"),
                project__team__cname=cname,
            ).exists()

            if dashboard_exists_in_team:
                return self.get_response(request)

        return HttpResponseForbidden()
