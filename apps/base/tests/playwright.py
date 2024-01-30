import pytest
from django import forms
from django.template.loader import render_to_string

from apps.base.alpine import ibis_store

pytestmark = pytest.mark.django_db


class PlaywrightForm:
    def __init__(self, page, dynamic_view, live_server):
        self.page = page
        self.dynamic_view = dynamic_view
        self.live_server = live_server
        self.page.set_default_timeout(1000)

    def render(self, content):
        if isinstance(content, forms.BaseForm):
            html = render_to_string(
                "test/form.html", {"form": content, "ibis_store": ibis_store}
            )
        else:
            html = render_to_string(
                "test/integration.html",
                {"content": content.decode("utf-8"), "ibis_store": ibis_store},
            )
        dynamic_url = self.dynamic_view(html)
        self.page.goto(self.live_server.url + dynamic_url)

    def select_value(self, name, value):
        self.page.select_option(f"select[name={name}]", value)

    def assert_fields(self, expected):
        field_names = {
            el.get_attribute("name")
            for el in self.page.locator(
                "form input,select,textarea,gy-select-autocomplete"
            ).all()
            if "-" not in el.get_attribute("name")  # exclude formsets
        } - {"csrfmiddlewaretoken"}
        assert field_names == set(expected), f"{field_names} != {set(expected)}"

    def assert_formsets(self, expected):
        prefixes = {
            el.get_attribute("name").split("-")[0]
            for el in self.page.locator("form input[name$=-TOTAL_FORMS]").all()
        }
        assert prefixes == set(expected), f"{prefixes} != {set(expected)}"

    def assert_select_options_length(self, name, expected):
        options = self.page.locator(f"select[name={name}] option").all()
        assert len(options) == expected, f"{len(options)} != {expected}"

    def assert_select_options(self, name, expected):
        options = self.page.locator(f"select[name={name}] option").all()
        assert len(options) == len(expected), f"{len(options)} != {len(expected)}"

        option_values = {
            option.get_attribute("value")
            for option in self.page.locator("select[name=function] option").all()
        }
        assert option_values == set(expected), f"{option_values} != {set(expected)}"
