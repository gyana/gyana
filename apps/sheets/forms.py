import googleapiclient
from apps.base.clients import sheets_client
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import HiddenInput

from .bigquery import get_sheets_id_from_url
from .models import Sheet


class SheetForm(forms.ModelForm):
    class Meta:
        model = Sheet
        fields = [
            "url",
            "cell_range",
            "project",
        ]
        widgets = {"project": HiddenInput()}
        help_texts = {}
        labels = {"url": "Google Sheets URL"}

    def clean_url(self):
        url = self.cleaned_data["url"]
        sheet_id = get_sheets_id_from_url(url)

        if sheet_id == "":
            raise ValidationError("The URL to the sheet seems to be invalid.")

        client = sheets_client()
        try:
            self._sheet = client.spreadsheets().get(spreadsheetId=sheet_id).execute()
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
