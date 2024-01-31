import pytest
from django.http import HttpResponse
from django.urls import path
from playwright.sync_api import expect

pytestmark = pytest.mark.django_db

from django.template import Template, RequestContext


def _template_view(template, name):
    def _view(request):
        return HttpResponse(Template(template).render(RequestContext(request, {})))

    return path(name, _view, name=name)


_base_template = """{% extends "web/base.html" %}{% block body %}
    <button x-data x-modal="/get">Click me</button>
{% endblock %}"""

_get_template = """{% extends "web/base.html" %}{% block body %}
    <div id="get">
        <button class="tf-modal__close"/><i class="fal fa-times fa-lg"></i></button>
        <form method="post" action="/post">
            <button type="submit">Submit</button>
        </div>
    </div>
{% endblock %}
"""

_post_template = """{% extends "web/base.html" %}{% block body %}
    TBD
{% endblock %}
"""


def test_modal_basic(dynamic_view, live_server_js, page):
    temporary_urls = [
        _template_view(_base_template, "base"),
        _template_view(_get_template, "get"),
    ]
    dynamic_view(temporary_urls)

    page.goto(live_server_js.url + "/base")

    page.locator("button").click()
    expect(page.locator("#get")).to_be_attached()

    page.locator(".tf-modal__close").click()
    expect(page.locator("#get")).not_to_be_attached()
