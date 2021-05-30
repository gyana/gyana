from apps.widgets.models import Widget
from django import forms
from django.forms.widgets import HiddenInput

from .models import Filter

IBIS_TO_PREDICATE = {"String": "string_predicate", "Int64": "numeric_predicate"}
IBIS_TO_VALUE = {"String": "string_value", "Int64": "integer_value"}

IBIS_TO_PREFIX = {"String": "string_", "Int64": "integer_"}


class ColumnChoices:
    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660

        if "columns" in kwargs:
            self.columns = kwargs.pop("columns")
            super().__init__(*args, **kwargs)
            self.fields["column"].choices = self.columns


class FilterForm(forms.ModelForm):
    class Meta:
        fields = (
            "column",
            "string_predicate",
            "numeric_predicate",
            "string_value",
            "integer_value",
        )

    def __init__(self, *args, **kwargs):

        self.schema = kwargs.pop("schema")

        super().__init__(*args, **kwargs)

        column_type = None

        # data populated by GET request in live form
        if (data := kwargs.get("data")) is not None:
            name = data[f"{kwargs['prefix']}-name"]
            if name in self.schema:
                column_type = self.schema[name].name

        # data populated from database in initial render
        elif self.instance.column in self.schema:
            column_type = self.schema[self.instance.column].name

        # remove all fields that are not for this type
        deletions = [v for k, v in IBIS_TO_PREFIX.items() if k != column_type]

        for deletion in deletions:
            self.fields = {
                k: v for k, v in self.fields.items() if not k.startswith(deletion)
            }


def get_filter_form(parent_fk, column_type=None):

    fields = ["column", parent_fk]
    if column_type is not None:
        fields += [IBIS_TO_PREDICATE[column_type.name], IBIS_TO_VALUE[column_type.name]]

    meta = type(
        "Meta",
        (),
        {"model": Filter, "fields": fields, "widgets": {parent_fk: HiddenInput()}},
    )

    return type(
        "FilterForm",
        (
            ColumnChoices,
            forms.ModelForm,
        ),
        {"Meta": meta, "column": forms.ChoiceField(choices=())},
    )
