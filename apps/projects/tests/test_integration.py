import pytest

pytestmark = pytest.mark.django_db


def test_project_crudl(client, logged_in_user):
    team = logged_in_user.teams.first()

    # create
    assert client.get(f"/teams/{team.id}/projects/new").status_code == 200

    r = client.post(
        f"/teams/{team.id}/projects/new",
        data={
            "name": "Metrics",
            "description": "All the company metrics",
            "submit": True,
        },
    )
    assert r.status_code == 303
    project = team.project_set.first()
    assert project is not None
    assert r.url == f"/projects/{project.id}"

    # read
    assert client.get(f"/projects/{project.id}").status_code == 200

    # list
    assert client.get(f"/teams/{team.id}").status_code == 200

    # update
    assert client.get(f"/projects/{project.id}/update").status_code == 200
    r = client.post(
        f"/projects/{project.id}/update",
        data={
            "name": "KPIs",
            "description": "All the company kpis",
            "submit": True,
        },
    )
    assert r.status_code == 303
    assert r.url == f"/projects/{project.id}"

    # delete
    assert client.get(f"/projects/{project.id}/delete").status_code == 200

    r = client.delete(f"/projects/{project.id}/delete")
    assert r.status_code == 302
    assert r.url == f"/teams/{team.id}"

    assert team.project_set.first() is None
