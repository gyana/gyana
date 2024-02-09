import pytest
from playwright.sync_api import expect

from apps.users.models import CustomUser
from apps.widgets.forms import WidgetSourceForm
from apps.widgets.models import Widget

pytestmark = pytest.mark.django_db

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore


def create_session_cookie(user, live_server):
    session = SessionStore()
    session[SESSION_KEY] = user.pk
    session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()

    cookie = {
        "name": settings.SESSION_COOKIE_NAME,
        "value": session.session_key,
        "secure": False,
        "url": live_server.url,
    }
    return cookie


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

    user = CustomUser.objects.first()
    pwf.page.context.add_cookies([create_session_cookie(user, live_server)])

    # search

    pwf.page.locator("input[type=text]").press_sequentially("Search")

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
