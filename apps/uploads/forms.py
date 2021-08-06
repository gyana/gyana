from apps.integrations.models import Integration
from django import forms
from django.forms.widgets import HiddenInput
from pathvalidate import ValidationError as PathValidationError
from pathvalidate import validate_filename


class CSVForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name", "kind", "project", "enable_sync_emails"]
        widgets = {
            "kind": HiddenInput(),
            "project": HiddenInput(),
        }


class CSVCreateForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name", "kind", "project", "file", "enable_sync_emails"]
        widgets = {
            "kind": HiddenInput(),
            "project": HiddenInput(),
            "name": HiddenInput(),
        }

    file = forms.CharField(
        widget=forms.FileInput(
            attrs={
                "accept": ".csv",
                "onchange": "(function(input){document.getElementById('id_name').value=input.files[0].name})(this)",
            }
        ),
        required=False,
    )

    def clean_name(self):
        name = self.cleaned_data["name"]
        try:
            validate_filename(name)
        except PathValidationError:
            self.add_error("file", "Invalid file name")

        return name.split(".").pop(0)
