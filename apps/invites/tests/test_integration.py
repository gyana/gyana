import re

import pytest
from django.core import mail
from pytest_django.asserts import assertFormError, assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertLink, assertOK
from apps.invites.models import Invite
from apps.users.models import CustomUser

pytestmark = pytest.mark.django_db


def test_invite_new_user_to_team(client, logged_in_user):
    team = logged_in_user.teams.first()

    # invite
    r = client.get(f"/teams/{team.id}")
    assertOK(r)
    assertLink(r, f"/teams/{team.id}/members/", "Members")

    r = client.get_turbo_frame(
        f"/teams/{team.id}/members/", f"/teams/{team.id}/invites/"
    )
    assertOK(r)
    assertLink(r, f"/teams/{team.id}/invites/new", "New Invite")

    r = client.get(f"/teams/{team.id}/invites/new")
    assertOK(r)
    assertFormRenders(r, ["email", "role"])

    r = client.post(
        f"/teams/{team.id}/invites/new",
        data={"email": "invite@gyana.com", "role": "member"},
    )
    assertRedirects(r, f"/teams/{team.id}/members/", status_code=303)

    # accept
    assert len(mail.outbox) == 1
    link = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group("url")

    client.logout()

    r = client.get(link)
    assertRedirects(r, "/signup/")

    invite = Invite.objects.first()
    assert invite is not None
    assert not invite.accepted

    # signup
    r = client.post(
        "/signup/", data={"email": "invite@gyana.com", "password1": "password"}
    )
    assertRedirects(r, "/", status_code=303, target_status_code=302)
    assertRedirects(client.get("/"), "/users/onboarding/")

    invite.refresh_from_db()
    assert invite.accepted
    assert team.members.count() == 2

    # regression test: gya-265
    r = client.get(link)
    assertRedirects(r, "/signup/", target_status_code=302)


def test_invite_existing_user_to_team(client, logged_in_user):
    invited_user = CustomUser.objects.create_user(
        "invite", email="invite@gyana.com", password="seewhatmatters", onboarded=True
    )
    team = logged_in_user.teams.first()

    # invite
    r = client.post(
        f"/teams/{team.id}/invites/new",
        data={"email": "invite@gyana.com", "role": "member"},
    )
    invite = Invite.objects.first()

    # accept
    assert len(mail.outbox) == 1
    link = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group("url")

    invite_link = f"/invitations/accept-invite/{invite.key}"

    client.logout()

    r = client.get(link)
    assertRedirects(r, f"/login/?next={invite_link}")

    r = client.post(
        f"/login/?next={invite_link}",
        data={"login": "invite@gyana.com", "password": "seewhatmatters"},
    )
    assertRedirects(r, invite_link, status_code=303, fetch_redirect_response=False)

    r = client.get(invite_link)
    assertRedirects(r, f"/teams/{team.id}")

    invite.refresh_from_db()
    assert invite is not None
    assert invite.accepted
    assert team.members.count() == 2


def test_invite_existing_authenticated_user_to_team(client, logged_in_user):
    invited_user = CustomUser.objects.create_user(
        "invite", email="invite@gyana.com", onboarded=True
    )
    team = logged_in_user.teams.first()

    # invite
    r = client.post(
        f"/teams/{team.id}/invites/new",
        data={"email": "invite@gyana.com", "role": "member"},
    )
    invite = Invite.objects.first()
    assert invite is not None

    # accept
    assert len(mail.outbox) == 1
    link = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group("url")

    # fix gya-311: current logged in user cannot accept invite
    r = client.get(link)
    invite.refresh_from_db()
    assert not invite.accepted

    # login as invited user
    client.logout()
    client.force_login(invited_user)

    r = client.get(link)
    assertRedirects(r, f"/teams/{team.id}")

    invite.refresh_from_db()
    assert invite.accepted
    assert team.members.count() == 2


def test_resend_and_delete_invite(client, logged_in_user):
    team = logged_in_user.teams.first()

    # invite
    r = client.post(
        f"/teams/{team.id}/invites/new",
        data={"email": "invite@gyana.com", "role": "member"},
    )
    assert len(mail.outbox) == 1

    invite = Invite.objects.first()

    r = client.get(f"/teams/{team.id}/invites/")
    assertOK(r)
    # resend form action
    assertFormRenders(r)
    assertLink(
        r, f"/teams/{team.id}/invites/{invite.id}/delete", tooltip="Delete invite"
    )

    # resend
    r = client.get(
        f"/teams/{team.id}/invites/{invite.id}/resend", tooltip="Send invite again"
    )
    assertOK(r)

    r = client.post(f"/teams/{team.id}/invites/{invite.id}/resend")
    assertRedirects(r, f"/teams/{team.id}/invites/{invite.id}/resend")

    assert len(mail.outbox) == 2

    # delete
    r = client.get(f"/teams/{team.id}/invites/{invite.id}/delete")
    assertOK(r)
    assertFormRenders(r)

    r = client.delete(f"/teams/{team.id}/invites/{invite.id}/delete")
    assertRedirects(r, f"/teams/{team.id}/members/")

    client.logout()

    assert Invite.objects.count() == 0

    link = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group("url")
    r = client.get(link)
    assertRedirects(r, "/signup/")


def test_cannot_invite_existing_user_or_existing_invited_user(client, logged_in_user):
    team = logged_in_user.teams.first()
    member_user = CustomUser.objects.create_user("invite", email="member@gyana.com")
    team.members.add(member_user, through_defaults={"role": "member"})

    # invite
    r = client.post(
        f"/teams/{team.id}/invites/new",
        data={"email": "member@gyana.com", "role": "member"},
    )

    assert r.status_code == 422
    assertFormError(
        r, "form", None, "A user with this email is already part of your team."
    )

    # delete the member but invite model still exists
    member_user.delete()
    assert (
        client.post(
            f"/teams/{team.id}/invites/new",
            data={"email": "member@gyana.com", "role": "member"},
        ).status_code
        == 303
    )
    r = client.post(
        f"/teams/{team.id}/invites/new",
        data={"email": "member@gyana.com", "role": "member"},
    )
    assert r.status_code == 422
    assertFormError(
        r, "form", None, "A user with this email is already invited to your team."
    )
