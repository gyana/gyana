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
from apps.base.formsets import RequiredInlineFormset
from apps.base.views import CreateView
from pytest import fixture
from django.db import connection
from crispy_forms.bootstrap import TabHolder
from crispy_forms.layout import Layout
from apps.base.crispy import CrispyFormset, Tab

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
        name = models.CharField(max_length=255, null=True, blank=True)
        tab_field = models.CharField(max_length=255, null=True, blank=True)

    class TestChildModel(models.Model):
        key = models.CharField(max_length=255)
        value = models.CharField(max_length=255, null=True, blank=True)
        parent = models.ForeignKey(
            "TestModel", on_delete=models.CASCADE, related_name="test_formset"
        )

    class TestChildForm(ModelForm):
        class Meta:
            model = TestChildModel
            fields = "__all__"

    TestFormset = forms.inlineformset_factory(
        parent_model=TestModel,
        model=TestChildModel,
        form=TestChildForm,
        formset=RequiredInlineFormset,
        can_delete=True,
        extra=0,
    )

    class TestForm(ModelForm):
        class Meta:
            model = TestModel
            fields = "__all__"
            widgets = {"other_select": forms.Select()}
            show = {"name": "select == 'one'"}
            effect = "choices.other_select = select.split('').map(c => ({value: c, label: c}))"
            formsets = {
                "test_formset": TestFormset,
            }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.helper.layout = Layout(
                TabHolder(
                    Tab(
                        "General",
                        "select",
                        "other_select",
                        "name",
                        CrispyFormset("test_formset", "Test Formset"),
                    ),
                    Tab(
                        "Tab",
                        "tab_field",
                    ),
                )
            )

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
            <button id="submit-form" type="submit">Submit</button>
        </form>
    {% endblock %}"""

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(TestModel)
        schema_editor.create_model(TestChildModel)

    yield TestView.as_view()

    with connection.schema_editor() as schema_editor:
        schema_editor.delete_model(TestModel)
        schema_editor.delete_model(TestChildModel)


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
    page.locator("#submit-form").click()
    expect(page.get_by_text("Invalid name")).to_be_attached()

    # post
    page.fill('input[name="name"]', "valid")
    page.locator("#submit-form").click()

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
    page.locator("#submit-form").click()

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


def test_formset(dynamic_view, live_server, page, test_view):
    TestModel = test_view.view_class.model

    temporary_urls = [path("base", test_view, name="base")]
    dynamic_view(temporary_urls)

    page.goto(live_server.url + "/base")

    page.get_by_text("Add new").click()
    page.locator('input[name="test_formset-0-key"]').fill("key")

    page.locator("#submit-form").click()

    assert TestModel.objects.count() == 1
    assert TestModel.objects.first().test_formset.count() == 1
    assert TestModel.objects.first().test_formset.first().key == "key"
