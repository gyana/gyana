from apps.appsumo.models import AppsumoCode

from .config import APPSUMO_PLANS

# business logic for AppSumo pricing plans


def get_deal(appsumo_queryset):

    active_codes = appsumo_queryset.filter(refunded_before=None)
    stacked = active_codes.count()

    if stacked == 0:
        return {"rows": 0, "credits": 0}

    # handle special cases for previous plans

    usd_49 = active_codes.filter(deal=AppsumoCode.Deal.USD_49).count()
    if usd_49 >= 4:
        return APPSUMO_PLANS[AppsumoCode.Deal.USD_49][4]

    usd_179 = active_codes.filter(deal=AppsumoCode.Deal.USD_179).count()
    if usd_179 >= 1:
        return APPSUMO_PLANS[AppsumoCode.Deal.USD_179][min(stacked, 2)]

    # otherwise they go onto most recent plan
    # the stacking information is identical for AppSumo Select
    return APPSUMO_PLANS[AppsumoCode.Deal.USD_59][min(stacked, 5)]
