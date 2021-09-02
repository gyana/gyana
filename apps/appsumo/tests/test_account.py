from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from apps.appsumo.account import get_deal
from apps.appsumo.models import AppsumoCode, PurchasedCodes, UploadedCodes
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

APPSUMO_DATA_DIR = Path("apps/appsumo/data")

UPLOADED = "uploaded.csv"
PURCHASED_49 = "purchased-deal-49-usd.csv"
PURCHASED_179 = "purchased-deal-179-usd.csv"
PURCHASED_59 = "purchased-deal-59-usd.csv"

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
        ),
        downloaded=timezone.make_aware(datetime(2021, 4, 1, 0, 0, 0)),
    ).save()
    for (path, downloaded) in [
        (PURCHASED_49, timezone.make_aware(datetime(2021, 6, 25, 18, 0, 0))),
        (PURCHASED_179, timezone.make_aware(datetime(2021, 7, 1, 18, 0, 0))),
        (PURCHASED_59, timezone.make_aware(datetime(2021, 8, 27))),
    ]:
        PurchasedCodes(
            data=SimpleUploadedFile(
                path,
                open(APPSUMO_DATA_DIR / path, "rb").read(),
            ),
            downloaded=downloaded,
        ).save()


@pytest.mark.django_db
def test_deal_49_usd(setup_purchased_codes):

    purchased_49 = pd.read_csv(
        APPSUMO_DATA_DIR / PURCHASED_49, names=["code"]
    ).code.tolist()

    # a user has a single code
    codes = AppsumoCode.objects.filter(code=purchased_49[0])

    assert get_deal(codes) == M

    # a user stacks four codes
    codes = AppsumoCode.objects.filter(code__in=purchased_49[:4])

    assert get_deal(codes) == 10 * M

    # a user stacks more than four codes
    codes = AppsumoCode.objects.filter(code__in=purchased_49[:10])

    assert get_deal(codes) == 10 * M


@pytest.mark.django_db
def test_deal_179_usd(setup_purchased_codes):

    purchased_49 = pd.read_csv(
        APPSUMO_DATA_DIR / PURCHASED_49, names=["code"]
    ).code.tolist()

    purchased_179 = set(
        pd.read_csv(APPSUMO_DATA_DIR / PURCHASED_179, names=["code"]).code.tolist()
    ) - set(purchased_49)

    # a user has a single code
    codes = AppsumoCode.objects.filter(code=purchased_179[0])

    assert get_deal(codes) == 5 * M
