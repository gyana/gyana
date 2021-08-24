from apps.base.models import BaseModel
from apps.teams.models import Team
from django.db import models


class AppsumoCode(BaseModel):

    code = models.CharField(max_length=8, unique=True)
    team = models.ForeignKey(Team, null=True, on_delete=models.SET_NULL)
    redeemed = models.DateTimeField(null=True)

    def __str__(self):
        return self.code
