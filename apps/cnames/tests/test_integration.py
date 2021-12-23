from unittest import mock
from uuid import uuid4

import pytest
from django.utils import timezone
from pytest_django.asserts import assertFormError, assertRedirects

from apps.appsumo.models import AppsumoCode
from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
    assertSelectorText,
)
from apps.dashboards.models import Dashboard
from apps.teams.models import Team

pytestmark = pytest.mark.django_db


can_create_cname = mock.patch.object(Team, "can_create_cname", True)


def test_cname_crudl(client, logged_in_user, heroku):
    team = logged_in_user.teams.first()

    heroku.get_domain().acm_status = "waiting"
    heroku.reset_mock()

    # User on free plan can't create custom domain
    r = client.get_turbo_frame(f"/teams/{team.id}/update", f"/teams/{team.id}/cnames/")
    assertOK(r)
    assertSelectorText(
        r, "p", "You cannot create more custom domains on your current plan."
    )

    r = client.get(f"/teams/{team.id}/cnames/new")
    assertOK(r)
    assertFormRenders(r, ["domain"])

    r = client.post(f"/teams/{team.id}/cnames/new", data={"domain": "test.domain.com"})
    assert r.status_code == 422

    # upgrade user
    AppsumoCode.objects.create(code="12345678", team=team, redeemed=timezone.now())
    AppsumoCode.objects.create(code="12345679", team=team, redeemed=timezone.now())

    r = client.get_turbo_frame(f"/teams/{team.id}/update", f"/teams/{team.id}/cnames/")
    assertOK(r)
    assertLink(r, f"/teams/{team.id}/cnames/new", "create one")

    r = client.post(f"/teams/{team.id}/cnames/new", data={"domain": "test.domain.com"})
    assertRedirects(r, f"/teams/{team.id}/update", status_code=303)

    assert team.cname_set.count() == 1
    cname = team.cname_set.first()
    cname.domain == "test.domain.com"
    assert heroku.add_domain.call_count == 1
    assert heroku.add_domain.call_args.args == ("test.domain.com", None)

    # read and update not enabled

    # list
    r = client.get_turbo_frame(f"/teams/{team.id}/update", f"/teams/{team.id}/cnames/")
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 1)
    assertLink(r, f"/teams/{team.id}/cnames/{cname.id}/delete", title="Delete CNAME")

    # status indicator
    r = client.get_turbo_frame(
        f"/teams/{team.id}/update",
        f"/teams/{team.id}/cnames/",
        f"/cnames/{cname.id}/status",
    )
    assertSelectorLength(r, ".fa-spinner-third", 1)
    assert heroku.get_domain.call_count == 1
    assert heroku.get_domain.call_args.args == ("test.domain.com",)

    heroku.get_domain().acm_status = "cert issued"
    heroku.reset_mock()
    r = client.get_turbo_frame(
        f"/teams/{team.id}/update",
        f"/teams/{team.id}/cnames/",
        f"/cnames/{cname.id}/status",
    )
    assertOK(r)
    assertSelectorLength(r, ".fa-check", 1)
    assert heroku.get_domain.call_count == 1
    assert heroku.get_domain.call_args.args == ("test.domain.com",)

    # delete
    heroku.reset_mock()
    r = client.get(f"/teams/{team.id}/cnames/{cname.id}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"/teams/{team.id}/cnames/{cname.id}/delete")
    assertRedirects(r, f"/teams/{team.id}/update")

    assert team.cname_set.count() == 0
    assert heroku.get_domain.call_count == 1
    assert heroku.get_domain.call_args.args == ("test.domain.com",)
    assert heroku.get_domain().remove.call_count == 1


@can_create_cname
def test_cname_validation(client, logged_in_user, c_name_factory):
    team = logged_in_user.teams.first()
    c_name_factory(team=team)

    # domain regex
    r = client.post(f"/teams/{team.id}/cnames/new", data={"domain": "not-a-domain"})
    assertFormError(r, "form", "domain", "Must be a valid domain")

    # unique
    r = client.post(f"/teams/{team.id}/cnames/new", data={"domain": "test.domain.com"})
    ERROR = "A CNAME with this domain already exists. If you think this is a mistake, reach out to support and we'll sort it out for you."
    assertFormError(r, "form", "domain", ERROR)


@can_create_cname
def test_cname_middleware_for_public_dashboard(
    client,
    logged_in_user,
    c_name_factory,
    dashboard_factory,
    widget_factory,
    control_factory,
):
    team = logged_in_user.teams.first()
    cname = c_name_factory(team=team)
    dashboard = dashboard_factory(
        project__team=team,
        shared_status=Dashboard.SharedStatus.PUBLIC,
        shared_id=uuid4(),
    )
    widget = widget_factory(page__dashboard=dashboard)
    other_dashboard = dashboard_factory(
        project__team=team,
        shared_status=Dashboard.SharedStatus.PUBLIC,
        shared_id=uuid4(),
    )
    project = dashboard.project

    SHARED = f"/dashboards/{dashboard.shared_id}"

    # update a project to use a cname
    r = client.get(f"/projects/{project.id}/update")
    assertOK(r)
    assertFormRenders(r, ["name", "description", "access", "cname"])

    r = client.post(
        f"/projects/{project.id}/update",
        data={
            "name": "Project",
            "access": "everyone",
            "cname": cname.id,
            "submit": True,
        },
    )
    assertRedirects(r, f"/projects/{project.id}/update", status_code=303)

    # public dashboard on our domain
    r = client.get(SHARED)
    assertOK(r)

    # public dashboard on custom domain
    r = client.get(SHARED, HTTP_HOST="test.domain.com")
    assertOK(r)

    # individual widget output
    r = client.get(
        f"/projects/{project.id}/dashboards/{dashboard.id}/widgets/{widget.id}/output",
        HTTP_HOST="test.domain.com",
    )
    assertOK(r)

    # access control public update
    control = control_factory(page=dashboard.pages.first())
    r = client.get(
        f"/projects/{project.id}/dashboards/{dashboard.id}/controls/{control.id}/update-public",
        HTTP_HOST="test.domain.com",
    )
    assertOK(r)

    # incorrect domain fails
    r = client.get(SHARED, HTTP_HOST="wrong.domain.com")
    assert r.status_code == 403

    # incorrect project fails
    r = client.get(
        f"/dashboards/{other_dashboard.shared_id}", HTTP_HOST="test.domain.com"
    )
    assert r.status_code == 403


@can_create_cname
def test_cname_middleware_for_password_protected_dashboard(
    client, logged_in_user, c_name_factory, dashboard_factory, widget_factory
):
    team = logged_in_user.teams.first()
    cname = c_name_factory(team=team)
    dashboard = dashboard_factory(
        project__team=team,
        project__cname=cname,
        shared_status=Dashboard.SharedStatus.PASSWORD_PROTECTED,
        password_set=timezone.now(),
        shared_id=uuid4(),
    )
    dashboard.pages.create()
    dashboard.set_password("seewhatmatters")
    dashboard.save()

    SHARED = f"/dashboards/{dashboard.shared_id}"

    r = client.get(f"{SHARED}/login", HTTP_HOST="test.domain.com")
    assertOK(r)

    r = client.post(
        f"{SHARED}/login",
        data={"password": "seewhatmatters"},
        HTTP_HOST="test.domain.com",
    )
    assertRedirects(r, SHARED)

    r = client.get(SHARED, HTTP_HOST="test.domain.com")
    assertOK(r)

    r = client.get(f"{SHARED}/logout", HTTP_HOST="test.domain.com")
    assertRedirects(r, f"{SHARED}/login")
