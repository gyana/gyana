from django import forms
from django.forms.widgets import HiddenInput

from .models import Filter

IBIS_TO_PREDICATE = {"String": "string_predicate", "Int64": "integer_predicate"}
IBIS_TO_VALUE = {"String": "string_value", "Int64": "integer_value"}


class ColumnChoices:
    def __init__(self, *args, **kwargs):
        # https://stackoverflow.com/a/30766247/15425660

        if "columns" in kwargs:
            self.columns = kwargs.pop("columns")
            super().__init__(*args, **kwargs)
            self.fields["column"].choices = self.columns


def get_filter_form(column_type=None):

    fields = ["widget", "column"]
    if column_type is not None:
        fields += [IBIS_TO_PREDICATE[column_type.name], IBIS_TO_VALUE[column_type.name]]

    meta = type(
        "Meta",
        (),
        {
            "model": Filter,
            "fields": fields,
            "widgets": {"widget": HiddenInput()},
        },
    )

    filter_form = type(
        "FilterForm",
        (
            ColumnChoices,
            forms.ModelForm,
        ),
        {"Meta": meta, "column": forms.ChoiceField(choices=())},
    )

    return filter_form
