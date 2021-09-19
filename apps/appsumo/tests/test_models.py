from datetime import datetime

import pytest
from apps.appsumo.models import (AppsumoCode, AppsumoReview, PurchasedCodes,
                                 RefundedCodes, UploadedCodes)
from apps.teams.models import Team
from apps.users.models import CustomUser
from django.core import exceptions
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

pytestmark = pytest.mark.django_db


class TestAppsumoCode:
    def test_refunded(self):
        code = AppsumoCode.objects.create(code="12345678")
        assert not code.refunded

        code.refunded_before = timezone.now()
        assert code.refunded

    def test_exists(self):
        assert not AppsumoCode.exists("12345678")
        AppsumoCode.objects.create(code="12345678")
        assert AppsumoCode.exists("12345678")

    def test_available(self):
        code = AppsumoCode.objects.create(code="12345678")
        assert AppsumoCode.available("12345678")
        code.redeemed = timezone.now()
        code.save()
        assert not AppsumoCode.available("12345678")

    def redeem_by_user(self):
        user = CustomUser.objects.create_user("test")
        code = AppsumoCode.objects.create(code="12345678")

        code.redeem_by_user(user)

        assert code.redeemed_by == user
        assert code.redeemed is not None

    def test_redeem_new_team(self):
        user = CustomUser.objects.create_user("test")
        code = AppsumoCode.objects.create(code="12345678")

        code.redeem_new_team("test_team", user)

        assert code.redeemed_by == user
        assert code.redeemed is not None

        assert user.teams.count() == 1
        team = user.teams.first()
        assert team.name == "test_team"


class TestAppsumoReview:
    def test_add_to_team(self):
        team = Team.objects.create(name="test_team")
        review = AppsumoReview(
            review_link="https://appsumo.com/products/marketplace-gyana/#r678678"
        )

        assert not hasattr(review, "team")
        review.add_to_team(team)
        assert review.team == team


class TestUploadedCodes:
    def test_create(self):
        data = SimpleUploadedFile(
            "test-uploaded.csv",
            b"12345678\nABCDEFGH\nQWERTYUI",
        )

        uploaded_codes = UploadedCodes(data=data)
        uploaded_codes.save()

        assert uploaded_codes.success

        codes = AppsumoCode.objects.all()
        assert len(codes) == 3
        assert {c.code for c in codes} == {"12345678", "ABCDEFGH", "QWERTYUI"}


class TestPurchasedCodes:
    def test_create(self):
        AppsumoCode.objects.bulk_create(
            [AppsumoCode(code=code) for code in ("12345678", "ABCDEFGH", "QWERTYUI")]
        )

        data = SimpleUploadedFile(
            "test-redeemed-derived-49-usd.csv",
            b"12345678\nABCDEFGH",
        )

        purchased_codes = PurchasedCodes(data=data, deal=AppsumoCode.Deal.USD_49)
        purchased_codes.save()

        assert purchased_codes.success

        codes = AppsumoCode.objects.order_by("created").all()
        assert codes[0].code == "12345678"
        assert codes[0].deal == AppsumoCode.Deal.USD_49

        assert codes[1].code == "ABCDEFGH"
        assert codes[1].deal == AppsumoCode.Deal.USD_49

        assert codes[2].code == "QWERTYUI"
        assert codes[2].deal is None


class TestRefundedCodes:
    def test_create(self):
        AppsumoCode.objects.create(
            code="12345678", refunded_before=datetime(2021, 9, 1, 0, 0, 0)
        )
        AppsumoCode.objects.create(
            code="ABCDEFGH", refunded_before=datetime(2021, 12, 1, 0, 0, 0)
        )
        AppsumoCode.objects.create(code="QWERTYUI")
        AppsumoCode.objects.create(code="ASDFGHJK")

        data = SimpleUploadedFile(
            "test-refunded-snapshot.csv",
            b"12345678\nABCDEFGH\nQWERTYUI",
        )

        refunded_codes = RefundedCodes(
            data=data, downloaded=timezone.make_aware(datetime(2021, 10, 1, 0, 0, 0))
        )
        refunded_codes.save()

        assert refunded_codes.success

        codes = AppsumoCode.objects.order_by("created").all()
        assert codes[0].code == "12345678"
        # previous date overriden
        assert codes[0].refunded_before == timezone.make_aware(
            datetime(2021, 10, 1, 0, 0, 0)
        )

        assert codes[1].code == "ABCDEFGH"
        # later date unchanged
        assert codes[1].refunded_before == timezone.make_aware(
            datetime(2021, 12, 1, 0, 0, 0)
        )

        assert codes[2].code == "QWERTYUI"
        assert codes[2].refunded_before == timezone.make_aware(
            datetime(2021, 10, 1, 0, 0, 0)
        )

        assert codes[3].code == "ASDFGHJK"
        assert codes[3].refunded_before is None
