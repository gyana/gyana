import pytest
from apps.appsumo.models import AppsumoCode, AppsumoExtra
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
        assert team.ltd_disabled

    def test_exceeds_stacking_limit(self):
        team = Team.objects.create(name="Test team")
        for code in range(5):
            AppsumoCode.objects.create(team=team, code=str(code) * 8)

        assert not team.exceeds_stacking_limit

        code = AppsumoCode.objects.create(team=team, code="55555555")
        assert team.exceeds_stacking_limit

        code.refunded_before = timezone.now()
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
