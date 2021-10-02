import re

import pytest
from apps.invites.models import Invite
from apps.users.models import CustomUser
from django.core import mail

pytestmark = pytest.mark.django_db


def test_invite_new_user_to_team(client, logged_in_user):
    team = logged_in_user.teams.first()

    # invite
    assert client.get(f"/teams/{team.id}/invites/new").status_code == 200

    r = client.post(
        f"/teams/{team.id}/invites/new",
        data={"email": "invite@gyana.com", "role": "member"},
    )
    assert r.status_code == 303
    assert r.url == f"/teams/{team.id}/members/"

    # accept
    assert len(mail.outbox) == 1
    link = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group("url")

    client.logout()

    r = client.get(link)
    r.status_code == 200

    invite = Invite.objects.first()
    assert invite is not None
    assert invite.accepted

    # signup
    r = client.post(
        "/signup/", data={"email": "invite@gyana.com", "password1": "password"}
    )
    assert r.status_code == 303
    assert r.url == "/"

    assert team.members.count() == 2


def test_invite_existing_user_to_team(client, logged_in_user):
    invited_user = CustomUser.objects.create_user("invite", email="invite@gyana.com")
    team = logged_in_user.teams.first()

    # invite
    assert client.get(f"/teams/{team.id}/invites/new").status_code == 200

    r = client.post(
        f"/teams/{team.id}/invites/new",
        data={"email": "invite@gyana.com", "role": "member"},
    )
    assert r.status_code == 303
    assert r.url == f"/teams/{team.id}/members/"

    # accept
    assert len(mail.outbox) == 1
    link = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group("url")

    client.logout()
    client.force_login(invited_user)

    r = client.get(link)
    r.status_code == 200

    invite = Invite.objects.first()
    assert invite is not None
    assert invite.accepted

    assert team.members.count() == 2


def test_resend_and_delete_invite(client, logged_in_user):
    team = logged_in_user.teams.first()

    # invite
    r = client.post(
        f"/teams/{team.id}/invites/new",
        data={"email": "invite@gyana.com", "role": "member"},
    )
    assert r.status_code == 303
    assert r.url == f"/teams/{team.id}/members/"
    assert len(mail.outbox) == 1

    invite = Invite.objects.first()

    # redo
    assert client.get(f"/teams/{team.id}/invites/{invite.id}/resend").status_code == 200

    r = client.post(f"/teams/{team.id}/invites/{invite.id}/resend")
    r.status_code == 303
    r.url == f"/teams/{team.id}/invites/"

    assert len(mail.outbox) == 2

    # delete
    assert client.get(f"/teams/{team.id}/invites/{invite.id}/delete").status_code == 200

    r = client.delete(f"/teams/{team.id}/invites/{invite.id}/delete")
    r.status_code == 302
    r.url == f"/teams/{team.id}/invites/"

    client.logout()

    assert Invite.objects.count() == 0

    link = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group("url")
    assert client.get(link).status_code == 410


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
    assert (
        r.context["form"].non_field_errors()[0]
        == "A user with this email is already part of your team."
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
    assert (
        r.context["form"].non_field_errors()[0]
        == "A user with this email is already invited to your team."
    )
