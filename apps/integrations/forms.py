import googleapiclient
from apps.integrations.bigquery import get_sheets_id_from_url
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import FileInput, HiddenInput
from lib.clients import sheets_client
from pathvalidate import ValidationError as PathValidationError
from pathvalidate import validate_filename

from .models import Integration


class GoogleSheetsForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["url", "name", "cell_range", "kind", "project", "enable_sync_emails"]
        widgets = {"kind": HiddenInput(), "project": HiddenInput()}
        help_texts = {}

    def clean_url(self):
        url = self.cleaned_data["url"]
        sheet_id = get_sheets_id_from_url(url)

        if sheet_id == "":
            raise ValidationError("The URL to the sheet seems to be invalid.")

        client = sheets_client()
        try:
            client.spreadsheets().get(spreadsheetId=sheet_id).execute()
        except googleapiclient.errors.HttpError as e:
            raise ValidationError(
                "We couldn't access the sheet using the URL provided! Did you give access to the right email?"
            )

        return url

    def clean_cell_range(self):
        cell_range = self.cleaned_data["cell_range"]

        # If validation on the url field fails url, cleaned_data won't
        # have the url populated.
        if not (url := self.cleaned_data.get("url")):
            return cell_range

        sheet_id = get_sheets_id_from_url(url)

        client = sheets_client()
        try:
            client.spreadsheets().get(
                spreadsheetId=sheet_id, ranges=cell_range
            ).execute()
        except googleapiclient.errors.HttpError as e:
            # This will display the parse error
            raise ValidationError(e._get_reason().strip())

        return cell_range


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


class FivetranForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ["name", "service", "kind", "project", "enable_sync_emails"]
        widgets = {
            "kind": HiddenInput(),
            "service": HiddenInput(),
            "project": HiddenInput(),
        }


FORM_CLASS_MAP = {
    Integration.Kind.FIVETRAN: FivetranForm,
    Integration.Kind.CSV: CSVForm,
    Integration.Kind.GOOGLE_SHEETS: GoogleSheetsForm,
}
