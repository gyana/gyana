from django import forms
from django.forms.models import BaseInlineFormSet


class RequiredInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False
            form.use_required_attribute = True


class InlineColumnFormset(RequiredInlineFormset):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.form.base_fields["column"] = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in kwargs["form_kwargs"]["schema"]],
            ],
            help_text=self.form.base_fields["column"].help_text,
        )
