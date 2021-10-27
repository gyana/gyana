import re

import pytest
from apps.appsumo.models import AppsumoCode, AppsumoExtra
from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertNotFound,
    assertOK,
    assertSelectorLength,
)
from apps.users.models import CustomUser
from django.core import mail
from django.utils import timezone
from pytest_django.asserts import assertContains, assertFormError, assertRedirects

pytestmark = pytest.mark.django_db


def test_appsumo_link_invalid_code(client, logged_in_user):
    # code does not exist
    r = client.get("/appsumo/00000000")
    assertNotFound(r)

    # code already redeemed by someone else
    code = AppsumoCode.objects.create(code="12345678", redeemed=timezone.now())

    r = client.get("/appsumo/12345678")
    assertOK(r)
    assertContains(r, "has already been redeemed by another user.")

    # code already redeemed by you
    team = logged_in_user.teams.first()
    code.team = team
    code.save()

    r = client.get("/appsumo/12345678")
    assertOK(r)
    assertContains(r, "You've already redeemed the code")
    assertLink(r, f"/teams/{team.id}/account", "account")


def test_appsumo_landing(client):
    r = client.get("/appsumo/")
    assertOK(r)
    assertFormRenders(r, ["code"])

    # code does not exist
    r = client.post("/appsumo/", data={"code": "11111111"})
    assertFormError(r, "form", "code", "AppSumo code does not exist")

    # code is redeemed
    AppsumoCode.objects.create(code="22222222", redeemed=timezone.now())
    r = client.post("/appsumo/", data={"code": "22222222"})
    assertFormError(r, "form", "code", "AppSumo code is already redeemed")

    # code is refunded
    AppsumoCode.objects.create(code="33333333", refunded_before=timezone.now())
    r = client.post("/appsumo/", data={"code": "33333333"})
    assertFormError(r, "form", "code", "AppSumo code has been refunded")

    # create
    AppsumoCode.objects.create(code="12345678")
    r = client.post("/appsumo/", data={"code": "12345678"})
    assertRedirects(r, "/appsumo/12345678", status_code=303, target_status_code=302)


def test_code_signup_with_email_verification_and_onboarding(client, settings):
    settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"

    AppsumoCode.objects.create(code="12345678")

    assertRedirects(client.get("/appsumo/12345678"), "/appsumo/signup/12345678")

    r = client.get("/appsumo/signup/12345678")
    assertOK(r)
    assertFormRenders(r, ["email", "password1", "team"])

    r = client.post(
        "/appsumo/signup/12345678",
        data={
            "email": "test@gyana.com",
            "password1": "seewhatmatters",
            "team": "Test team",
        },
    )
    assertRedirects(r, "/confirm-email/", status_code=303)

    user = CustomUser.objects.first()
    team = user.teams.first()
    assert team.name == "Test team"
    assert team.appsumocode_set.count() == 1
    assert team.appsumocode_set.first().code == "12345678"

    # verify
    assert len(mail.outbox) == 1
    link = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group("url")

    assertRedirects(client.get(link), "/", target_status_code=302)
    assertRedirects(client.get("/"), "/users/onboarding/")

    # onboarding
    # todo: move logic to signup test, once signup is enabled
    r = client.get("/users/onboarding/")
    assertOK(r)
    assertFormRenders(r, ["first_name", "last_name", "marketing_allowed"])

    r = client.post(
        "/users/onboarding/",
        data={"first_name": "New", "last_name": "User", "marketing_allowed": True},
    )
    assertRedirects(r, "/users/onboarding/", status_code=303)

    r = client.get("/users/onboarding/")
    assertOK(r)
    assertFormRenders(r, ["company_industry", "company_role", "company_size"])

    r = client.post(
        "/users/onboarding/",
        data={
            "company_industry": "agency",
            "company_role": "marketing",
            "company_size": "2-10",
        },
    )
    assertRedirects(r, "/", status_code=303, target_status_code=302)
    assertRedirects(client.get("/"), f"/teams/{team.id}")

    user.refresh_from_db()
    assert user.marketing_allowed
    assert user.company_industry == "agency"
    assert user.onboarded


def test_redeem_code_on_existing_account_and_team(client, logged_in_user):
    team = logged_in_user.teams.first()
    AppsumoCode.objects.create(code="12345678")

    assertRedirects(client.get("/appsumo/12345678"), "/appsumo/redeem/12345678")

    r = client.get("/appsumo/redeem/12345678")
    assertOK(r)
    assertFormRenders(r, ["team"])

    r = client.post("/appsumo/redeem/12345678", data={"team": team.id})
    assertRedirects(r, "/", status_code=303, target_status_code=302)
    assertRedirects(client.get("/"), f"/teams/{team.id}")

    assert team.appsumocode_set.count() == 1
    assert team.appsumocode_set.first().code == "12345678"


def test_redeem_code_on_existing_account_and_no_team(client):
    user = CustomUser.objects.create_user("test", onboarded=True)
    client.force_login(user)
    AppsumoCode.objects.create(code="12345678")

    assertRedirects(client.get("/appsumo/12345678"), "/appsumo/redeem/12345678")

    r = client.get("/appsumo/redeem/12345678")
    assertOK(r)
    assertFormRenders(r, ["team_name"])

    r = client.post("/appsumo/redeem/12345678", data={"team_name": "Test team"})
    assertRedirects(r, "/", status_code=303, target_status_code=302)

    team = user.teams.first()
    assertRedirects(client.get("/"), f"/teams/{team.id}")

    assert team.name == "Test team"
    assert team.appsumocode_set.count() == 1
    assert team.appsumocode_set.first().code == "12345678"


def test_stack(client, logged_in_user):
    team = logged_in_user.teams.first()
    original_code = AppsumoCode.objects.create(code="00000000", team=team)
    code = AppsumoCode.objects.create(code="12345678")

    # view list of appsumo codes
    r = client.get_turbo_frame(
        f"/teams/{team.id}/account", f"/teams/{team.id}/appsumo/"
    )
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 1)
    assertLink(r, f"/teams/{team.id}/appsumo/stack", "Stack Code")

    # redeem a new code
    r = client.get(f"/teams/{team.id}/appsumo/stack")
    assertOK(r)
    assertFormRenders(r, ["code"])

    r = client.post(f"/teams/{team.id}/appsumo/stack", data={"code": "12345678"})
    assertRedirects(r, f"/teams/{team.id}/account", status_code=303)

    assert list(team.appsumocode_set.all()) == [code, original_code]

    # view updated list of codes
    r = client.get_turbo_frame(
        f"/teams/{team.id}/account", f"/teams/{team.id}/appsumo/"
    )
    assertOK(r)
    assertSelectorLength(r, "table tbody tr", 2)


def test_admin_extra_rows(client, logged_in_user):
    team = logged_in_user.teams.first()
    AppsumoCode.objects.create(code="00000000", team=team)
    AppsumoExtra.objects.create(rows=1, reason="For being awesome", team=team)

    r = client.get_turbo_frame(
        f"/teams/{team.id}/account",
        f"/teams/{team.id}/appsumo/",
        f"/teams/{team.id}/appsumo/extra",
    )
    assertOK(r)
    assertContains(r, "For being awesome")


# # Incentivised reviews are disabled due to new AppSumo policy

# def test_link_to_review(client, logged_in_user):
#     link = "https://appsumo.com/products/marketplace-gyana/#r666666"
#     team = logged_in_user.teams.first()
#     AppsumoCode.objects.create(code="00000000", team=team)

#     # there is no link
#     r = client.get_turbo_frame(
#         f"/teams/{team.id}/account", f"/teams/{team.id}/appsumo/"
#     )
#     assertOK(r)
#     assertLink(r, f"/teams/{team.id}/appsumo/review", "Link to your review")

#     # create
#     r = client.get(f"/teams/{team.id}/appsumo/review")
#     assertOK(r)
#     assertFormRenders(r, ["review_link"])

#     r = client.post(f"/teams/{team.id}/appsumo/review", data={"review_link": link})
#     assertRedirects(r, f"/teams/{team.id}/account", status_code=303)

#     # link created
#     r = client.get_turbo_frame(
#         f"/teams/{team.id}/account", f"/teams/{team.id}/appsumo/"
#     )
#     assertOK(r)
#     assertContains(r, "Thank you for writing an honest review!")

#     assert team.appsumoreview.review_link == link

#     # cannot review twice
#     r = client.post(f"/teams/{team.id}/appsumo/review", data={"review_link": link})
#     assert r.status_code == 422
#     error = "A user has linked to this review for their team. If you think this is a mistake, reach out to support and we'll sort it out for you."
#     assertFormError(r, "form", "review_link", error)
