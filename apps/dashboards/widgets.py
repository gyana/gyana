from django import forms
from django.forms.widgets import Textarea

from apps.base.fields import ColorField, ColorInput


class TextareaCode(Textarea):
    template_name = "django/forms/widgets/code.html"


class PaletteColorsWidget(forms.MultiWidget):
    template_name = "django/forms/widgets/palette_colors.html"
    widgets = [
        ColorInput(),
        ColorInput(),
        ColorInput(),
        ColorInput(),
        ColorInput(),
        ColorInput(),
        ColorInput(),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(widgets=self.widgets, *args, **kwargs)

    def decompress(self, value):
        if value:
            return value.split(" ")

        return [None]


class PaletteColorsField(forms.MultiValueField):
    widget = PaletteColorsWidget

    def __init__(self, **kwargs):
        fields = (
            ColorField(),
            ColorField(),
            ColorField(),
            ColorField(),
            ColorField(),
            ColorField(),
            ColorField(),
        )

        super().__init__(fields=fields, require_all_fields=False, **kwargs)

    def compress(self, data_list):
        return data_list

    def has_changed(self, initial, data):
        return super().has_changed(initial, map(lambda x: x.upper(), data))
