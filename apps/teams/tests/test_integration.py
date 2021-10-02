import pytest
from apps.projects.models import Project
from apps.teams.models import Team
from apps.users.models import CustomUser
from pytest_django.asserts import assertRedirects

pytestmark = pytest.mark.django_db


def test_team_crudl(client, logged_in_user, bigquery_client, settings):
    settings.MOCK_REMOTE_OBJECT_DELETION = False
    bigquery_client.reset_mock()
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

    assert bigquery_client.create_dataset.call_count == 1
    assert bigquery_client.create_dataset.call_args.args == (
        new_team.tables_dataset_id,
    )

    # read
    assert client.get(f"/teams/{new_team.id}").status_code == 200

    # current team in session
    assertRedirects(client.get("/"), f"/teams/{new_team.id}")
    client.get(f"/teams/{team.id}")
    assertRedirects(client.get("/"), f"/teams/{team.id}")

    # list -> NA

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

    assert bigquery_client.delete_dataset.call_count == 1
    assert bigquery_client.delete_dataset.call_args.args == (
        new_team.tables_dataset_id,
    )

    assert logged_in_user.teams.count() == 1


def test_member_crudl(client, logged_in_user):

    team = logged_in_user.teams.first()
    user = CustomUser.objects.create_user("member", onboarded=True)
    team.members.add(user, through_defaults={"role": "admin"})
    membership = user.membership_set.first()

    # create -> invites
    # read -> NA

    # list
    assert client.get(f"/teams/{team.id}/members/").status_code == 200

    # update
    assert (
        client.get(f"/teams/{team.id}/members/{membership.id}/update").status_code
        == 200
    )

    r = client.post(
        f"/teams/{team.id}/members/{membership.id}/update", data={"role": "member"}
    )
    r.status_code == "301"
    r.url == f"/teams/{team.id}/members/{membership.id}/update"
    membership.refresh_from_db()
    assert membership.role == "member"

    # delete
    client.get(f"/teams/{team.id}/members/{membership.id}/delete")

    r = client.delete(f"/teams/{team.id}/members/{membership.id}/delete")
    r.status_code == 301
    r.url == f"/teams/{team.id}/members"

    assert team.members.count() == 1


def test_member_role_and_check_restricted_permissions(client, logged_in_user):

    team = logged_in_user.teams.first()

    assert client.get(f"/teams/{team.id}/members/").status_code == 200
    assert client.get(f"/teams/{team.id}/invites/").status_code == 200
    assert client.get(f"/teams/{team.id}/update").status_code == 200

    # add a member
    user = CustomUser.objects.create_user("member", onboarded=True)
    team.members.add(user, through_defaults={"role": "member"})
    client.force_login(user)

    assert client.get(f"/teams/{team.id}/members/").status_code == 404
    assert client.get(f"/teams/{team.id}/invites/").status_code == 404
    assert client.get(f"/teams/{team.id}/update").status_code == 404


def test_account_limit_warning_and_disabled(client):
    team = Team.objects.create(name="team_team", override_row_limit=10)
    project = Project.objects.create(name="Project", team=team)
    user = CustomUser.objects.create_user("test", onboarded=True)
    team.members.add(user, through_defaults={"role": "admin"})
    client.force_login(user)

    assert (
        client.get(f"/projects/{project.id}/integrations/connectors/new").status_code
        == 200
    )
    assert (
        client.get(f"/projects/{project.id}/integrations/sheets/new").status_code == 200
    )
    assert (
        client.get(f"/projects/{project.id}/integrations/uploads/new").status_code
        == 200
    )

    assert team.enabled
    assert not team.warning

    team.row_count = 12
    team.save()
    assert team.warning
    assert team.enabled

    team.row_count = 15
    team.save()
    assert not team.enabled

    assert (
        client.get(f"/projects/{project.id}/integrations/connectors/new").status_code
        == 404
    )
    assert (
        client.get(f"/projects/{project.id}/integrations/sheets/new").status_code == 404
    )
    assert (
        client.get(f"/projects/{project.id}/integrations/uploads/new").status_code
        == 404
    )
