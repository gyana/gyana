from pathlib import Path

import pandas as pd
import pytest
from apps.appsumo.account import get_deal
from apps.appsumo.models import AppsumoCode, PurchasedCodes, UploadedCodes
from django.core.files.uploadedfile import SimpleUploadedFile

APPSUMO_DATA_DIR = Path("apps/appsumo/data")

UPLOADED = "uploaded.csv"
PURCHASED_49 = "redeemed-derived-49-usd.csv"
PURCHASED_179 = "redeemed-derived-179-usd.csv"
PURCHASED_59 = "redeemed-derived-59-usd.csv"

M = 1_000_000

# helper utility to generate from AppSumo point-in-time snapshots
# !cp redeemed-snapshot-2021-06-25.csv redeemed-derived-49-usd.csv
# generate_diff_csv("redeemed-snapshot-2021-06-25.csv", "redeemed-snapshot-2021-07-01.csv", "redeemed-derived-179-usd.csv")
# generate_diff_csv("redeemed-snapshot-2021-07-01.csv", "redeemed-snapshot-2021-08-27.csv", "redeemed-derived-59-usd.csv")


def generate_diff_csv(start, end, diff):
    df_1 = pd.read_csv(APPSUMO_DATA_DIR / start, names=["code"]).code.tolist()
    df_2 = pd.read_csv(APPSUMO_DATA_DIR / end, names=["code"]).code.tolist()
    pd.DataFrame({"codes": list(set(df_2) - set(df_1))}).to_csv(
        APPSUMO_DATA_DIR / diff, header=False, index=False
    )


@pytest.fixture
def setup_purchased_codes():
    UploadedCodes(
        data=SimpleUploadedFile(
            UPLOADED,
            open(APPSUMO_DATA_DIR / UPLOADED, "rb").read(),
        )
    ).save()
    for (path, deal) in [
        (PURCHASED_49, AppsumoCode.Deal.USD_49),
        (PURCHASED_179, AppsumoCode.Deal.USD_179),
        (PURCHASED_59, AppsumoCode.Deal.USD_59),
    ]:
        PurchasedCodes(
            data=SimpleUploadedFile(
                path,
                open(APPSUMO_DATA_DIR / path, "rb").read(),
            ),
            deal=deal,
        ).save()


@pytest.mark.django_db
def test_deal_49_usd(setup_purchased_codes):

    purchased_49 = pd.read_csv(
        APPSUMO_DATA_DIR / PURCHASED_49, names=["code"]
    ).code.tolist()

    # a user has a single code
    codes = AppsumoCode.objects.filter(code=purchased_49[0])

    assert get_deal(codes)["rows"] == M

    # a user stacks four codes
    codes = AppsumoCode.objects.filter(code__in=purchased_49[:4])

    assert get_deal(codes)["rows"] == 10 * M

    # a user stacks more than four codes
    codes = AppsumoCode.objects.filter(code__in=purchased_49[:10])

    assert get_deal(codes)["rows"] == 10 * M

    # a user stacks two codes -> $59 deal
    codes = AppsumoCode.objects.filter(code__in=purchased_49[:2])

    assert get_deal(codes)["rows"] == 2 * M


@pytest.mark.django_db
def test_deal_179_usd(setup_purchased_codes):

    purchased_179 = pd.read_csv(
        APPSUMO_DATA_DIR / PURCHASED_179, names=["code"]
    ).code.tolist()

    # a user has a single code
    codes = AppsumoCode.objects.filter(code=purchased_179[0])

    assert get_deal(codes)["rows"] == 5 * M

    purchased_59 = pd.read_csv(
        APPSUMO_DATA_DIR / PURCHASED_59, names=["code"]
    ).code.tolist()

    # a user purchased a second code at $59
    codes = AppsumoCode.objects.filter(code__in=purchased_179[:1] + purchased_59[:1])

    assert get_deal(codes)["rows"] == 10 * M

    codes = AppsumoCode.objects.filter(code__in=purchased_179[:1] + purchased_59[:9])

    assert get_deal(codes)["rows"] == 10 * M


@pytest.mark.django_db
def test_deal_59_usd(setup_purchased_codes):

    purchased_59 = pd.read_csv(
        APPSUMO_DATA_DIR / PURCHASED_59, names=["code"]
    ).code.tolist()

    # a user has 0 codes
    codes = AppsumoCode.objects.filter(code__in=[])

    assert get_deal(codes)["rows"] == 0

    # a user has a single code
    codes = AppsumoCode.objects.filter(code=purchased_59[0])

    assert get_deal(codes)["rows"] == M

    # a user has 2 codes
    codes = AppsumoCode.objects.filter(code__in=purchased_59[:2])

    assert get_deal(codes)["rows"] == 2 * M

    # a user has 5 codes
    codes = AppsumoCode.objects.filter(code__in=purchased_59[:5])

    assert get_deal(codes)["rows"] == 10 * M

    # a user has 10 codes
    codes = AppsumoCode.objects.filter(code__in=purchased_59[:10])

    assert get_deal(codes)["rows"] == 10 * M
