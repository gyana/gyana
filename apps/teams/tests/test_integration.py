import pytest
from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertNotFound,
    assertOK,
    assertSelectorText,
)
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
    r = client.get(f"/teams/{team.id}")
    assertOK(r)
    assertLink(r, f"/teams/new", "New Team")

    # create

    r = client.get("/teams/new")
    assertOK(r)
    assertFormRenders(r, ["name"])

    r = client.post("/teams/new", data={"name": "Neera"})
    assert logged_in_user.teams.count() == 2
    new_team = logged_in_user.teams.first()
    assertRedirects(r, f"/teams/{new_team.id}/plan", status_code=303)

    assert bigquery_client.create_dataset.call_count == 1
    assert bigquery_client.create_dataset.call_args.args == (
        new_team.tables_dataset_id,
    )

    # choose plan
    r = client.get(f"/teams/{new_team.id}/plan")
    assertOK(r)
    assertLink(r, f"/teams/{new_team.id}", "Choose plan")

    # read
    r = client.get(f"/teams/{new_team.id}")
    assertOK(r)
    assertSelectorText(r, "#heading", "Neera")
    assertLink(r, f"/teams/{new_team.id}/update", "Settings")

    # current team in session
    assertRedirects(client.get("/"), f"/teams/{new_team.id}")
    client.get(f"/teams/{team.id}")
    assertRedirects(client.get("/"), f"/teams/{team.id}")

    # list -> NA

    # update
    r = client.get(f"/teams/{new_team.id}/update")
    assertOK(r)
    assertFormRenders(r, ["icon", "name"])

    r = client.post(f"/teams/{new_team.id}/update", data={"name": "Agni"})
    assertRedirects(r, f"/teams/{new_team.id}/update", status_code=303)
    new_team.refresh_from_db()
    assert new_team.name == "Agni"

    # delete
    r = client.get(f"/teams/{new_team.id}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"/teams/{new_team.id}/delete")
    assertRedirects(r, "/", target_status_code=302)

    assert bigquery_client.delete_dataset.call_count == 1
    assert bigquery_client.delete_dataset.call_args.args == (
        new_team.tables_dataset_id,
    )

    assert logged_in_user.teams.count() == 1


def test_member_crudl(client, logged_in_user):

    team = logged_in_user.teams.first()
    user = CustomUser.objects.create_user(
        "member", email="member@gyana.com", onboarded=True
    )
    team.members.add(user, through_defaults={"role": "admin"})
    membership = user.membership_set.first()

    # create -> invites
    # read -> NA

    # list
    r = client.get(f"/teams/{team.id}")
    assertLink(r, f"/teams/{team.id}/members/", "Members")

    r = client.get(f"/teams/{team.id}/members/")
    assertOK(r)
    assertLink(
        r, f"/teams/{team.id}/members/{membership.id}/update", "member@gyana.com"
    )

    # update
    r = client.get(f"/teams/{team.id}/members/{membership.id}/update")
    assertOK(r)
    assertFormRenders(r, ["role"])
    assertLink(r, f"/teams/{team.id}/members/{membership.id}/delete", "Delete")

    r = client.post(
        f"/teams/{team.id}/members/{membership.id}/update", data={"role": "member"}
    )
    assertRedirects(r, f"/teams/{team.id}/members/", status_code=303)
    membership.refresh_from_db()
    assert membership.role == "member"

    # delete
    r = client.get(f"/teams/{team.id}/members/{membership.id}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"/teams/{team.id}/members/{membership.id}/delete")
    assertRedirects(r, f"/teams/{team.id}/members/")

    assert team.members.count() == 1


def test_member_role_and_check_restricted_permissions(client, logged_in_user):

    team = logged_in_user.teams.first()

    assertOK(client.get(f"/teams/{team.id}/members/"))
    assertOK(client.get(f"/teams/{team.id}/invites/"))
    assertOK(client.get(f"/teams/{team.id}/update"))

    # add a member
    user = CustomUser.objects.create_user("member", onboarded=True)
    team.members.add(user, through_defaults={"role": "member"})
    client.force_login(user)

    assertNotFound(client.get(f"/teams/{team.id}/members/"))
    assertNotFound(client.get(f"/teams/{team.id}/invites/"))
    assertNotFound(client.get(f"/teams/{team.id}/update"))


def test_account_limit_warning_and_disabled(client):
    team = Team.objects.create(name="team_team", override_row_limit=10)
    project = Project.objects.create(name="Project", team=team)
    user = CustomUser.objects.create_user("test", onboarded=True)
    team.members.add(user, through_defaults={"role": "admin"})
    client.force_login(user)

    assertOK(client.get(f"/projects/{project.id}/integrations/connectors/new"))
    assertOK(client.get(f"/projects/{project.id}/integrations/sheets/new"))
    assertOK(client.get(f"/projects/{project.id}/integrations/uploads/new"))

    assert team.enabled
    assert not team.warning

    team.row_count = 12
    team.save()
    assert team.warning
    assert team.enabled

    team.row_count = 15
    team.save()
    assert not team.enabled

    assertNotFound(client.get(f"/projects/{project.id}/integrations/connectors/new"))
    assertNotFound(client.get(f"/projects/{project.id}/integrations/sheets/new"))
    assertNotFound(client.get(f"/projects/{project.id}/integrations/uploads/new"))
