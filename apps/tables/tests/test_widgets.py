import pytest
from playwright.sync_api import expect

from apps.widgets.forms import WidgetSourceForm
from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db


def test_table_select_basic(
    project,
    dashboard_factory,
    integration_table_factory,
    widget_factory,
    pwf,
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

    pwf.render(form)
    # required for search
    pwf.page.force_login(live_server)

    # initial load

    # 2x used in + 5x most recent
    expect(pwf.page.locator("label.checkbox")).to_have_count(7)

    for idx in range(2):
        el = pwf.page.locator("label.checkbox").nth(idx)
        expect(el).to_contain_text(f"Used in {idx}")
        expect(el).to_contain_text("Used in this dashboard")

    for idx in range(5):
        el = pwf.page.locator("label.checkbox").nth(idx + 2)
        expect(el).to_contain_text(f"Other table {idx}")
        expect(el).not_to_contain_text("Used in this dashboard")

    # select option

    option = pwf.page.locator("label.checkbox").nth(0)
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

    pwf.page.locator("input[type=text]").press_sequentially("Search")

    pwf.page.pause()

    # 1x selected + 5x search results
    expect(pwf.page.locator("label.checkbox")).to_have_count(6)

    option = pwf.page.locator("label.checkbox").nth(0)
    expect(option).to_contain_text("Used in 0")
    expect(option.locator("input")).to_be_checked()
    expect(option).to_have_class(
        "checkbox checkbox--radio checkbox--icon checkbox--checked"
    )

    for idx in range(5):
        el = pwf.page.locator("label.checkbox").nth(idx + 1)
        expect(el).to_contain_text(f"Search table {idx}")

    # select another option

    option = pwf.page.locator("label.checkbox").nth(3)

    expect(option.locator("input")).not_to_be_checked()
    expect(option).not_to_have_class(
        "checkbox checkbox--radio checkbox--icon checkbox--checked"
    )

    option.click()

    expect(option.locator("input")).to_be_checked()
    expect(option).to_have_class(
        "checkbox checkbox--radio checkbox--icon checkbox--checked"
    )
