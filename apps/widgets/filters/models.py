from apps.widgets.models import Widget
from django.db import models


class Filter(models.Model):
    class Type(models.TextChoices):
        INTEGER = "INTEGER", "Integer"
        STRING = "STRING", "String"

    class IntegerPredicate(models.TextChoices):
        EQUAL = "equal", "is equal to"
        NEQUAL = "nequal", "is not equal to"

    class StringPredicate(models.TextChoices):
        STARTSWITH = "starts_with", "starts with"
        ENDSWITH = "ends_with", "ends with"

    widget = models.ForeignKey(Widget, on_delete=models.CASCADE)

    column = models.CharField(max_length=300)
    type = models.CharField(max_length=8, choices=Type.choices)

    integer_predicate = models.CharField(
        max_length=16, choices=IntegerPredicate.choices, null=True, blank=True
    )
    integer_value = models.BigIntegerField(null=True, blank=True)

    string_predicate = models.CharField(
        max_length=16, choices=StringPredicate.choices, null=True, blank=True
    )
    string_value = models.TextField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.column
