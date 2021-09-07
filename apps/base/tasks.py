import requests
from django.conf import settings

CHECK_IN_URL = "https://api.honeybadger.io/v1/check_in"


def honeybadger_check_in(key):
    print(settings.ENVIRONMENT)
    # if settings.ENVIRONMENT == "local":
    requests.get(f"{CHECK_IN_URL}/{key}")
