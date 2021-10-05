from apps.appsumo.models import AppsumoCode

# plans update at midday Austin time

SELECT_TIERS = {
    1: {"rows": 1_000_000, "credits": 10_000},
    2: {"rows": 2_000_000, "credits": 20_000, "cnames": 3, "sub_accounts": 5},
    3: {
        "rows": 3_000_000,
        "credits": 30_000,
        "cnames": 6,
        "sub_accounts": 10,
        "white_labeling": True,
    },
    4: {
        "rows": 5_000_000,
        "credits": 40_000,
        "cnames": 10,
        "sub_accounts": 25,
        "white_labeling": True,
    },
    5: {
        "rows": 10_000_000,
        "credits": 50_000,
        "cnames": 25,
        "sub_accounts": -1,
        "white_labeling": True,
    },
}

# automatically grandfather to a stacked SELECT tier

APPSUMO_PLANS = {
    # original plan we launched with $49 and 4-stack
    AppsumoCode.Deal.USD_49: {
        4: {
            **SELECT_TIERS[5],
            "rows": 10_000_000,
            "credits": 50_000,
        },
    },
    # temporary new plan at $179 per code with stacking
    AppsumoCode.Deal.USD_179: {
        1: {**SELECT_TIERS[4], "rows": 5_000_000, "credits": 40_000},
        2: {**SELECT_TIERS[5], "rows": 10_000_000, "credits": 50_000},
    },
    # current plan (pre-Select)
    AppsumoCode.Deal.USD_59: SELECT_TIERS,
    # Select
    AppsumoCode.Deal.SELECT: SELECT_TIERS,
}
