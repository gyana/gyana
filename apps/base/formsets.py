from django import forms
from django.forms.models import BaseInlineFormSet


class RequiredInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.names = kwargs.pop("names", None)
        super().__init__(*args, **kwargs)
        self.can_add = self.total_form_count() < self.max_num
        self.hide_delete_button = self.min_num == self.max_num

        for form in self.forms:
            form.empty_permitted = False
            form.use_required_attribute = True


class InlineColumnFormset(RequiredInlineFormset):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.form.base_fields["column"] = forms.ChoiceField(
            choices=[
                ("", "No column selected"),
                *[(col, col) for col in self.instance.parents.first().schema],
            ],
            help_text=self.form.base_fields["column"].help_text,
        )
