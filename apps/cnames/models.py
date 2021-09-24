import re

from apps.base.models import BaseModel
from apps.teams.models import Team
from django.core.validators import RegexValidator
from django.db import models

domain_regex = RegexValidator(
    # https://github.com/kvesteri/validators/blob/master/validators/domain.py
    re.compile(
        r"^(?:[a-zA-Z0-9]"  # First character of the domain
        r"(?:[a-zA-Z0-9-_]{0,61}[A-Za-z0-9])?\.)"  # Sub domain + hostname
        r"+[A-Za-z0-9][A-Za-z0-9-_]{0,61}"  # First 61 characters of the gTLD
        r"[A-Za-z]$"  # Last character of the gTLD
    ),
    "Must be a valid domain",
)


class CName(BaseModel):
    domain = models.CharField(max_length=253, validators=[domain_regex])
    team = models.OneToOneField(Team, on_delete=models.CASCADE)

    def __str__(self):
        return self.domain
