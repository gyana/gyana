from unittest.mock import Mock, patch

import pytest
from allauth.account.forms import SignupForm
from apps.appsumo.forms import (
    AppsumoLandingform,
    AppsumoRedeemForm,
    AppsumoRedeemNewTeamForm,
    AppsumoSignupForm,
    AppsumoStackForm,
)
from apps.appsumo.models import AppsumoCode
from apps.teams.models import Team
from apps.users.models import CustomUser
from django.utils import timezone

pytestmark = pytest.mark.django_db


class TestAppsumoLandingform:
    @pytest.fixture
    def code(self):
        return AppsumoCode.objects.create(code="12345678")

    def test_invalid_code(self, code):
        form = AppsumoLandingform(data={"code": "ABCDEFGH"})
        assert form.errors["code"] == ["Not a valid AppSumo code"]


class TestAppsumoStackForm:
    @pytest.fixture
    def code(self):
        return AppsumoCode.objects.create(code="12345678", redeemed=timezone.now())

    def test_does_not_exist(self, code):
        form = AppsumoStackForm(data={"code": "ABCDEFGH"})
        assert form.errors["code"] == ["AppSumo code does not exist"]

    def test_is_redeemed(self, code):
        form = AppsumoStackForm(data={"code": "12345678"})
        assert form.errors["code"] == ["AppSumo code is already redeemed"]


class TestAppsumoRedeemNewTeamForm:
    def test_redeem_new_team(self):
        user = CustomUser.objects.create_user("test")
        code = AppsumoCode.objects.create(code="12345678")

        form = AppsumoRedeemNewTeamForm(
            data={"team_name": "test_team"}, instance=code, user=user
        )
        form.save()

        assert code.redeemed_by == user
        assert code.redeemed is not None

        assert user.teams.count() == 1
        team = user.teams.first()
        assert team.name == "test_team"


class TestAppsumoRedeemForm:
    @pytest.fixture
    def initial(self):
        user = CustomUser.objects.create_user("test")
        team = Team.objects.create(name="test_team")
        code = AppsumoCode.objects.create(code="12345678")
        team.members.add(user)

        return user, team, code

    def test_select_options(self, initial):
        user, team, code = initial

        form = AppsumoRedeemForm(user=user, instance=code)
        assert len(form.fields["team"].queryset) == 1
        assert form.fields["team"].queryset[0] == team

    def test_redeem_team(self, initial):
        user, team, code = initial

        form = AppsumoRedeemForm(data={"team": team.id}, instance=code, user=user)
        form.save()

        assert team.appsumocode_set.count() == 1
        assert team.appsumocode_set.first() == code

        assert code.redeemed_by == user
        assert code.redeemed is not None


class TestAppsumoSignupForm:
    def test_signup(self):
        user = CustomUser.objects.create_user("test")
        code = AppsumoCode.objects.create(code="12345678")

        form = AppsumoSignupForm(
            data={
                "email": "test@gyana.com",
                "password1": "seewhatmatters",
                "team": "test_team",
            },
            code=code,
        )
        with patch.object(SignupForm, "save", return_value=user):
            assert form.is_valid()
            user = form.save(Mock())

        code.refresh_from_db()

        assert code.redeemed_by == user
        assert code.redeemed is not None

        assert user.teams.count() == 1
        team = user.teams.first()
        assert team.name == "test_team"
