from pathlib import Path
from typing import List

import pandas as pd

from apps.appsumo.models import AppsumoCode

from .config import APPSUMO_PLANS

# business logic for AppSumo pricing plans


def get_deal(appsumo_codes: List[AppsumoCode]):

    active_codes = [code for code in appsumo_codes if not code.refunded]
    stacked = len(active_codes)

    if stacked == 0:
        return {"rows": 0, "credits": 0}

    # handle special cases for previous plans

    usd_49 = len(
        [code for code in active_codes if code.deal == AppsumoCode.Deal.USD_49]
    )
    if usd_49 >= 4:
        return APPSUMO_PLANS[AppsumoCode.Deal.USD_49][4]

    usd_179 = len(
        [code for code in active_codes if code.deal == AppsumoCode.Deal.USD_179]
    )
    if usd_179 >= 1:
        return APPSUMO_PLANS[AppsumoCode.Deal.USD_179][min(stacked, 2)]

    # otherwise they go onto most recent plan
    # the stacking information is identical for AppSumo Select
    return APPSUMO_PLANS[AppsumoCode.Deal.USD_59][min(stacked, 5)]


# helper utility to generate from AppSumo point-in-time snapshots
# !cp redeemed-snapshot-2021-06-25.csv redeemed-derived-49-usd.csv
# generate_diff_csv("redeemed-snapshot-2021-06-25.csv", "redeemed-snapshot-2021-07-01.csv", "redeemed-derived-179-usd.csv")
# generate_diff_csv("redeemed-snapshot-2021-07-01.csv", "redeemed-snapshot-2021-08-27.csv", "redeemed-derived-59-usd.csv")

APPSUMO_DATA_DIR = Path("apps/appsumo/data")


def generate_diff_csv(start, end, diff):
    df_1 = pd.read_csv(APPSUMO_DATA_DIR / start, names=["code"]).code.tolist()
    df_2 = pd.read_csv(APPSUMO_DATA_DIR / end, names=["code"]).code.tolist()
    pd.DataFrame({"codes": list(set(df_2) - set(df_1))}).to_csv(
        APPSUMO_DATA_DIR / diff, header=False, index=False
    )
