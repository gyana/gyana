import pytest
from apps.appsumo.models import AppsumoCode
from apps.appsumo.views import AppsumoReview
from apps.teams.models import Team
from apps.users.models import CustomUser
from django.utils import timezone
from pytest_django.asserts import assertRedirects, assertTemplateUsed

pytestmark = pytest.mark.django_db


class TestAppsumoLanding:
    def test_get(self, client):
        response = client.get("/appsumo/")
        assert response.status_code == 200

    def test_does_not_exist(self, client):
        response = client.post("/appsumo/", data={"code": "12345678"})
        assert response.status_code == 422
        assert (
            response.context["form"].errors["code"][0] == "AppSumo code does not exist"
        )

    def test_already_redeemed(self, client):
        AppsumoCode.objects.create(code="12345678", redeemed=timezone.now())
        response = client.post("/appsumo/", data={"code": "12345678"})
        assert response.status_code == 422
        assert (
            response.context["form"].errors["code"][0]
            == "AppSumo code is already redeemed"
        )

    def test_refunded(self, client):
        AppsumoCode.objects.create(code="12345678", refunded_before=timezone.now())
        response = client.post("/appsumo/", data={"code": "12345678"})
        assert response.status_code == 422
        assert (
            response.context["form"].errors["code"][0]
            == "AppSumo code has been refunded"
        )

    def test_post(self, client):
        AppsumoCode.objects.create(code="12345678")
        response = client.post("/appsumo/", data={"code": "12345678"})
        assert response.status_code == 303
        assert response.url == "/appsumo/12345678"


class TestAppsumoRedirect:
    def test_redeemed_already(self, client):
        AppsumoCode.objects.create(code="12345678", redeemed=timezone.now())
        response = client.get("/appsumo/12345678")

        assert response.status_code == 200
        assertTemplateUsed(response, "appsumo/already_redeemed.html")

    def test_redirect_signup(self, client):
        AppsumoCode.objects.create(code="12345678")
        response = client.get("/appsumo/12345678")
        assertRedirects(response, "/appsumo/signup/12345678")

    def test_redirect_login(self, client):
        user = CustomUser.objects.create_user("test")
        AppsumoCode.objects.create(code="12345678")

        client.force_login(user)
        response = client.get("/appsumo/12345678")
        assertRedirects(response, "/appsumo/redeem/12345678")


class TestAppsumoSignup:
    def test_get(self, client):
        AppsumoCode.objects.create(code="12345678")
        response = client.get("/appsumo/signup/12345678")
        assert response.status_code == 200

    def test_signup_email_not_required(self, client):
        AppsumoCode.objects.create(code="12345678")
        response = client.post(
            "/appsumo/signup/12345678",
            data={
                "email": "test@gyana.com",
                "password1": "seewhatmatters",
                "team": "Test team",
            },
        )
        assert response.status_code == 303
        assert response.url == "/users/onboarding/"

        user = CustomUser.objects.first()
        team = user.teams.first()
        assert team.name == "Test team"
        assert team.appsumocode_set.count() == 1
        assert team.appsumocode_set.first().code == "12345678"

    def test_signup_email_required(self, client, settings):
        settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"

        AppsumoCode.objects.create(code="12345678")
        response = client.post(
            "/appsumo/signup/12345678",
            data={
                "email": "test@gyana.com",
                "password1": "seewhatmatters",
                "team": "Test team",
            },
        )
        assert response.status_code == 303
        assert response.url == "/confirm-email/"


class TestAppsumoRedeem:
    def test_get(self, client):
        AppsumoCode.objects.create(code="12345678")
        user = CustomUser.objects.create_user("test")
        client.force_login(user)
        response = client.get("/appsumo/redeem/12345678")
        assert response.status_code == 200

    def test_existing_team(self, client):
        AppsumoCode.objects.create(code="12345678")
        team = Team.objects.create(name="team_team")
        user = CustomUser.objects.create_user("test")
        team.members.add(user, through_defaults={"role": "admin"})
        client.force_login(user)

        response = client.post("/appsumo/redeem/12345678", data={"team": team.id})
        assert response.status_code == 303
        assert team.appsumocode_set.count() == 1
        assert team.appsumocode_set.first().code == "12345678"

    def test_new_team(self, client):
        AppsumoCode.objects.create(code="12345678")
        user = CustomUser.objects.create_user("test")
        client.force_login(user)

        response = client.post(
            "/appsumo/redeem/12345678", data={"team_name": "Test team"}
        )
        assert response.status_code == 303
        team = user.teams.first()
        assert team.name == "Test team"
        assert team.appsumocode_set.count() == 1
        assert team.appsumocode_set.first().code == "12345678"


class TestAppsumoStack:
    def test_get(self, client):
        team = Team.objects.create(name="team_team")
        user = CustomUser.objects.create_user("test")
        team.members.add(user, through_defaults={"role": "admin"})
        client.force_login(user)

        response = client.get("/teams/1/appsumo/stack")
        assert response.status_code == 200

    def test_post(self, client):
        team = Team.objects.create(name="team_team")
        user = CustomUser.objects.create_user("test")
        team.members.add(user, through_defaults={"role": "admin"})
        client.force_login(user)

        code = AppsumoCode.objects.create(code="12345678")
        response = client.post("/teams/1/appsumo/stack", data={"code": "12345678"})

        assert response.status_code == 303
        assert response.url == "/teams/1/account"

        assert list(team.appsumocode_set.all()) == [code]


class TestAppsumoReview:
    def test_tbh(self, client):
        assert False
