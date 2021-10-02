import pytest
from pytest_django.asserts import assertRedirects

pytestmark = pytest.mark.django_db


def test_team_crudl(client, logged_in_user):
    team = logged_in_user.teams.first()

    # redirect
    assertRedirects(client.get("/"), f"/teams/{team.id}")

    # create
    assert client.get("/teams/new").status_code == 200

    r = client.post("/teams/new", data={"name": "Neera"})
    assert r.status_code == 303
    assert logged_in_user.teams.count() == 2
    new_team = logged_in_user.teams.first()
    assert r.url == f"/teams/{new_team.id}"

    # read
    assert client.get(f"/teams/{new_team.id}").status_code == 200

    # current team in session
    assertRedirects(client.get("/"), f"/teams/{new_team.id}")
    client.get(f"/teams/{team.id}")
    assertRedirects(client.get("/"), f"/teams/{team.id}")

    # update
    assert client.get(f"/teams/{new_team.id}/update").status_code == 200

    r = client.post(f"/teams/{new_team.id}/update", data={"name": "Agni"})
    assert r.status_code == 303
    assert r.url == f"/teams/{new_team.id}/update"
    new_team.refresh_from_db()
    assert new_team.name == "Agni"

    # delete
    assert client.get(f"/teams/{new_team.id}/delete").status_code == 200

    r = client.delete(f"/teams/{new_team.id}/delete")
    r.status_code == 302
    r.url == "/"

    assert logged_in_user.teams.count() == 1
