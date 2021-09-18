import pytest
from apps.appsumo.models import AppsumoCode
from apps.appsumo.views import AppsumoReview
from apps.teams.models import Team
from apps.users.models import CustomUser
from django.utils import timezone
from pytest_django.asserts import assertRedirects, assertTemplateUsed

pytestmark = pytest.mark.django_db


class TestAppsumoStack:
    @pytest.fixture
    def setup(self, client):
        team = Team.objects.create(name="team_team")
        user = CustomUser.objects.create_user("test")
        team.members.add(user, through_defaults={"role": "admin"})
        client.force_login(user)

    def test_get(self, client, setup):
        response = client.get("/teams/1/appsumo/stack")
        assert response.status_code == 200

    def test_post(self, client, setup):
        AppsumoCode.objects.create(code="12345678")
        response = client.post("/teams/1/appsumo/stack", data={"code": "12345678"})

        assert response.status_code == 303
        assert response.url == "/teams/1/account"


class TestAppsumoLanding:
    def test_get(self, client):
        response = client.get("/appsumo/")
        assert response.status_code == 200

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
    pass


class TestAppsumoRedeem:
    pass


class TestAppsumoReview:
    @pytest.fixture
    def view(self, rf):
        team = Team.objects.create(name="test_team")
        request = rf.get("/teams/1/appsumo/review")
        view_instance = AppsumoReview()
        view_instance.setup(request, team_id=team.id)
        return view_instance

    def test_form_kwargs(self, view):
        assert "team" in view.get_form_kwargs()

    def test_success_url(self, view):
        assert view.get_success_url() == "/teams/1/account"
