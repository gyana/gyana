import textwrap

import googleapiclient
from apps.base.clients import sheets_client
from apps.integrations.models import Integration
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .bigquery import get_sheets_id_from_url
from .models import Sheet


class SheetCreateForm(forms.ModelForm):
    class Meta:
        model = Sheet
        fields = [
            "url",
            "cell_range",
        ]
        help_texts = {}
        labels = {"url": "Google Sheets URL"}

    def __init__(self, *args, **kwargs):
        self._project = kwargs.pop("project")
        self._created_by = kwargs.pop("created_by")

        super().__init__(*args, **kwargs)

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
        instance = super().save(commit=False)

        title = self._sheet["properties"]["title"]
        # maximum Google Drive name length is 32767
        name = textwrap.shorten(title, width=255, placeholder="...")
        integration = Integration(
            project=self._project,
            kind=Integration.Kind.SHEET,
            name=name,
            created_by=self._created_by,
        )
        instance.integration = integration

        if commit:
            with transaction.atomic():
                integration.save()
                instance.save()
                self.save_m2m()

        return instance


class SheetUpdateForm(forms.ModelForm):
    class Meta:
        model = Sheet
        fields = [
            "cell_range",
        ]

    def clean_cell_range(self):
        cell_range = self.cleaned_data["cell_range"]

        # If validation on the url field fails url, cleaned_data won't
        # have the url populated.
        if not (url := self.instance.url):
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
