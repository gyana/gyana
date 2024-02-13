from typing import Any
from django.http.response import HttpResponse as HttpResponse
from django.template import Template, RequestContext
import pytest
from django import forms
from django.db import models
from django.urls import path
from playwright.sync_api import expect
from apps.base.forms import ModelForm
from django.test.utils import isolate_apps
from apps.base.views import CreateView
from pytest import fixture
from django.db import connection

pytestmark = pytest.mark.django_db


@isolate_apps("test")
@fixture
def test_view():
    class TestModel(models.Model):
        class SelectChoices(models.TextChoices):
            ONE = "one", "One"
            TWO = "two", "Two"

        select = models.CharField(
            max_length=255, choices=SelectChoices.choices, default=SelectChoices.ONE
        )
        other_select = models.CharField(max_length=255, null=True, blank=True)
        name = models.CharField(max_length=255, null=True)

    class TestForm(ModelForm):
        class Meta:
            model = TestModel
            fields = "__all__"
            widgets = {"other_select": forms.Select()}
            show = {"name": "select == 'one'"}
            effect = "choices.other_select = select.split('').map(c => ({value: c, label: c}))"

        def clean_name(self):
            name = self.cleaned_data["name"]

            if name == "invalid":
                raise forms.ValidationError("Invalid name")

            return name

    class TestView(CreateView):
        model = TestModel
        form_class = TestForm
        success_url = "/success"

        def render_to_response(self, context, **response_kwargs):
            return HttpResponse(
                Template(_base_template).render(RequestContext(self.request, context)),
            )

    _base_template = """{% extends "web/base.html" %}{% load crispy_forms_tags %}{% block body %}
        <form method="post">
            {% csrf_token %}
            {% crispy form %}
            <button type="submit">Submit</button>
        </form>
    {% endblock %}"""

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(TestModel)

    yield TestView.as_view()

    with connection.schema_editor() as schema_editor:
        schema_editor.delete_model(TestModel)


def test_create(dynamic_view, live_server, page, test_view):
    TestModel = test_view.view_class.model

    temporary_urls = [path("base", test_view, name="base")]
    dynamic_view(temporary_urls)

    assert TestModel.objects.count() == 0

    # get
    r = page.goto(live_server.url + "/base")
    assert r.status == 200

    # invalid
    page.fill('input[name="name"]', "invalid")
    page.locator("button").click()
    expect(page.get_by_text("Invalid name")).to_be_attached()

    # post
    page.fill('input[name="name"]', "valid")
    page.locator("button").click()

    page.wait_for_url("/success")
    assert TestModel.objects.count() == 1


def test_show(dynamic_view, live_server, page, test_view):
    TestModel = test_view.view_class.model

    temporary_urls = [path("base", test_view, name="base")]
    dynamic_view(temporary_urls)

    page.goto(live_server.url + "/base")

    # hide
    page.select_option("select", "two")
    expect(page.locator("input[name=name]")).not_to_be_attached()

    # post
    page.locator("button").click()

    assert TestModel.objects.count() == 1

    test_model = TestModel.objects.first()

    assert test_model.select == "two"
    assert test_model.name is None


def test_effect_choices(dynamic_view, live_server, page, test_view):
    TestModel = test_view.view_class.model

    temporary_urls = [path("base", test_view, name="base")]
    dynamic_view(temporary_urls)

    page.goto(live_server.url + "/base")

    # effect
    page.select_option("select", "two")

    expect(page.locator("select[name=other_select]"))

    option_values = {
        option.get_attribute("value")
        for option in page.locator("select[name=other_select] option").all()
    }

    assert option_values == {"t", "w", "o"}
