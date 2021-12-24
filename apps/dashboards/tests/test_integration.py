from uuid import uuid4

import pytest
from pytest_django.asserts import assertContains, assertFormError, assertRedirects

from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)
from apps.dashboards.models import Dashboard

pytestmark = pytest.mark.django_db


def test_dashboard_crudl(client, project, dashboard_factory):

    LIST = f"/projects/{project.id}/dashboards"

    # zero state
    r = client.get(f"{LIST}/")
    assertOK(r)
    assertFormRenders(r, ["project"])
    assertContains(r, "Create a new dashboard")

    # create
    r = client.post(f"{LIST}/new", data={"project": project.id})
    dashboard = project.dashboard_set.first()
    assert dashboard is not None
    assert dashboard.pages.first() is not None
    DETAIL = f"{LIST}/{dashboard.id}"
    assertRedirects(r, DETAIL, status_code=303)

    # read
    r = client.get(DETAIL)
    assertOK(r)
    # TODO: Fix this
    assertFormRenders(r, ["name", "x", "y", "kind", "page"])
    assertLink(r, f"{DETAIL}/delete", "Delete")

    # update/rename
    new_name = "Superduper dashboard"
    r = client.post(DETAIL, data={"name": new_name})
    assertRedirects(r, DETAIL, status_code=303)
    dashboard.refresh_from_db()
    assert dashboard.name == new_name

    # add page
    r = client.post(f"{DETAIL}/pages/new")
    assertRedirects(r, f"{DETAIL}?page=2", status_code=302)
    page = dashboard.pages.last()
    assert page.position == 2

    r = client.get(r.url)
    assertOK(r)
    assertContains(r, "Page 2 of 2")

    # delete page
    r = client.delete(f"{DETAIL}/pages/{page.id}")
    assertRedirects(r, f"{DETAIL}?page=1", status_code=302)
    assert dashboard.pages.count() == 1

    # delete
    r = client.get(f"{DETAIL}/delete")
    assertOK(r)
    assertFormRenders(r)
    r = client.delete(f"{DETAIL}/delete")
    assertRedirects(r, f"{LIST}/")
    assert project.dashboard_set.first() is None

    # list with pagination
    dashboard_factory.create_batch(30, project=project)
    r = client.get(f"{LIST}/")
    assertOK(r)
    assertLink(r, f"{LIST}/?page=2", "2")
    r = client.get(f"{LIST}/?page=2")
    assertOK(r)


def test_dashboard_share(
    client, logged_in_user, project, dashboard_factory, widget_factory
):
    dashboard = dashboard_factory(project=project)
    widget = widget_factory(page__dashboard=dashboard)

    DETAIL = f"/projects/{project.id}/dashboards/{dashboard.id}"
    WIDGET = f"{DETAIL}/widgets/{widget.id}/output"

    # share a dashboard
    r = client.get(DETAIL)
    assertSelectorLength(r, f'button[data-modal-src="/dashboards/{dashboard.id}/share"]', 1)
    r = client.get(f"/dashboards/{dashboard.id}/share")
    assertOK(r)
    assertFormRenders(r, ["shared_status"])

    # public
    r = client.post(
        f"/dashboards/{dashboard.id}/share",
        data={"shared_status": Dashboard.SharedStatus.PUBLIC, "submit": True},
    )
    assertRedirects(r, f"/dashboards/{dashboard.id}/share", status_code=303)
    dashboard.refresh_from_db()
    assert dashboard.shared_id is not None
    PUBLIC = f"/dashboards/{dashboard.shared_id}"

    # check access
    client.logout()

    r = client.get(PUBLIC)
    assertOK(r)
    r = client.get(WIDGET)
    assertOK(r)

    # password protected
    client.force_login(logged_in_user)
    r = client.post(
        f"/dashboards/{dashboard.id}/share",
        data={"shared_status": Dashboard.SharedStatus.PASSWORD_PROTECTED},
    )
    assert r.status_code == 422
    assertFormRenders(r, ["shared_status", "password"])

    r = client.post(
        f"/dashboards/{dashboard.id}/share",
        data={
            "shared_status": Dashboard.SharedStatus.PASSWORD_PROTECTED,
            "password": "secret",
            "submit": True,
        },
    )
    assertRedirects(r, f"/dashboards/{dashboard.id}/share", status_code=303)

    # check access
    client.logout()

    r = client.get(PUBLIC)
    assertRedirects(r, f"{PUBLIC}/login")
    r = client.get(WIDGET)
    assert r.status_code == 404

    r = client.get(f"{PUBLIC}/login")
    assertOK(r)

    # wrong password
    r = client.post(f"{PUBLIC}/login", data={"password": "wrong"})
    assertFormError(r, "form", "password", "Wrong password")

    # right password
    r = client.post(f"{PUBLIC}/login", data={"password": "secret"})
    assertRedirects(r, PUBLIC)

    # access persists in session
    r = client.get(PUBLIC)
    assertOK(r)
    assertLink(r, f"{PUBLIC}/logout", "Forget me")
    r = client.get(WIDGET)
    assertOK(r)

    # logout
    r = client.get(f"{PUBLIC}/logout")
    assertRedirects(r, f"{PUBLIC}/login")

    # not accessible
    r = client.get(PUBLIC)
    assertRedirects(r, f"{PUBLIC}/login")
    r = client.get(WIDGET)
    assert r.status_code == 404

    # stop share
    client.force_login(logged_in_user)
    r = client.post(
        f"/dashboards/{dashboard.id}/share",
        data={"shared_status": Dashboard.SharedStatus.PRIVATE, "submit": True},
    )

    client.logout()
    r = client.get(PUBLIC)
    assert r.status_code == 404
    r = client.get(WIDGET)
    assert r.status_code == 404


def test_dashboard_duplication(
    client,
    project,
    dashboard_factory,
    widget_factory,
    integration_table_factory,
    filter_factory,
):
    name = "My dashboard"
    dashboard = dashboard_factory(project=project, name=name)
    table = integration_table_factory()
    widget = widget_factory(page__dashboard=dashboard, table=table)
    filter_ = filter_factory(widget=widget, column="My column")

    r = client.post(f"/dashboards/{dashboard.id}/duplicate")
    assert project.dashboard_set.count() == 2
    new_dashboard = project.dashboard_set.exclude(id=dashboard.id).first()

    assertRedirects(r, f"/projects/{project.id}/dashboards/", status_code=303)
    assert new_dashboard is not None
    assert new_dashboard.name == f"Copy of {name}"

    new_dashboard_page = new_dashboard.pages.first()
    assert new_dashboard_page.widgets.count() == 1
    new_widget = new_dashboard_page.widgets.first()

    # preserve name and table information
    assert new_widget.name == widget.name
    assert new_widget.table == widget.table

    # linked models are duplicated
    new_filter = new_widget.filters.first()
    assert new_filter is not None
    assert filter_ != new_filter
    assert filter_.column == new_filter.column
