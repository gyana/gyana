from django.db import models

DEFAULT_ROW_LIMIT = 50_000
DEFAULT_CREDIT_LIMIT = 100


def get_row_limit(self):
    from apps.appsumo.account import get_deal

    if self.override_row_limit is not None:
        return self.override_row_limit

    rows = max(
        DEFAULT_ROW_LIMIT,
        get_deal(self.appsumocode_set.all())["rows"],
    )

    # extra 1M for writing a review
    if hasattr(self, "appsumoreview"):
        rows += 1_000_000

    rows += self.appsumoextra_set.aggregate(models.Sum("rows"))["rows__sum"] or 0

    return rows


def get_credits(self):
    from apps.appsumo.account import get_deal

    return max(DEFAULT_CREDIT_LIMIT, get_deal(self.appsumocode_set.all())["credits"])
