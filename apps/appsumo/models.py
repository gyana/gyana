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


class AppsumoCode(BaseModel):

    code = models.CharField(max_length=8, unique=True)
    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)

    purchased_before = models.DateTimeField(null=True)
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


# upload redeemed and refunded codes via the admin interface


class UploadedCodes(BaseModel):
    data = models.FileField(
        upload_to=f"{SLUG}/uploaded_codes" if SLUG else "uploaded_codes"
    )
    downloaded = models.DateTimeField()
    success = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        codes = pd.read_csv(self.data.url, names=["code"]).code.tolist()

        with transaction.atomic():
            AppsumoCode.objects.bulk_create([AppsumoCode(code=code) for code in codes])
            self.success = True
            super().save(*args, **kwargs)


class PurchasedCodes(BaseModel):
    data = models.FileField(
        upload_to=f"{SLUG}/purchased_codes" if SLUG else "purchased_codes"
    )
    downloaded = models.DateTimeField()
    success = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        codes = pd.read_csv(self.data.url, names=["code"]).code.tolist()

        # prefetch all the relevant codes
        len(AppsumoCode.objects.filter(code__in=codes).all())

        with transaction.atomic():

            # if the code does not exist, we have a big problem
            for code in codes:
                appsumo_code = AppsumoCode.objects.get(code=code)
                if (
                    appsumo_code.purchased_before is None
                    or appsumo_code.purchased_before > self.downloaded
                ):
                    appsumo_code.purchased_before = self.downloaded
                    appsumo_code.save()

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
        codes = pd.read_csv(self.data.url, names=["code"]).code.tolist()

        # prefetch all the relevant codes
        len(AppsumoCode.objects.filter(code__in=codes).all())

        with transaction.atomic():

            # if the code does not exist, we have a big problem
            for code in codes:
                appsumo_code = AppsumoCode.objects.get(code=code)
                if (
                    appsumo_code.refunded_before is None
                    or appsumo_code.refunded_before > self.downloaded
                ):
                    appsumo_code.refunded_before = self.downloaded
                    appsumo_code.save()

            self.success = True
            super().save(*args, **kwargs)
