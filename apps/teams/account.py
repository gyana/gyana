from django.db import models

from .models import Team

DEFAULT_ROW_LIMIT = 50_000
DEFAULT_CREDIT_LIMIT = 100


def get_row_limit(team: Team):
    from apps.appsumo.account import get_deal

    if team.override_row_limit is not None:
        return team.override_row_limit

    rows = max(
        DEFAULT_ROW_LIMIT,
        get_deal(team.appsumocode_set.all())["rows"],
    )

    # extra 1M for writing a review
    if hasattr(team, "appsumoreview"):
        rows += 1_000_000

    rows += team.appsumoextra_set.aggregate(models.Sum("rows"))["rows__sum"] or 0

    return rows


def get_credits(team: Team):
    from apps.appsumo.account import get_deal

    return max(DEFAULT_CREDIT_LIMIT, get_deal(team.appsumocode_set.all())["credits"])
