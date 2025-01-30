import hashlib

import pandas as pd
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction

from apps.base.clients import SLUG
from apps.base.models import BaseModel
from apps.base.storage import get_public_storage
from apps.teams import roles
from apps.teams.models import Team


class CustomUser(AbstractUser):
    """
    Add additional fields to the user model here.

    https://docs.djangoproject.com/en/3.2/topics/auth/customizing/#extending-django-s-default-user
    """

    avatar = models.FileField(
        storage=get_public_storage(),
        upload_to="profile-pictures/",
        null=True,
        blank=True,
    )
    onboarded = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    def get_display_name(self):
        if self.get_full_name().strip():
            return self.get_full_name()

        return self.email

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        else:
            return "https://www.gravatar.com/avatar/{}?s=128&d=identicon".format(
                self.gravatar_id
            )

    @property
    def gravatar_id(self):
        # https://en.gravatar.com/site/implement/hash/
        return hashlib.md5(self.email.lower().strip().encode("utf-8")).hexdigest()

    @property
    def teams_admin_of(self):
        return Team.objects.filter(
            membership__role=roles.ROLE_ADMIN, membership__user=self
        ).all()

    @property
    def is_creators_only_integration(self):
        return self.created_by.integration_set.count() == 1


class ApprovedWaitlistEmail(BaseModel):
    email = models.EmailField(unique=True)

    @staticmethod
    def check_approved(email):
        return ApprovedWaitlistEmail.objects.filter(email__iexact=email).exists()


class ApprovedWaitlistEmailBatch(BaseModel):
    data = models.FileField(
        upload_to=(
            f"{SLUG}/approved_waitlist_batch" if SLUG else "approved_waitlist_batch"
        )
    )
    success = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        emails = pd.read_csv(self.data.file.open(), names=["email"]).email.tolist()

        with transaction.atomic():
            for email in emails:
                ApprovedWaitlistEmail.objects.get_or_create(email=email.lower())

            self.success = True
            super().save(*args, **kwargs)
