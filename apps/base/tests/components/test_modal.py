import pytest
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import get_resolver, path

pytestmark = pytest.mark.django_db


def modal_view(request):
    return HttpResponse(
        render_to_string(
            "test/modal.html", {"test": open("static/js/base-bundle.js", "r").read()}
        )
    )


def modal_get(request):
    return HttpResponse("Hi")


temporary_urls = [
    path("temp-view/", modal_view, name="temp-view"),
    path("get/", modal_view, name="get"),
]


@pytest.fixture
def dynamic_urlconf(settings):
    settings.ROOT_URLCONF = "gyana.urls"

    get_resolver(settings.ROOT_URLCONF).url_patterns += temporary_urls
    yield
    get_resolver(settings.ROOT_URLCONF).url_patterns.remove(temporary_urls[-1])


def test_dynamic_view_renders_html(client, dynamic_urlconf, live_server, page):
    page.goto(live_server.url + "/temp-view/")
