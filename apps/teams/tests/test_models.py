import pytest
from apps.appsumo.models import AppsumoCode, AppsumoExtra, AppsumoReview
from apps.teams.models import Team
from django.utils import timezone

pytestmark = pytest.mark.django_db


class TestTeam:
    def test_redeemed_refunded_active(self):
        team = Team.objects.create(name="Test team")

        now = timezone.now()
        AppsumoCode.objects.create(team=team, code="11111111")
        AppsumoCode.objects.create(team=team, code="22222222")
        AppsumoCode.objects.create(team=team, code="33333333", refunded_before=now)
        AppsumoCode.objects.create(team=team, code="44444444", refunded_before=now)
        AppsumoCode.objects.create(team=team, code="55555555", refunded_before=now)

        assert team.redeemed_codes == 5
        assert team.refunded_codes == 3
        assert team.active_codes == 2

    def test_ltd_disabled(self):
        team = Team.objects.create(name="Test team")
        code = AppsumoCode.objects.create(team=team, code="11111111")

        assert not team.ltd_disabled
        code.refunded_before = timezone.now()
        code.save()
        assert team.ltd_disabled

    def test_exceeds_stacking_limit(self):
        team = Team.objects.create(name="Test team")
        for code in range(5):
            AppsumoCode.objects.create(team=team, code=str(code) * 8)

        assert not team.exceeds_stacking_limit

        code = AppsumoCode.objects.create(team=team, code="55555555")
        assert team.exceeds_stacking_limit

        code.refunded_before = timezone.now()
        code.save()
        assert not team.exceeds_stacking_limit

    def test_has_extra_rows(self):
        team = Team.objects.create(name="Test team")

        assert not team.has_extra_rows

        AppsumoExtra.objects.create(team=team, rows=1, reason="extra")
        assert team.has_extra_rows

    def test_plan(self):
        team = Team.objects.create(name="Test team")

        assert team.plan == "Free"

        AppsumoCode.objects.create(team=team, code="11111111")
        assert team.plan == "Lifetime Deal for Gyana"

    def test_row_limit(self):
        team = Team.objects.create(name="Test team")
        assert team.row_limit == 50_000

        team.override_row_limit = 10
        assert team.row_limit == 10

        team.override_row_limit = None
        AppsumoCode.objects.create(code="12345678", team=team)
        assert team.row_limit == 1_000_000

        AppsumoReview.objects.create(
            team=team,
            review_link="https://appsumo.com/products/marketplace-gyana/#r666666",
        )
        assert team.row_limit == 2_000_000

        AppsumoExtra.objects.create(team=team, rows=100_000, reason="extra")
        assert team.row_limit == 2_100_000
