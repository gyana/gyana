import pandas as pd
from apps.base.models import BaseModel
from apps.teams.models import Team
from django.conf import settings
from django.db import models
from django.db.models.fields import DateTimeField


class AppsumoCode(BaseModel):

    code = models.CharField(max_length=8, unique=True)
    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)
    redeemed = models.DateTimeField(null=True)
    redeemed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.code


# upload redeemed and refunded codes via the admin interface


class RedeemedCodes(BaseModel):
    data = models.FileField()
    downloaded = DateTimeField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        codes = pd.read_csv(self.data.url)


class RefundedCodes(BaseModel):
    data = models.FileField()
    downloaded = DateTimeField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        filename = self.data.url
