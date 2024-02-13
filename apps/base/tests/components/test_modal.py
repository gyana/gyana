import pytest
from django import forms
from django.http import HttpResponse
from django.template import RequestContext, Template
from django.urls import path
from playwright.sync_api import expect

from apps.base.views import HttpResponseSeeOther

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
                return HttpResponseSeeOther("/modal")

            return HttpResponse(
                Template(template).render(RequestContext(request, {"form": form})),
                status=422,
            )

        form = TestForm()

        return HttpResponse(
            Template(template).render(RequestContext(request, {"form": form})),
        )

    return path(name, _view, name=name)


_base_template = """{% extends "web/base.html" %}{% block body %}
    <button x-data x-modal="/modal">Click me</button>
{% endblock %}"""

_modal_template = """{% extends "web/base.html" %}{% block body %}
    <div id="modal-root">
        <button class="modal__close"/><i class="fal fa-times fa-lg"></i></button>
        <a id="tab-misc" hx-get="/misc">Tab misc</a>
        <a id="tab-modal" hx-get="/modal?tab=other">Tab {{ request.GET.tab }}</a>
        <input id="modal-search" type="text" />
        <form hx-post="/modal">
            {% csrf_token %}
            {{ form }}
            <button id="modal-submit" value="Save" type="submit">Save</button>
            <button id="modal-preview" value="Save & Preview" type="submit">Save & Preview</button>
        </div>
        {% comment %} POST logic for forms ignores query string {% endcomment %}
        <form hx-post="/misc?tab=post">
            {% csrf_token %}
            <button id="misc-submit" type="submit">Misc</button>
        </div>
    </div>
{% endblock %}
"""

_persist_template = """{% extends "web/base.html" %}{% block body %}
    <button x-data x-modal.persist="/modal/10">Click me</button>
{% endblock %}"""

_misc_template = """Ignore me"""

_dblclick_template = """{% extends "web/base.html" %}{% block body %}
    <button x-data x-modal:dblclick="/modal">Click me</button>
{% endblock %}"""


def test_modal_open_close(dynamic_view, live_server_js, page):
    temporary_urls = [
        _template_view(_base_template, "base"),
        _template_view(_modal_template, "modal"),
    ]
    dynamic_view(temporary_urls)

    page.goto(live_server_js.url + "/base")

    # open the modal
    page.locator("button").click()
    expect(page.locator("#modal-root")).to_be_attached()

    # close with cross
    page.locator(".modal__close").click()
    expect(page.locator("#modal-root")).not_to_be_attached()

    # close by clicking outside
    page.locator("button").click()
    page.locator(".modal").click(position={"x": 5, "y": 5})
    expect(page.locator("#modal-root")).not_to_be_attached()

    warning = page.get_by_text("You have unsaved changes that will be lost on closing")

    # warning modal
    page.locator("button").click()
    page.locator("input[name=name]").fill("valid")
    page.locator(".modal__close").click()
    expect(warning).to_be_attached()

    # stay
    page.get_by_text("Stay").click()
    expect(warning).not_to_be_attached()
    expect(page.locator("#modal-root")).to_be_attached()

    # close anyway
    page.locator(".modal__close").click()
    expect(warning).to_be_attached()
    page.get_by_text("Close Anyway").click()
    expect(warning).not_to_be_attached()
    expect(page.locator("#modal-root")).not_to_be_attached()

    # don't show warning if changed field has no name
    page.locator("button").click()
    expect(page.locator("#modal-root")).to_be_attached()
    page.locator("#modal-search").fill("search")
    page.locator(".modal__close").click()
    expect(warning).not_to_be_attached()


def test_modal_post(dynamic_view, live_server_js, page):
    temporary_urls = [
        _template_view(_base_template, "base"),
        _template_view(_modal_template, "modal"),
        _template_view(_misc_template, "misc"),
    ]
    dynamic_view(temporary_urls)

    # post logic ignores query string
    page.goto(live_server_js.url + "/base?tab=test")

    # do not close on POST to another URL
    page.locator("button").click()
    page.locator("#misc-submit").click()
    expect(page.locator("#modal-root")).to_be_attached()

    # do not close if form is invalid
    page.locator("input[name=name]").fill("invalid")
    page.locator("#modal-submit").click()
    expect(page.get_by_text("Invalid name")).to_be_attached()
    expect(page.locator("#modal-root")).to_be_attached()

    # do not close if preview
    page.locator("input[name=name]").fill("valid")
    page.locator("#modal-preview").click()
    expect(page.get_by_text("Invalid name")).not_to_be_attached()
    expect(page.locator("#modal-root")).to_be_attached()

    # explicit close after preview (changed is reset)
    page.locator(".modal__close").click()
    expect(page.locator("#modal-root")).not_to_be_attached()

    # close on POST to x-modal URL
    page.locator("button").click()
    page.locator("input[name=name]").fill("valid")
    page.locator("#modal-submit").click()
    expect(page.locator("#modal-root")).not_to_be_attached()


def test_modal_persist(dynamic_view, live_server_js, page):
    temporary_urls = [
        _template_view(_persist_template, "persist"),
        _template_view(_modal_template, "modal/10"),
    ]

    dynamic_view(temporary_urls)

    page.goto(live_server_js.url + "/persist")

    # open the modal
    page.locator("button").click()
    expect(page.locator("#modal-root")).to_be_attached()

    # check that URL is updated
    assert page.url == live_server_js.url + "/persist?modal_item=10"

    # refresh the page and check modal is still open
    page.reload()
    expect(page.locator("#modal-root")).to_be_attached()

    # check modal is not persisted after closed
    page.locator(".modal__close").click()
    expect(page.locator("#modal-root")).not_to_be_attached()

    assert page.url == live_server_js.url + "/persist?"


def test_modal_tabs(dynamic_view, live_server_js, page):
    temporary_urls = [
        _template_view(_base_template, "base"),
        _template_view(_modal_template, "modal"),
        _template_view(_misc_template, "misc"),
    ]
    dynamic_view(temporary_urls)

    # tab logic ignores query string
    page.goto(live_server_js.url + "/base?tab=test")

    # open the modal
    page.locator("button").click()
    expect(page.locator("#modal-root")).to_be_attached()

    warning = page.get_by_text("You have unsaved changes that will be lost on closing")

    # warning
    page.locator("input[name=name]").fill("valid")
    page.locator("#tab-modal").click()
    expect(warning).to_be_attached()

    # stay
    page.get_by_text("Stay").click()
    expect(warning).not_to_be_attached()
    expect(page.locator("#modal-root")).to_be_attached()
    expect(page.get_by_text("Tab other")).not_to_be_attached()

    # close anyway
    page.locator("#tab-modal").click()
    expect(warning).to_be_attached()
    page.get_by_text("Close Anyway").click()
    expect(warning).not_to_be_attached()
    expect(page.get_by_text("Tab other")).to_be_attached()

    # only for tab with same URL
    page.locator("input[name=name]").fill("valid")
    page.locator("#tab-misc").click()
    expect(warning).not_to_be_attached()
    expect(page.get_by_text("Ignore me")).to_be_attached()


def test_modal_dblclick(dynamic_view, live_server_js, page):
    temporary_urls = [
        _template_view(_dblclick_template, "dblclick"),
        _template_view(_modal_template, "modal"),
    ]
    dynamic_view(temporary_urls)

    page.goto(live_server_js.url + "/dblclick")

    # does not open modal
    page.locator("button").click()
    expect(page.locator("#modal-root")).not_to_be_attached()

    # open the modal
    page.locator("button").dblclick()
    expect(page.locator("#modal-root")).to_be_attached()
