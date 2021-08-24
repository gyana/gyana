import pandas as pd
from apps.base.models import BaseModel
from apps.teams.models import Team
from django.conf import settings
from django.db import models, transaction


class AppsumoCode(BaseModel):

    code = models.CharField(max_length=8, unique=True)
    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)

    bought_before = models.DateTimeField(null=True)
    redeemed = models.DateTimeField(null=True)
    refunded_before = models.DateTimeField(null=True)

    redeemed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.code


# upload redeemed and refunded codes via the admin interface


class PurchasedCodes(BaseModel):
    data = models.FileField()
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
                    appsumo_code.bought_before is not None
                    or appsumo_code.bought_before > self.downloaded
                ):
                    appsumo_code.bought_before = self.downloaded
                    appsumo_code.save()

            self.success = True
            super().save(*args, **kwargs)


class RefundedCodes(BaseModel):
    data = models.FileField()
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
                    appsumo_code.refunded_before is not None
                    or appsumo_code.refunded_before > self.downloaded
                ):
                    appsumo_code.refunded_before = self.downloaded
                    appsumo_code.save()

            self.success = True
            super().save(*args, **kwargs)
