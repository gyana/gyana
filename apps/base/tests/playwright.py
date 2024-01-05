from django.template.loader import render_to_string

from apps.base.alpine import ibis_store


class PlaywrightForm:
    def __init__(self, page):
        self.page = page

    def render(self, form):
        html = render_to_string(
            "test/form.html", {"form": form, "ibis_store": ibis_store}
        )
        self.page.set_content(html)

    def select_value(self, name, value):
        self.page.select_option(f"select[name={name}]", value)

    def assert_fields(self, expected):
        field_names = {
            el.get_attribute("name")
            for el in self.page.locator("form input,select,textarea").all()
        }
        assert field_names == set(expected), f"{field_names} != {set(expected)}"

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
