from datetime import datetime

from apps.appsumo.models import AppsumoCode
from django.utils import timezone

# plans update at midday Austin time

APPSUMO_PLANS = {
    # original plan we launched with $49 and 4-stack
    AppsumoCode.Deal.USD_49: {
        4: {"rows": 10_000_000, "credits": 50_000},
    },
    # temporary new plan at $179 per code with stacking
    AppsumoCode.Deal.USD_179: {
        1: {"rows": 5_000_000, "credits": 40_000},
        2: {"rows": 10_000_000, "credits": 50_000},
    },
    # current plan (pre-Select)
    AppsumoCode.Deal.USD_59: {
        1: {"rows": 1_000_000, "credits": 10_000},
        2: {"rows": 2_000_000, "credits": 20_000},
        3: {"rows": 3_000_000, "credits": 30_000},
        4: {"rows": 5_000_000, "credits": 40_000},
        5: {"rows": 10_000_000, "credits": 50_000},
    },
    # todo: appsumo select plan
}
