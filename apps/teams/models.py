from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from apps.base.models import BaseModel

from . import roles

DEFAULT_ROW_LIMIT = 1_000_000
WARNING_BUFFER = 0.2


class Team(BaseModel):
    name = models.CharField(max_length=100)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="teams", through="Membership"
    )

    row_limit = models.BigIntegerField(default=DEFAULT_ROW_LIMIT)
    # row count is recalculated on a daily basis, or re-counted in certain situations
    # calculating every view is too expensive
    row_count = models.BigIntegerField(default=0)
    row_count_calculated = models.DateTimeField(null=True)
    max_credit = models.IntegerField(default=0)

    def update_row_count(self):
        from apps.tables.models import Table

        self.row_count = (
            Table.available.filter(integration__project__team=self).aggregate(
                models.Sum("num_rows")
            )["num_rows__sum"]
            or 0
        )
        self.row_count_calculated = timezone.now()
        self.save()

    @property
    def warning(self):
        return self.row_limit < self.row_count <= self.row_limit * (1 + WARNING_BUFFER)

    @property
    def enabled(self):
        return self.row_count <= self.row_limit * (1 + WARNING_BUFFER)

    @property
    def tables_dataset_id(self):
        from apps.base.clients import SLUG

        dataset_id = f"team_{self.id:06}_tables"
        if SLUG:
            dataset_id = f"{SLUG}_{dataset_id}"
        return dataset_id

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("teams:detail", args=(self.id,))

    @property
    def current_credit_balance(self):
        last_statement = (
            self.creditstatement_set.latest("created")
            if self.creditstatement_set.first()
            else None
        )
        start_balance = last_statement.balance if last_statement else 0
        transactions = (
            self.credittransaction_set.filter(created__lt=last_statement.created)
            if last_statement
            else self.credittransaction_set
        )
        return (
            start_balance
            + (
                transactions.filter(
                    transaction_type=CreditTransaction.TransactionType.INCREASE,
                ).aggregate(models.Sum("amount"))["amount__sum"]
                or 0
            )
            - (
                transactions.filter(
                    transaction_type=CreditTransaction.TransactionType.DECREASE,
                ).aggregate(models.Sum("amount"))["amount__sum"]
                or 0
            )
        )


class Membership(BaseModel):
    """
    A user's team membership
    """

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=roles.ROLE_CHOICES)


# Credit system design motivated by https://stackoverflow.com/a/29713230


class CreditTransaction(models.Model):
    class Meta:
        ordering = ("-created",)

    class TransactionType(models.TextChoices):
        DECREASE = "decrease", "Decrease"
        INCREASE = "increase", "Increase"

    created = models.DateTimeField(auto_now_add=True, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    amount = models.IntegerField()


class CreditStatement(models.Model):
    class Meta:
        ordering = ("-created",)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    balance = models.IntegerField()
    credits_used = models.IntegerField()
    credits_received = models.IntegerField()
