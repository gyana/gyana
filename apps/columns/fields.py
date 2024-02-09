from django import forms
from ibis.expr.datatypes import Array, Struct

from apps.base.core.utils import create_column_choices
from apps.base.widgets import SelectWithDisable


class ColumnField(forms.ChoiceField):
    widget = SelectWithDisable

    def __init__(self, *args, **kwargs):
        self.disable_struct_array = kwargs.pop("disable_struct_array", False)
        self.allowed_types = kwargs.pop("allowed_types", None)
        self.disabled_types = kwargs.pop("disabled_types", None)
        self.message = kwargs.pop("message", None)

        super().__init__(*args, **kwargs)

    def _set_column_choices(self, schema):
        self.choices = create_column_choices(schema)

        if self.disable_struct_array:
            self.widget.disabled = {
                name: "Currently, you cannot use this column type here."
                for name, type_ in schema.items()
                if isinstance(type_, (Struct, Array))
            }

        if self.allowed_types:
            self.widget.disabled = {
                name: self.message
                for name, type_ in schema.items()
                if type_ not in self.allowed_types
            }

        if self.disabled_types:
            self.widget.disabled = {
                name: self.message
                for name, type_ in schema.items()
                if type_ in self.disabled_types
            }
