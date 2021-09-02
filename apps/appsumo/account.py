from django.utils import timezone

from .config import APPSUMO_MAX_STACK, APPSUMO_PLANS

# business logic for AppSumo pricing plans


def get_row_count(appsumo_queryset, review=False):

    active_codes = appsumo_queryset.filter(refunded_before=None).all()
    stacked = len(active_codes)

    # to determine your plan, take the most recently purchased code
    most_recent = max(
        (
            code.purchased_before
            for code in active_codes
            if code.purchased_before is not None
        ),
        default=timezone.now(),
    )
    best_plan = next(
        plan for expired, plan in APPSUMO_PLANS.items() if expired >= most_recent
    )
    max_stack = list(best_plan.keys())[-1]
    rows = best_plan.get(min(stacked, max_stack))["rows"]

    # extra 1M for writing a review
    if review:
        rows += 1_000_000

    return rows
