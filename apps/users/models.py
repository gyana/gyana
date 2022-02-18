import hashlib

import pandas as pd
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from storages.backends.gcloud import GoogleCloudStorage

from apps.base.clients import SLUG
from apps.base.models import BaseModel
from apps.teams import roles
from apps.teams.models import Team


class CustomUser(AbstractUser):
    """
    Add additional fields to the user model here.

    https://docs.djangoproject.com/en/3.2/topics/auth/customizing/#extending-django-s-default-user
    """

    class CompanyIndustry(models.TextChoices):
        AGENCY = "agency", "Agency"
        SOFTWARE = "software", "Software"
        ECOMMERCE = "ecommerce", "E-commerce"
        CONSULTING = "consulting", "Consulting"
        EDUCATION = "education", "Education"
        FINTECH = "fintech", "Fintech"
        NONPROFIT = "nonprofit", "Nonprofit"
        OTHER = "other", "Other"

    class CompanyRole(models.TextChoices):
        LEADERSHIP = "leadership", "Leadership"
        MARKETING = "marketing", "Marketing"
        BUSINESS_ANALYST = "business analyst", "Business Analyst"
        DATA_SCIENTIST = "data scientist", "Data Scientist"
        PRODUCT_MANAGER = "product manager", "Product Manager"
        DEVELOPER = "developer", "Developer"
        STUDENT = "student", "Student"
        SALES = "sales", "Sales"
        OTHER = "other", "Other"

    class CompanySize(models.TextChoices):
        ONE = "1", "Just me"
        TWO_TO_TEN = "2-10", "2-10"
        ELEVEN_TO_FIFTY = "11-50", "11-50"
        FIFTY_ONE_TO_TWO_HUNDRED = "51-200", "51-200"
        TWO_HUNDRED_AND_ONE_TO_ONE_THOUSAND = "201-1000", "201-1000"
        MORE_THAN_ONE_THOUSAND = "more than 1000", "More than 1000"

    avatar = models.FileField(
        storage=GoogleCloudStorage(
            bucket_name=settings.GS_PUBLIC_BUCKET_NAME,
            cache_control=settings.GS_PUBLIC_CACHE_CONTROL,
            querystring_auth=False,
        ),
        upload_to="profile-pictures/",
        null=True,
        blank=True,
    )
    onboarded = models.BooleanField(default=False)
    company_industry = models.CharField(
        max_length=16, null=True, choices=CompanyIndustry.choices
    )
    company_role = models.CharField(
        max_length=32, null=True, choices=CompanyRole.choices
    )
    company_size = models.CharField(
        max_length=16, null=True, choices=CompanySize.choices
    )
    marketing_allowed = models.BooleanField(null=True)

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
        upload_to=f"{SLUG}/approved_waitlist_batch"
        if SLUG
        else "approved_waitlist_batch"
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
