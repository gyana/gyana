import pytest
from apps.appsumo.models import AppsumoCode, AppsumoExtra
from apps.users.models import CustomUser
from django.utils import timezone
from pytest_django.asserts import assertRedirects

pytestmark = pytest.mark.django_db


def test_appsumo_link_invalid_code(client):
    AppsumoCode.objects.create(code="12345678", redeemed=timezone.now())

    # already redeemed (no redirection)
    assert client.get("/appsumo/12345678").status_code == 200


def test_appsumo_landing(client):
    # code does not exist
    r = client.post("/appsumo/", data={"code": "11111111"})
    assert r.context["form"].errors["code"][0] == "AppSumo code does not exist"

    # code is redeemed
    AppsumoCode.objects.create(code="22222222", redeemed=timezone.now())
    r = client.post("/appsumo/", data={"code": "22222222"})
    assert r.context["form"].errors["code"][0] == "AppSumo code is already redeemed"

    # code is refunded
    AppsumoCode.objects.create(code="33333333", refunded_before=timezone.now())
    r = client.post("/appsumo/", data={"code": "33333333"})
    assert r.context["form"].errors["code"][0] == "AppSumo code has been refunded"

    # create
    AppsumoCode.objects.create(code="12345678")
    r = client.post("/appsumo/", data={"code": "12345678"})
    assert r.status_code == 303
    assert r.url == "/appsumo/12345678"


def test_signup_with_code(client):
    AppsumoCode.objects.create(code="12345678")

    assertRedirects(client.get("/appsumo/12345678"), "/appsumo/signup/12345678")

    r = client.post(
        "/appsumo/signup/12345678",
        data={
            "email": "test@gyana.com",
            "password1": "seewhatmatters",
            "team": "Test team",
        },
    )
    assert r.status_code == 303
    assert r.url == "/users/onboarding/"

    user = CustomUser.objects.first()
    team = user.teams.first()
    assert team.name == "Test team"
    assert team.appsumocode_set.count() == 1
    assert team.appsumocode_set.first().code == "12345678"


def test_redeem_code_on_existing_account_and_team(client, logged_in_user):
    AppsumoCode.objects.create(code="12345678")

    assertRedirects(client.get("/appsumo/12345678"), "/appsumo/redeem/12345678")

    team = logged_in_user.teams.first()
    r = client.post("/appsumo/redeem/12345678", data={"team": team.id})
    assert r.status_code == 303
    assert r.url == "/"

    assert team.appsumocode_set.count() == 1
    assert team.appsumocode_set.first().code == "12345678"


def test_redeem_code_on_existing_account_and_no_team(client):
    user = CustomUser.objects.create_user("test", onboarded=True)
    client.force_login(user)

    AppsumoCode.objects.create(code="12345678")

    assertRedirects(client.get("/appsumo/12345678"), "/appsumo/redeem/12345678")

    r = client.post("/appsumo/redeem/12345678", data={"team_name": "Test team"})
    assert r.status_code == 303
    assert r.url == "/"

    team = user.teams.first()
    assert team.name == "Test team"
    assert team.appsumocode_set.count() == 1
    assert team.appsumocode_set.first().code == "12345678"


def test_stack_and_refund(client, logged_in_user):
    team = logged_in_user.teams.first()

    code = AppsumoCode.objects.create(code="12345678")
    r = client.post(f"/teams/{team.id}/appsumo/stack", data={"code": "12345678"})

    assert r.status_code == 303
    assert r.url == f"/teams/{team.id}/account"

    assert list(team.appsumocode_set.all()) == [code]

    assert client.get(f"/teams/{team.id}/appsumo/").status_code == 200


def test_link_to_review(client, logged_in_user):
    link = "https://appsumo.com/products/marketplace-gyana/#r666666"
    team = logged_in_user.teams.first()
    r = client.post(f"/teams/{team.id}/appsumo/review", data={"review_link": link})

    assert r.status_code == 303
    assert r.url == f"/teams/{team.id}/account"

    assert team.appsumoreview.review_link == link

    r = client.post(f"/teams/{team.id}/appsumo/review", data={"review_link": link})
    assert r.status_code == 422
    assert (
        r.context["form"].errors["review_link"][0]
        == "A user has linked to this review for their team. If you think this is a mistake, reach out to support and we'll sort it out for you."
    )


def test_admin_extra_rows(client, logged_in_user):
    team = logged_in_user.teams.first()
    AppsumoExtra.objects.create(rows=1, reason="extra", team=team)

    assert client.get(f"/teams/{team.id}/appsumo/extra").status_code == 200
