import pytest
from apps.appsumo.models import AppsumoCode
from apps.users.models import CustomUser
from django.utils import timezone
from pytest_django.asserts import assertRedirects, assertTemplateUsed

pytestmark = pytest.mark.django_db


class TestAppsumoStack:
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
