import requests
from django.conf import settings

CHECK_IN_URL = "https://api.honeybadger.io/v1/check_in"


def honeybadger_check_in(key):
    if settings.ENVIRONMENT == "production":
        requests.get(f"{CHECK_IN_URL}/{key}")
