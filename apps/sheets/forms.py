import datetime

import googleapiclient
from apps.base.clients import sheets_client
from apps.integrations.bigquery import get_sheets_id_from_url
from apps.integrations.models import Integration
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import HiddenInput

from .models import Sheet


class GoogleSheetsForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = [
            "kind",
            "project",
        ]
        widgets = {"kind": HiddenInput(), "project": HiddenInput()}
        help_texts = {}

    url = forms.URLField(max_length=200)
    cell_range = forms.CharField(required=False, max_length=64, empty_value=None)

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

    def save(self, commit=True):

        self.instance.name = self._sheet["properties"]["title"]

        # saved automatically by parent
        Sheet(
            integration=self.instance,
            url=self.cleaned_data["url"],
            cell_range=self.cleaned_data["cell_range"],
        )

        return super().save(commit)
