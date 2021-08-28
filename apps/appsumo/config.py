from datetime import datetime

from django.utils.timezone import utc

# plans update at midday Austin time

APPSUMO_PLANS = {
    # original plan we launched with $49 and 4-stack
    datetime(2021, 6, 25, 18, 0, 0).replace(tzinfo=utc): {
        1: {"rows": 1_000_000, "credits": 10_000},
        2: {"rows": 2_000_000, "credits": 10_000},
        3: {"rows": 3_000_000, "credits": 10_000},
        4: {"rows": 10_000_000, "credits": 50_000},
    },
    # temporary new plan at $179 per code with stacking
    datetime(2021, 7, 1, 18, 0, 0).replace(tzinfo=utc): {
        1: {"rows": 1_000_000, "credits": 10_000},
        2: {"rows": 2_000_000, "credits": 20_000},
        3: {"rows": 3_000_000, "credits": 30_000},
        4: {"rows": 5_000_000, "credits": 40_000},
        5: {"rows": 10_000_000, "credits": 50_000},
    },
    # current plan (pre-Select)
    datetime(2022, 1, 1, 18, 0, 0).replace(tzinfo=utc): {
        1: {"rows": 1_000_000, "credits": 10_000},
        2: {"rows": 2_000_000, "credits": 20_000},
        3: {"rows": 3_000_000, "credits": 30_000},
        4: {"rows": 5_000_000, "credits": 40_000},
        5: {"rows": 10_000_000, "credits": 50_000},
    },
    # todo: appsumo select plan
}

APPSUMO_MAX_STACK = 5
