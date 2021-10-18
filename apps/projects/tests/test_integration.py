import pytest
from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)
from apps.users.models import CustomUser
from pytest_django.asserts import assertContains, assertRedirects

pytestmark = pytest.mark.django_db


def test_project_crudl(client, logged_in_user):
    team = logged_in_user.teams.first()

    # create
    r = client.get_turbo_frame(f"/teams/{team.id}", f"/teams/{team.id}/templates/")
    assertLink(r, f"/teams/{team.id}/projects/new", "New Project")

    r = client.get(f"/teams/{team.id}/projects/new")
    assertOK(r)
    assertFormRenders(r, ["name", "description", "access", "cname"])

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
    assertSelectorLength(r, "table tbody tr", 1)
    assertLink(r, f"/projects/{project.id}", "Metrics")

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
    assertRedirects(r, f"/projects/{project.id}", status_code=303)

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
    assertFormRenders(r, ["name", "description", "access", "members", "cname"])

    # create private project
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
    assertSelectorLength(client.get(f"/teams/{team.id}"), "table tbody tr", 1)
    assertOK(client.get(f"/projects/{project.id}"))

    # validate forbidden
    client.force_login(other_user)
    assertSelectorLength(client.get(f"/teams/{team.id}"), "table tbody tr", 0)
    assert client.get(f"/projects/{project.id}").status_code == 404
