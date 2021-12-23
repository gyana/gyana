from datetime import time

import pytest
from django.utils import timezone
from pytest_django.asserts import assertContains, assertRedirects

from apps.appsumo.models import AppsumoCode
from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorHasAttribute,
    assertSelectorLength,
    assertSelectorText,
)
from apps.users.models import CustomUser

pytestmark = pytest.mark.django_db


def test_project_crudl(client, logged_in_user):
    team = logged_in_user.teams.first()

    # create
    r = client.get(f"/teams/{team.id}")
    # zero state link
    assertLink(r, f"/teams/{team.id}/projects/new", "Create a new project")

    r = client.get(f"/teams/{team.id}/projects/new")
    assertOK(r)
    assertFormRenders(r, ["name", "description", "access"])

    r = client.post(
        f"/teams/{team.id}/projects/new",
        data={
            "name": "Metrics",
            "description": "All the company metrics",
            "access": "everyone",
            "submit": True,
        },
    )
    project = team.project_set.first()
    assert project is not None
    assertRedirects(r, f"/projects/{project.id}", status_code=303)

    # read
    r = client.get(f"/projects/{project.id}")
    assertOK(r)
    assertContains(r, "Metrics")
    assertContains(r, "All the company metrics")
    assertLink(r, f"/projects/{project.id}/update", "Settings")

    # list
    r = client.get(f"/teams/{team.id}")
    assertOK(r)
    assertLink(r, f"/projects/{project.id}", "Metrics")
    # normal link
    assertLink(r, f"/teams/{team.id}/projects/new", "New Project")

    # update
    r = client.get(f"/projects/{project.id}/update")
    assertOK(r)
    assertFormRenders(r, ["name", "description", "access", "cname"])
    assertLink(r, f"/projects/{project.id}/delete", "Delete")

    r = client.post(
        f"/projects/{project.id}/update",
        data={
            "name": "KPIs",
            "description": "All the company kpis",
            "access": "everyone",
            "submit": True,
        },
    )
    assertRedirects(r, f"/projects/{project.id}/update", status_code=303)

    project.refresh_from_db()
    assert project.name == "KPIs"

    # delete
    r = client.get(f"/projects/{project.id}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"/projects/{project.id}/delete")
    assertRedirects(r, f"/teams/{team.id}")

    assert team.project_set.first() is None


def test_private_projects(client, logged_in_user):
    team = logged_in_user.teams.first()

    other_user = CustomUser.objects.create_user("other user")
    team.members.add(other_user, through_defaults={"role": "admin"})

    # live fields
    r = client.post(
        f"/teams/{team.id}/projects/new",
        data={
            "name": "Metrics",
            "description": "All the company metrics",
            "access": "invite",
        },
    )
    assertFormRenders(r, ["name", "description", "access", "members"])
    assertSelectorHasAttribute(r, "#id_access", "disabled")

    # create private project that is rejected because user is on free tier
    r = client.post(
        f"/teams/{team.id}/projects/new",
        data={
            "name": "Metrics",
            "description": "All the company metrics",
            "access": "invite",
            "members": [logged_in_user.id],
            "submit": True,
        },
    )

    assert r.status_code == 422
    project = team.project_set.first()
    assert project is None

    # upgrade user
    AppsumoCode.objects.create(code="12345678", team=team, redeemed=timezone.now())
    AppsumoCode.objects.create(code="12345679", team=team, redeemed=timezone.now())

    r = client.post(
        f"/teams/{team.id}/projects/new",
        data={
            "name": "Metrics",
            "description": "All the company metrics",
            "access": "invite",
            "members": [logged_in_user.id],
            "submit": True,
        },
    )

    project = team.project_set.first()
    assert project is not None

    # validate access
    assertOK(client.get(f"/projects/{project.id}"))

    # validate forbidden
    client.force_login(other_user)
    assertSelectorLength(client.get(f"/teams/{team.id}"), "table tbody tr", 0)
    assert client.get(f"/projects/{project.id}").status_code == 404


def test_free_tier_project_limit(client, logged_in_user, project_factory):
    # Create 3 projects
    team = logged_in_user.teams.first()
    project_factory.create_batch(3, team=team)

    r = client.get(f"/teams/{team.id}")
    assertSelectorText(
        r,
        "#new-project",
        "You have reached the maximum number of projects on your current plan.",
    )
    r = client.post(
        f"/teams/{team.id}/projects/new",
        data={
            "name": "Metrics",
            "access": "everyone",
        },
    )
    assert r.status_code == 422


def test_automate(client, logged_in_user, project_factory, graph_run_factory, is_paid):

    team = logged_in_user.teams.first()
    project = project_factory(team=team)
    graph_run_factory.create_batch(3, project=project)

    r = client.get(f"/projects/{project.id}/automate")
    assertOK(r)

    r = client.get(f"/projects/{project.id}/runs")
    assertOK(r)
    assertFormRenders(r, ["daily_schedule_time"])
    assertSelectorLength(r, "table tbody tr", 3)

    r = client.post(
        f"/projects/{project.id}/runs", data={"daily_schedule_time": "06:00"}
    )
    assertRedirects(r, f"/projects/{project.id}/runs", status_code=303)

    project.refresh_from_db()
    print(project.daily_schedule_time)
    assert project.daily_schedule_time.hour == 6
