from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone
from djpaddle.models import Checkout, Plan, Subscription
from pytest_django.asserts import assertContains, assertRedirects

from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertNotFound,
    assertOK,
    assertSelectorLength,
    assertSelectorText,
)
from apps.teams.models import Team
from apps.users.models import CustomUser

pytestmark = pytest.mark.django_db


def test_team_crudl(client, logged_in_user, bigquery):

    team = logged_in_user.teams.first()
    # the fixture creates a new team
    bigquery.reset_mock()

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

    assert bigquery.create_dataset.call_count == 1
    assert bigquery.create_dataset.call_args.args == (new_team.tables_dataset_id,)

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

    # switcher
    assertLink(r, f"/teams/{team.id}", "Vayu")

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

    assertOK(client.get(f"/projects/{project.id}/integrations/connectors/new"))
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
    assertContains(r, "You're exceeding your row count limit.")

    team.row_count = 15
    team.save()
    assert not team.enabled

    r = client.get(f"/teams/{team.id}")
    assertOK(r)
    assertContains(r, "You've exceeded your row count limit by over 20%")

    assertNotFound(client.get(f"/projects/{project.id}/integrations/connectors/new"))
    assertNotFound(client.get(f"/projects/{project.id}/integrations/sheets/new"))
    assertNotFound(client.get(f"/projects/{project.id}/integrations/uploads/new"))


def test_subscriptions(client, logged_in_user, settings):

    team = logged_in_user.teams.first()
    pro_plan = Plan.objects.create(name="Pro", billing_type="month", billing_period=1)
    business_plan = Plan.objects.create(
        name="Pro", billing_type="month", billing_period=1
    )

    settings.DJPADDLE_PRO_PLAN_ID = pro_plan.id
    settings.DJPADDLE_BUSINESS_PLAN_ID = business_plan.id

    r = client.get(f"/teams/{team.id}/account")
    assertOK(r)
    assertLink(r, f"/teams/{team.id}/plan", "Upgrade")

    r = client.get(f"/teams/{team.id}/plan")
    assertOK(r)
    assertContains(r, "Upgrade to Pro")
    assertContains(r, "Upgrade to Business")
    # check for paddle attributes
    passthrough = f'{{"user_id": {logged_in_user.id}, "team_id": {team.id}}}'
    assertSelectorLength(r, f"a[data-passthrough='{passthrough}']", 2)
    assertSelectorLength(r, f"[data-product='{pro_plan.id}']", 1)
    assertSelectorLength(r, f"[data-product='{business_plan.id}']", 1)

    # clicking will launch the javascript checkout
    # this will re-direct to checkout completion page
    # the checkout is inserted by Paddle JS, and the subscription is added via webhook

    checkout = Checkout.objects.create(
        id=uuid4(),
        completed=True,
        passthrough={"user_id": logged_in_user.id, "team_id": team.id},
    )
    Subscription.objects.create(
        id=uuid4(),
        subscriber=team,
        cancel_url="https://cancel.url",
        checkout_id=checkout.id,
        currency="GBP",
        email=logged_in_user.email,
        event_time=timezone.now(),
        marketing_consent=True,
        next_bill_date=timezone.now() + timedelta(weeks=4),
        passthrough={"user_id": logged_in_user.id, "team_id": team.id},
        quantity=1,
        source="test.url",
        status=Subscription.STATUS_ACTIVE,
        plan=pro_plan,
        unit_price=30,
        update_url="https://update.url",
        created_at=timezone.now(),
        updated_at=timezone.now(),
    )
    r = client.get(f"/teams/{team.id}/checkout/success?checkout={checkout.id}")
    assertOK(r)
    assertLink(r, f"/teams/{team.id}/account", "Take me there")

    r = client.get(f"/teams/{team.id}/account")
    assertOK(r)
    assertContains(r, "You are currently subscribed to Pro.")
    assertLink(r, "https://update.url", "Update Payment Method")
    assertLink(r, "https://cancel.url", "Cancel Subscription")
    assertLink(r, f"/teams/{team.id}/plan", "Change Plan")

    # upgrade to business
    r = client.get(f"/teams/{team.id}/plan")
    assertContains(r, 'Your current plan')
    assertContains(r, 'Upgrade to Business')
