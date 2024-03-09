from typing import Any

import pytest
from crispy_forms.bootstrap import TabHolder
from crispy_forms.layout import Layout
from django import forms
from django.db import connection, models
from django.http.response import HttpResponse as HttpResponse
from django.template import RequestContext, Template
from django.test.utils import isolate_apps
from django.urls import path
from playwright.sync_api import expect
from pytest import fixture

from apps.base.crispy import CrispyFormset, Tab
from apps.base.forms import ModelForm
from apps.base.formsets import RequiredInlineFormset
from apps.base.views import CreateView, UpdateView

# mark with transaction=True, otherwise flakiness due to deadlocks
pytestmark = pytest.mark.django_db(transaction=True)


@isolate_apps("test")
@fixture
def model(dynamic_view):
    class TestModel(models.Model):
        class SelectChoices(models.TextChoices):
            ONE = "one", "One"
            TWO = "two", "Two"
            FORMSET = "formset", "Formset"

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
        min_num=1,
        max_num=4,
    )

    class TestForm(ModelForm):
        class Meta:
            model = TestModel
            fields = "__all__"
            widgets = {"other_select": forms.Select()}
            show = {"name": "select == 'one'", "test_formset": "select == 'formset'"}
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
                        "Tab link",
                        "tab_field",
                    ),
                )
            )

        def clean_name(self):
            name = self.cleaned_data["name"]

            if name == "invalid":
                raise forms.ValidationError("Invalid name")

            return name

    class TestCreateView(CreateView):
        model = TestModel
        form_class = TestForm
        success_url = "/success"

        def render_to_response(self, context, **response_kwargs):
            return HttpResponse(
                Template(_base_template).render(RequestContext(self.request, context)),
            )

    class TestUpdateView(UpdateView):
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

    temporary_urls = [
        path("new", TestCreateView.as_view(), name="new"),
        path("<int:pk>/update", TestUpdateView.as_view(), name="update"),
    ]
    dynamic_view(temporary_urls)

    yield TestModel

    with connection.schema_editor() as schema_editor:
        schema_editor.delete_model(TestModel)
        schema_editor.delete_model(TestChildModel)


def test_create_update(live_server, page, model):
    assert model.objects.count() == 0

    # get /new
    r = page.goto(live_server.url + "/new")
    assert r.status == 200

    # invalid
    page.fill('input[name="name"]', "invalid")
    page.locator("#submit-form").click()
    expect(page.get_by_text("Invalid name")).to_be_attached()

    # post /new
    page.fill('input[name="name"]', "valid")
    page.locator("#submit-form").click()

    page.wait_for_url("/success")
    assert model.objects.count() == 1
    assert model.objects.first().name == "valid"

    # get /1/update
    page.goto(live_server.url + "/1/update")
    assert r.status == 200

    # post /1/update
    page.fill('input[name="name"]', "updated")
    page.locator("#submit-form").click()

    page.wait_for_url("/success")
    assert model.objects.first().name == "updated"


def test_show(live_server, page, model):
    page.goto(live_server.url + "/new")

    # hide
    page.select_option("select", "two")
    expect(page.locator("input[name=name]")).not_to_be_attached()

    # post
    page.locator("#submit-form").click()

    assert model.objects.count() == 1

    test_model = model.objects.first()

    assert test_model.select == "two"
    assert test_model.name is None


def test_effect_choices(live_server, page, model):
    page.goto(live_server.url + "/new")

    # effect
    page.select_option("select", "two")

    expect(page.locator("select[name=other_select]"))

    option_values = {
        option.get_attribute("value")
        for option in page.locator("select[name=other_select] option").all()
    }

    assert option_values == {"t", "w", "o"}


def test_tab(live_server, page, model):
    page.goto(live_server.url + "/new")

    expect(page.locator("input[name=tab_field]")).not_to_be_visible()

    page.get_by_text("Tab link").click()
    expect(page.locator("input[name=tab_field]")).to_be_visible()

    # go to tab
    page.fill('input[name="tab_field"]', "tab")
    page.locator("#submit-form").click()

    assert model.objects.count() == 1
    assert model.objects.first().tab_field == "tab"


def test_formset(live_server, page, model):
    page.goto(live_server.url + "/new")

    # show for formset
    page.select_option("select", "formset")

    # min num
    expect(
        page.locator('[data-pw="formset-test_formset-remove"]').first
    ).to_be_disabled()
    expect(page.get_by_text("Add new")).not_to_be_disabled()

    # add
    page.locator('input[name="test_formset-0-key"]').fill("key0")

    page.get_by_text("Add new").click()
    page.locator('input[name="test_formset-1-key"]').fill("key1")

    page.locator("#submit-form").click()

    assert model.objects.count() == 1
    test_model = model.objects.first()
    assert test_model.test_formset.count() == 2
    assert {t.key for t in test_model.test_formset.all()} == {"key0", "key1"}

    # delete (server and client side)
    # including invalid fields in deleted elements

    page.goto(live_server.url + "/1/update")

    page.get_by_text("Add new").click()
    page.get_by_text("Add new").click()

    # max_num
    expect(page.get_by_text("Add new")).to_be_disabled()
    expect(
        page.locator('[data-pw="formset-test_formset-remove"]').first
    ).not_to_be_disabled()

    # requires server deletion, including empty required field
    page.locator('input[name="test_formset-0-key"]').fill("")
    server_deletion = page.locator('[data-pw="formset-test_formset-remove"]').first
    server_deletion.click()
    expect(server_deletion).not_to_be_visible()

    # client deletion
    client_deletion = page.locator('[data-pw="formset-test_formset-remove"]').nth(2)
    client_deletion.click()
    expect(client_deletion).not_to_be_visible()

    page.locator('input[name="test_formset-1-key"]').fill("key10")  # update
    page.locator('input[name="test_formset-3-key"]').fill("key3")  # new

    page.locator("#submit-form").click()

    assert model.objects.count() == 1
    assert model.objects.first().test_formset.count() == 2
    assert {t.key for t in test_model.test_formset.all()} == {"key3", "key10"}
