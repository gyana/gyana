from django import forms
import pytest
from django.http import HttpResponse
from django.urls import path
from playwright.sync_api import expect
from django.template import Template, RequestContext

pytestmark = pytest.mark.django_db


class TestForm(forms.Form):
    name = forms.CharField(required=True)

    def clean_name(self):
        name = self.cleaned_data["name"]

        if name == "invalid":
            raise forms.ValidationError("Invalid name")

        return name


def _template_view(template, name):
    def _view(request):
        if request.method == "POST":
            form = TestForm(request.POST)

            if form.is_valid():
                return HttpResponse("OK")

        else:
            form = TestForm()

        return HttpResponse(
            Template(template).render(RequestContext(request, {"form": form}))
        )

    return path(name, _view, name=name)


_base_template = """{% extends "web/base.html" %}{% block body %}
    <button x-data x-modal="/modal">Click me</button>
{% endblock %}"""

_modal_template = """{% extends "web/base.html" %}{% block body %}
    <div id="modal">
        <button class="tf-modal__close"/><i class="fal fa-times fa-lg"></i></button>
        <form hx-post="/modal">
            {% csrf_token %}
            {{ form }}
            <button id="modal-submit" type="submit">Submit</button>
        </div>
        <form hx-post="/misc">
            {% csrf_token %}
            <button id="misc-submit" type="submit">Submit</button>
        </div>
    </div>
{% endblock %}
"""

_persist_template = """{% extends "web/base.html" %}{% block body %}
    <button x-data x-modal.persist="/modal/10">Click me</button>
{% endblock %}"""

_misc_template = """Ignore me"""


def test_modal_open_close(dynamic_view, live_server_js, page):
    temporary_urls = [
        _template_view(_base_template, "base"),
        _template_view(_modal_template, "modal"),
    ]
    dynamic_view(temporary_urls)

    page.goto(live_server_js.url + "/base")

    # open the modal
    page.locator("button").click()
    expect(page.locator("#modal")).to_be_attached()

    # close with cross
    page.locator(".tf-modal__close").click()
    expect(page.locator("#modal")).not_to_be_attached()

    # close by clicking outside
    page.locator("button").click()
    page.locator(".tf-modal").click(position={"x": 5, "y": 5})
    expect(page.locator("#modal")).not_to_be_attached()

    warning = page.get_by_text("You have unsaved changes that will be lost on closing")

    # warning modal
    page.locator("button").click()
    page.locator("input[name=name]").fill("valid")
    page.locator(".tf-modal__close").click()
    expect(warning).to_be_attached()

    # stay
    page.get_by_text("Stay").click()
    expect(warning).not_to_be_attached()
    expect(page.locator("#modal")).to_be_attached()

    # close anyway
    page.locator(".tf-modal__close").click()
    expect(warning).to_be_attached()
    page.get_by_text("Close Anyway").click()
    expect(warning).not_to_be_attached()
    expect(page.locator("#modal")).not_to_be_attached()


def test_modal_post(dynamic_view, live_server_js, page):
    temporary_urls = [
        _template_view(_base_template, "base"),
        _template_view(_modal_template, "modal"),
        _template_view(_misc_template, "misc"),
    ]
    dynamic_view(temporary_urls)

    page.goto(live_server_js.url + "/base")

    # do not close on POST to another URL
    page.locator("button").click()
    page.locator("#misc-submit").click()
    expect(page.locator("#modal")).to_be_attached()

    # do not close if form is invalid
    page.locator("#modal-submit").click()
    page.locator("input[name=name]").fill("invalid")
    expect(page.locator("#modal")).to_be_attached()

    # close on POST to x-modal URL
    page.locator("#modal-submit").click()
    page.locator("input[name=name]").fill("valid")
    expect(page.locator("#modal")).not_to_be_attached()


def test_modal_persist(dynamic_view, live_server_js, page):
    temporary_urls = [
        _template_view(_persist_template, "persist"),
        _template_view(_modal_template, "modal/10"),
    ]

    dynamic_view(temporary_urls)

    page.goto(live_server_js.url + "/persist")

    # open the modal
    page.locator("button").click()
    expect(page.locator("#modal")).to_be_attached()

    # check that URL is updated
    assert page.url == live_server_js.url + "/persist?modal_item=10"

    # refresh the page and check modal is still open
    page.reload()
    expect(page.locator("#modal")).to_be_attached()
