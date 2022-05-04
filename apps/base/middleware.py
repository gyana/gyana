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
            dataset=settings.ENVIORNMENT,
            debug=True,
        )

        self.get_response = get_response

    def process_request(self, request):
        request.start_time = time.time()

        return None

    def process_response(self, request, response):
        response_time = time.time() - request.start_time

        ev = libhoney.Event(
            data={
                "method": request.method,
                "scheme": request.scheme,
                "path": request.path,
                "query": request.GET,
                "isSecure": request.is_secure(),
                "isAjax": request.is_ajax(),
                "isUserAuthenticated": request.user.is_authenticated(),
                "username": request.user.username,
                "host": request.get_host(),
                "ip": request.META["REMOTE_ADDR"],
                "responseTime_ms": response_time * 1000,
            }
        )
        ev.send()

        return response
