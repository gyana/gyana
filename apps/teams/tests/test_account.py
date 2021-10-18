import pytest
from apps.appsumo.models import AppsumoCode, AppsumoExtra, AppsumoReview
from apps.teams.account import get_row_limit
from apps.teams.models import Team

pytestmark = pytest.mark.django_db


def test_row_limit():
    team = Team.objects.create(name="Test team")
    assert get_row_limit(team) == 50_000

    team.override_row_limit = 10
    assert get_row_limit(team) == 10

    team.override_row_limit = None
    AppsumoCode.objects.create(code="12345678", team=team)
    assert get_row_limit(team) == 1_000_000

    AppsumoReview.objects.create(
        team=team,
        review_link="https://appsumo.com/products/marketplace-gyana/#r666666",
    )
    assert get_row_limit(team) == 2_000_000

    AppsumoExtra.objects.create(team=team, rows=100_000, reason="extra")
    assert get_row_limit(team) == 2_100_000
