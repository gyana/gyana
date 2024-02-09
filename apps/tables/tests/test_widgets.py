import pytest
from django.template import Context, RequestContext, Template
from playwright.sync_api import expect

from apps.base.alpine import ibis_store
from apps.widgets.forms import WidgetSourceForm
from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db

_template = """{% extends "web/base.html" %}{% load crispy_forms_tags %}{% block body %}
    <form>
    {% csrf_token %}
    {% crispy form %}
    </form>
{% endblock %}"""


def test_table_select_basic(
    project,
    dashboard_factory,
    integration_table_factory,
    widget_factory,
    page,
    dynamic_view,
    live_server,
    with_pg_trgm_extension,
):
    dashboard = dashboard_factory(project=project)
    widget = widget_factory(kind=Widget.Kind.TABLE, page__dashboard=dashboard)

    # other tables in the project
    for idx in range(10):
        table = integration_table_factory(
            project=project,
            integration__name=f"Other table {idx}",
            name=f"other_table_{idx}",
        )

    # searchable tables
    for idx in range(5):
        table = integration_table_factory(
            project=project,
            integration__name=f"Search table {idx}",
            name=f"search_table_{idx}",
        )

    # used in this dashboard
    for idx in range(2):
        table = integration_table_factory(
            project=project,
            integration__name=f"Used in {idx}",
            name=f"used_in_{idx}",
        )
        widget_factory(kind=Widget.Kind.TABLE, table=table, page=widget.page)

    form = WidgetSourceForm(instance=widget)

    html = Template(_template).render(Context({"form": form, "ibis_store": ibis_store}))
    dynamic_url = dynamic_view(html)
    page.goto(live_server.url + "/" + dynamic_url)
    # required for search
    page.force_login(live_server)

    # initial load

    # 2x used in + 5x most recent
    expect(page.locator("label.checkbox")).to_have_count(7)

    for idx in range(2):
        el = page.locator("label.checkbox").nth(idx)
        expect(el).to_contain_text(f"Used in {idx}")
        expect(el).to_contain_text("Used in this dashboard")

    for idx in range(5):
        el = page.locator("label.checkbox").nth(idx + 2)
        expect(el).to_contain_text(f"Other table {idx}")
        expect(el).not_to_contain_text("Used in this dashboard")

    # select option

    option = page.locator("label.checkbox").nth(0)
    expect(option.locator("input")).not_to_be_checked()
    expect(option).not_to_have_class(
        "checkbox checkbox--radio checkbox--icon checkbox--checked"
    )

    option.click()

    expect(option.locator("input")).to_be_checked()
    expect(option).to_have_class(
        "checkbox checkbox--radio checkbox--icon checkbox--checked"
    )

    # search

    page.locator("input[type=text]").press_sequentially("Search")

    # 1x selected + 5x search results
    expect(page.locator("label.checkbox")).to_have_count(6)

    option = page.locator("label.checkbox").nth(0)
    expect(option).to_contain_text("Used in 0")
    expect(option.locator("input")).to_be_checked()
    expect(option).to_have_class(
        "checkbox checkbox--radio checkbox--icon checkbox--checked"
    )

    for idx in range(5):
        el = page.locator("label.checkbox").nth(idx + 1)
        expect(el).to_contain_text(f"Search table {idx}")

    # select another option

    option = page.locator("label.checkbox").nth(3)

    expect(option.locator("input")).not_to_be_checked()
    expect(option).not_to_have_class(
        "checkbox checkbox--radio checkbox--icon checkbox--checked"
    )

    option.click()

    expect(option.locator("input")).to_be_checked()
    expect(option).to_have_class(
        "checkbox checkbox--radio checkbox--icon checkbox--checked"
    )
