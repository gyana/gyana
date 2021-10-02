import pytest
from apps.users.models import CustomUser
from bs4 import BeautifulSoup
from pytest_django.asserts import assertContains

pytestmark = pytest.mark.django_db


def assertLink(response, url, text):
    soup = BeautifulSoup(response.content)
    matches = soup.select(f'a[href="{url}"]')

    assert len(matches) == 1
    assert text in matches[0].text


def get_selector(response, selector):
    soup = BeautifulSoup(response.content)
    return soup.select(selector)


def test_project_crudl(client, logged_in_user):
    team = logged_in_user.teams.first()

    # create
    assertLink(
        client.get_turbo_frame(f"/teams/{team.id}", f"/teams/{team.id}/templates/"),
        f"/teams/{team.id}/projects/new",
        "New Project",
    )

    assert client.get(f"/teams/{team.id}/projects/new").status_code == 200

    r = client.post(
        f"/teams/{team.id}/projects/new",
        data={
            "name": "Metrics",
            "description": "All the company metrics",
            "access": "everyone",
            "submit": True,
        },
    )
    assert r.status_code == 303
    project = team.project_set.first()
    assert project is not None
    assert r.url == f"/projects/{project.id}"

    # read
    r = client.get(f"/projects/{project.id}")
    assert r.status_code == 200
    assertContains(r, "Metrics")
    assertContains(r, "All the company metrics")
    assertLink(r, f"/projects/{project.id}/update", "Settings")

    # list
    r = client.get(f"/teams/{team.id}")
    assert r.status_code == 200
    assert len(get_selector(r, "table tbody tr")) == 1
    assertLink(r, f"/projects/{project.id}", "Metrics")

    # update
    r = client.get(f"/projects/{project.id}/update")
    assert r.status_code == 200
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
    assert r.status_code == 303
    assert r.url == f"/projects/{project.id}"
    project.refresh_from_db()
    assert project.name == "KPIs"

    # delete
    assert client.get(f"/projects/{project.id}/delete").status_code == 200

    r = client.delete(f"/projects/{project.id}/delete")
    assert r.status_code == 302
    assert r.url == f"/teams/{team.id}"

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
    assert "members" in r.context["form"].fields

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

    # validate access
    project = team.project_set.first()
    assert project is not None
    assert client.get(f"/projects/{project.id}").status_code == 200

    # validate forbidden
    client.force_login(other_user)
    assert client.get(f"/projects/{project.id}").status_code == 404
