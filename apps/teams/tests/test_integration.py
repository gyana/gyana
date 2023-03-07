import pytest
from djpaddle.models import Plan
from pytest_django.asserts import assertContains, assertRedirects

from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertNotFound,
    assertNotLink,
    assertOK,
    assertSelectorLength,
    assertSelectorText,
)
from apps.base.tests.subscribe import upgrade_to_pro
from apps.teams.models import Team
from apps.users.models import CustomUser

pytestmark = pytest.mark.django_db


def test_team_crudl(client, logged_in_user, bigquery, flag_factory, settings):

    team = logged_in_user.teams.first()
    flag = flag_factory(name="beta")
    pro_plan = Plan.objects.create(name="Pro", billing_type="month", billing_period=1)
    settings.DJPADDLE_PRO_PLAN_ID = pro_plan.id
    # the fixture creates a new team
    bigquery.reset_mock()

    # redirect
    assertRedirects(client.get("/"), f"/teams/{team.id}")
    r = client.get(f"/teams/{team.id}")
    assertOK(r)
    assertLink(r, f"/teams/new")

    # create
    r = client.get("/teams/new")
    assertOK(r)
    assertFormRenders(r, ["name"])

    r = client.post("/teams/new", data={"name": "Neera"})
    assert logged_in_user.teams.count() == 2
    new_team = logged_in_user.teams.first()
    assertRedirects(r, f"/teams/{new_team.id}", status_code=302)

    assert bigquery.create_dataset.call_count == 1
    assert bigquery.create_dataset.call_args.args == (new_team.tables_dataset_id,)

    # read
    r = client.get(f"/teams/{new_team.id}")
    assertOK(r)
    assertSelectorText(r, "#heading", "Neera")
    assertLink(r, f"/teams/{new_team.id}/update", "Settings")

    # current team in session
    assertRedirects(client.get("/"), f"/teams/{new_team.id}")
    client.get(f"/teams/{team.id}")
    assertRedirects(client.get("/"), f"/teams/{team.id}")

    # switcher
    assertLink(r, f"/teams/{team.id}")

    # list -> NA

    # update
    r = client.get(f"/teams/{new_team.id}/update")
    assertOK(r)
    assertFormRenders(r, ["icon", "name", "color", "timezone", "beta"])

    r = client.post(
        f"/teams/{new_team.id}/update",
        data={"name": "Agni", "timezone": "Asia/Kolkata", "beta": True},
    )
    assertRedirects(r, f"/teams/{new_team.id}/update", status_code=303)
    new_team.refresh_from_db()
    assert new_team.name == "Agni"
    assert str(new_team.timezone) == "Asia/Kolkata"
    assert new_team in flag.teams.all()

    # remove from beta
    r = client.post(
        f"/teams/{new_team.id}/update",
        data={"name": "Agni", "timezone": "Asia/Kolkata", "beta": False},
    )
    assert new_team not in flag.teams.all()

    # delete
    r = client.get(f"/teams/{new_team.id}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"/teams/{new_team.id}/delete")
    assertRedirects(r, "/", target_status_code=302)

    # Does a soft delete
    assert bigquery.delete_dataset.call_count == 0

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

    MEMBERSHIP_URL = f"/teams/{team.id}/members/{membership.id}"

    # list
    r = client.get(f"/teams/{team.id}")
    assertLink(r, f"/teams/{team.id}/members/", "Members")

    r = client.get(f"/teams/{team.id}/members/")
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 2)
    assertLink(r, f"{MEMBERSHIP_URL}/update", "member@gyana.com")

    # update
    r = client.get(f"{MEMBERSHIP_URL}/update")
    assertOK(r)
    assertFormRenders(r, ["role"])
    assertLink(r, f"{MEMBERSHIP_URL}/delete", "Delete")

    r = client.post(f"{MEMBERSHIP_URL}/update", data={"role": "member"})
    assertRedirects(r, f"/teams/{team.id}/members/", status_code=303)
    membership.refresh_from_db()
    assert membership.role == "member"

    # delete
    r = client.get(f"{MEMBERSHIP_URL}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"{MEMBERSHIP_URL}/delete")
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


def test_account_limit_warning_and_disabled(client, project_factory):
    team = Team.objects.create(name="team_team", override_row_limit=10)
    project = project_factory(team=team)
    user = CustomUser.objects.create_user("test", onboarded=True)
    team.members.add(user, through_defaults={"role": "admin"})
    client.force_login(user)

    # TODO: Put back in once we have connectors again
    # assertOK(client.get(f"/projects/{project.id}/integrations/connectors/new"))
    assertOK(client.get(f"/projects/{project.id}/integrations/sheets/new"))
    assertOK(client.get(f"/projects/{project.id}/integrations/uploads/new"))

    assert team.enabled
    assert not team.warning

    team.row_count = 12
    team.save()
    assert team.warning
    assert team.enabled

    r = client.get(f"/teams/{team.id}")
    assertOK(r)
    assertContains(r, "You've exceeded your row count limit.")

    team.row_count = 15
    team.save()
    assert not team.enabled

    r = client.get(f"/teams/{team.id}")
    assertOK(r)
    assertContains(r, "You've exceeded your row count limit by over 20%")

    # TODO: Put back in once we have connectors again
    # assertNotFound(client.get(f"/projects/{project.id}/integrations/connectors/new"))
    assertNotFound(client.get(f"/projects/{project.id}/integrations/sheets/new"))
    assertNotFound(client.get(f"/projects/{project.id}/integrations/uploads/new"))


def test_pro_upgrade_with_limits(client, logged_in_user, settings, project_factory):

    team = logged_in_user.teams.first()
    pro_plan = Plan.objects.create(name="Pro", billing_type="month", billing_period=1)
    settings.DJPADDLE_PRO_PLAN_ID = pro_plan.id

    project = project_factory(team=team)

    LIST = f"/projects/{project.id}/integrations"

    # free tier have no access to connector and custom API

    r = client.get(f"{LIST}/")
    assertOK(r)
    assertNotLink(r, f"{LIST}/connectors/new", "Add a connector")
    assertNotLink(r, f"{LIST}/connectors/customapi", "Use a Custom API")

    upgrade_to_pro(logged_in_user, team, pro_plan)

    # zero state
    r = client.get(f"{LIST}/")

    assertLink(r, f"{LIST}/customapis/new", "Use a Custom API")

    # dropdown
    r = client.get(f"{LIST}/")
    # assertLink(r, f"{LIST}/connectors/new", "New Connector")
    assertLink(r, f"{LIST}/customapis/new", "Custom API")
