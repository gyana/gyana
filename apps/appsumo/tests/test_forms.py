from unittest.mock import MagicMock, Mock, patch

import pytest
from allauth.account.forms import SignupForm
from apps.appsumo.forms import (
    AppsumoCodeForm,
    AppsumoRedeemForm,
    AppsumoRedeemNewTeamForm,
    AppsumoReviewForm,
    AppsumoSignupForm,
)
from apps.appsumo.models import AppsumoCode, AppsumoReview
from apps.teams.models import Team

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def transaction_atomic_patch():
    with patch("django.db.transaction.atomic"):
        yield


class TestAppsumoCodeForm:
    @patch.object(AppsumoCode, "exists", return_value=False)
    def test_does_not_exist(self, *_):
        form = AppsumoCodeForm(data={"code": "ABCDEFGH"})
        assert form.errors["code"] == ["AppSumo code does not exist"]

    @patch.object(AppsumoCode, "exists", return_value=True)
    @patch.object(AppsumoCode, "available", return_value=False)
    def test_is_redeemed(self, *_):
        form = AppsumoCodeForm(data={"code": "12345678"})
        assert form.errors["code"] == ["AppSumo code is already redeemed"]

    @patch.object(AppsumoCode, "exists", return_value=True)
    @patch.object(AppsumoCode, "available", return_value=True)
    def test_valid(self, *_):
        form = AppsumoCodeForm(data={"code": "12345678"})
        assert form.is_valid()


class TestAppsumoRedeemNewTeamForm:
    def test_on_commit(self, *_):
        user = MagicMock()
        code = MagicMock()

        form = AppsumoRedeemNewTeamForm(instance=code, user=user)
        form.cleaned_data = {"team_name": "test_team"}
        form.on_commit(code)

        assert code.redeem_new_team.call_count == 1
        assert code.redeem_new_team.call_args[0] == ("test_team", user)


class TestAppsumoRedeemForm:
    def test_teams_queryset(self):
        user = MagicMock()
        teams = MagicMock()
        user.teams_admin_of = teams

        form = AppsumoRedeemForm(user=user)
        # internally ModelChoiceField will call .all()
        assert form.fields["team"].queryset == teams.all()

    def test_on_commit(self, *_):
        code = MagicMock()
        user = MagicMock()
        teams = MagicMock()
        user.teams_admin_of = teams

        form = AppsumoRedeemForm(instance=code, user=user)
        form.on_commit(code)

        assert code.redeem_by_user.call_count == 1
        assert code.redeem_by_user.call_args[0] == (user,)


class TestAppsumoSignupForm:
    def test_signup(self, *_):
        user = MagicMock()
        code = MagicMock()

        form = AppsumoSignupForm(code=code)
        form.cleaned_data = {"team": "test_team"}

        with patch.object(SignupForm, "save", return_value=user):
            form.save(MagicMock())

        assert code.redeem_new_team.call_count == 1
        assert code.redeem_new_team.call_args[0] == ("test_team", user)


class TestAppsumoReviewForm:
    # def test_invalid_link_regex(self):
    #     form = AppsumoReviewForm(
    #         data={"review_link": "https://appsumo.com/products/marketplace-gyana/"}
    #     )
    #     assert form.errors["review_link"] == [
    #         "Paste the exact link as displayed on AppSumo"
    #     ]

    # def test_link_already_exists(self):
    #     AppsumoReview.objects.create(
    #         review_link="https://appsumo.com/products/marketplace-gyana/#r678678",
    #         team=Team.objects.create(name="test_team"),
    #     )
    #     form = AppsumoReviewForm(
    #         data={
    #             "review_link": "https://appsumo.com/products/marketplace-gyana/#r678678"
    #         }
    #     )
    #     assert form.errors["review_link"] == [
    #         "A user has linked to this review for their team. If you think this is a mistake, reach out to support and we'll sort it out for you."
    #     ]

    def test_create_link(self):
        team = Team.objects.create(name="test_team")
        form = AppsumoReviewForm(
            data={
                "review_link": "https://appsumo.com/products/marketplace-gyana/#r678678"
            },
            team=team,
        )
        assert form.is_valid()
        form.save()

        assert hasattr(team, "appsumoreview")
        assert (
            team.appsumoreview.review_link
            == "https://appsumo.com/products/marketplace-gyana/#r678678"
        )
