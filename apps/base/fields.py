from django import forms
from django.contrib.postgres.fields import ArrayField
from ibis.expr.datatypes import Struct, Array

from apps.base.core.utils import create_column_choices
from apps.base.widgets import MultiSelect


class ChoiceArrayField(ArrayField):
    """
    A field that allows us to store an array of choices.

    Uses Django 1.9's postgres ArrayField
    and a MultipleChoiceField for its formfield.

    Usage:

        choices = ChoiceArrayField(models.CharField(max_length=...,
                                                    choices=(...,)),
                                   default=[...])
    """

    def formfield(self, **kwargs):
        defaults = {
            "form_class": forms.MultipleChoiceField,
            "choices": self.base_field.choices,
            "widget": MultiSelect,
        }
        defaults.update(kwargs)
        # Skip our parent's formfield implementation completely as we don't
        # care for it.
        # pylint:disable=bad-super-call
        return super(ArrayField, self).formfield(**defaults)


class ColorInput(forms.TextInput):
    input_type = "color"


class ColorField(forms.CharField):
    widget = ColorInput


class ColumnSelect(forms.Select):
    template_name = "django/forms/widgets/select_column.html"

    def __init__(self, attrs=None, choices=()) -> None:
        super().__init__(attrs=attrs, choices=choices)
        self.disabled = []

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        for _, optgroup, __ in context["widget"]["optgroups"]:
            for option in optgroup:
                if (value := option["value"]) in self.disabled:
                    option["attrs"]["disabled"] = True
                    option["attrs"]["title"] = self.disabled[value]
        return context


class ColumnField(forms.ChoiceField):
    widget = ColumnSelect

    def __init__(self, *args, **kwargs):
        self.disable_struct_array = kwargs.pop("disable_struct_array", False)
        self.allowed_types = kwargs.pop("allowed_types", None)
        self.disabled_types = kwargs.pop("disabled_types", None)
        self.message = kwargs.pop("message", None)

        super().__init__(*args, **kwargs)

    def _set_column_choices(self, schema):
        self.choices = create_column_choices(schema)

        if self.disable_struct_array:
            self.disabled = {
                name: "Currently, you cannot use this column type here."
                for name, type_ in schema.items()
                if isinstance(type_, (Struct, Array))
            }

        if self.allowed_types:
            self.disabled = {
                name: self.message
                for name, type_ in schema.items()
                if type_ not in self.allowed_types
            }

        if self.disabled_types:
            self.disabled = {
                name: self.message
                for name, type_ in schema.items()
                if type_ in self.disabled_types
            }
