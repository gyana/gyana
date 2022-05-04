import os
import time

import libhoney
from django.conf import settings
from honeybadger import honeybadger


class HoneybadgerUserContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            honeybadger.set_context(
                user_id=request.user.id, user_email=request.user.email
            )
        return self.get_response(request)


class HoneycombMiddleware:
    def __init__(self, get_response):
        libhoney.init(
            writekey=settings.HONEYCOMB_API_KEY,
            dataset=settings.ENVIRONMENT,
        )

        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        response_time = time.time() - start_time

        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        ev = libhoney.new_event(
            data={
                "method": request.method,
                "scheme": request.scheme,
                "path": request.path,
                "query": request.GET,
                "isSecure": request.is_secure(),
                "isAjax": is_ajax,
                "isUserAuthenticated": request.user.is_authenticated,
                "username": request.user.username,
                "host": request.get_host(),
                "ip": request.META["REMOTE_ADDR"],
                "responseTime_ms": response_time * 1000,
            }
        )
        ev.send()

        return response
