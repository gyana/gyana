import pandas as pd
from apps.base.clients import SLUG
from apps.base.models import BaseModel
from apps.teams.models import Team
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models, transaction

# review ids are incrementing integers, currently at 6 digits
appsumo_review_regex = RegexValidator(
    r"^https:\/\/appsumo\.com\/products\/marketplace-gyana\/\#r[0-9]{6,9}$",
    "Paste the exact link as displayed on AppSumo",
)

# after we upload the codes to AppSumo, they provide two downloads:
# - redeemed codes = all sold codes that are not refunded
# - refunded codes = all sold codes that are refunded
# there is no historical data, only point in time snapshots based on when
# we have downloaded the CSV file. Fortunately, we downloaded a snapshot of
# redeemed codes just after the two deals ended (unfortunately not refunded).


class AppsumoCode(BaseModel):
    class Deal(models.TextChoices):
        USD_49 = "usd_49", "Launch deal $49 (24/03/21 - 25/06/21)"
        USD_179 = "usd_179", "Temporary deal $179 (25/06/21 - 01/07/21)"
        USD_59 = "usd_59", "Final deal $59 (01/07/21 - 26/08/21)"
        # add the AppSumo Select deal here

    code = models.CharField(max_length=8, unique=True)
    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)

    # possibly null for a refunded code
    deal = models.CharField(max_length=8, null=True, choices=Deal.choices)
    redeemed = models.DateTimeField(null=True)
    refunded_before = models.DateTimeField(null=True)

    redeemed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )

    @property
    def refunded(self):
        return self.refunded_before is not None

    def __str__(self):
        return self.code


class AppsumoReview(BaseModel):

    review_link = models.URLField(
        unique=True,
        validators=[appsumo_review_regex],
        error_messages={
            "unique": "A user has linked to this review for their team. If you think this is a mistake, reach out to support and we'll sort it out for you."
        },
    )
    team = models.OneToOneField(Team, on_delete=models.CASCADE)

    def __str__(self):
        return self.review_link


class AppsumoExtra(BaseModel):

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    rows = models.BigIntegerField()
    reason = models.TextField()


# upload redeemed and refunded codes via the admin interface


class UploadedCodes(BaseModel):
    data = models.FileField(
        upload_to=f"{SLUG}/uploaded_codes" if SLUG else "uploaded_codes"
    )
    success = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        codes = pd.read_csv(self.data.file.open(), names=["code"]).code.tolist()

        with transaction.atomic():
            AppsumoCode.objects.bulk_create([AppsumoCode(code=code) for code in codes])
            self.success = True
            super().save(*args, **kwargs)


class PurchasedCodes(BaseModel):
    data = models.FileField(
        upload_to=f"{SLUG}/purchased_codes" if SLUG else "purchased_codes"
    )
    deal = models.CharField(max_length=8, choices=AppsumoCode.Deal.choices)
    success = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        codes = pd.read_csv(self.data.file.open(), names=["code"]).code.tolist()

        appsumo_codes = AppsumoCode.objects.filter(code__in=codes).all()

        # if the code does not exist, we have a big problem
        assert len(appsumo_codes) == len(codes)

        with transaction.atomic():
            for appsumo_code in appsumo_codes:
                appsumo_code.deal = self.deal

            AppsumoCode.objects.bulk_update(appsumo_codes, ["deal"])

            self.success = True
            super().save(*args, **kwargs)


class RefundedCodes(BaseModel):
    data = models.FileField(
        upload_to=f"{SLUG}/refunded_codes" if SLUG else "refunded_codes"
    )
    downloaded = models.DateTimeField()
    success = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        codes = pd.read_csv(self.data.file.open(), names=["code"]).code.tolist()

        # prefetch all the relevant codes
        appsumo_codes = AppsumoCode.objects.filter(code__in=codes).all()

        # if the code does not exist, we have a big problem
        assert len(appsumo_codes) == len(codes)

        with transaction.atomic():

            for appsumo_code in appsumo_codes:
                if (
                    appsumo_code.refunded_before is None
                    or appsumo_code.refunded_before > self.downloaded
                ):
                    appsumo_code.refunded_before = self.downloaded

            AppsumoCode.objects.bulk_update(appsumo_codes, ["refunded_before"])

            self.success = True
            super().save(*args, **kwargs)
