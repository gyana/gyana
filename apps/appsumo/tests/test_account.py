import pytest
from apps.appsumo.account import get_deal
from apps.appsumo.models import AppsumoCode
from django.utils import timezone

M = 1_000_000


@pytest.fixture
def codes():
    usd_49 = [
        AppsumoCode(code="usd_49" + str(idx) * 2, deal=AppsumoCode.Deal.USD_49)
        for idx in range(5)
    ]
    usd_179 = [
        AppsumoCode(code="usd_179" + str(idx), deal=AppsumoCode.Deal.USD_179)
        for idx in range(5)
    ]
    usd_59 = [
        AppsumoCode(code="usd_59" + str(idx) * 2, deal=AppsumoCode.Deal.USD_59)
        for idx in range(10)
    ]

    return usd_49, usd_179, usd_59


def test_deal_49(codes):

    usd_49, usd_179, usd_59 = codes

    # a user has a single code
    assert get_deal(usd_49[:1])["rows"] == M

    # a user stacks four codes
    assert get_deal(usd_49[:4])["rows"] == 10 * M

    # a user stacks more than four codes
    assert get_deal(usd_49[:5])["rows"] == 10 * M

    # a user stacks two codes -> $59 deal
    assert get_deal(usd_49[:2])["rows"] == 2 * M

    # overrides any other stacking
    assert get_deal(usd_49[:4] + usd_179[:2] + usd_59[:5])


def test_deal_179_usd(codes):

    _, usd_179, usd_59 = codes

    # a user has a single code
    assert get_deal(usd_179[:1])["rows"] == 5 * M

    # a user purchased a second code at $59
    assert get_deal(usd_179[:1] + usd_59[:1])["rows"] == 10 * M

    # but no more
    assert get_deal(usd_179[:1] + usd_59[:5])["rows"] == 10 * M


def test_deal_59_usd(codes):

    *_, usd_59 = codes

    # a user has 0 codes
    assert get_deal(usd_59[:0])["rows"] == 0

    # a user has a single code
    assert get_deal(usd_59[:1])["rows"] == M

    # a user has 2 codes
    assert get_deal(usd_59[:2])["rows"] == 2 * M

    # a user has 5 codes
    assert get_deal(usd_59[:5])["rows"] == 10 * M

    # a user has 10 codes
    assert get_deal(usd_59[:10])["rows"] == 10 * M


def test_refunded(codes):
    *_, usd_59 = codes

    usd_59[0].refunded_before = timezone.now()

    assert get_deal(usd_59[:1])["rows"] == 0
