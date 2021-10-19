import googleapiclient
from apps.base.forms import BaseModelForm
from django import forms
from django.core.exceptions import ValidationError

from .models import Sheet
from .sheets import get_sheets_id_from_url


class SheetCreateForm(BaseModelForm):
    class Meta:
        model = Sheet
        fields = ["url"]
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

        from apps.base.clients import sheets_client

        client = sheets_client()
        try:
            self._sheet = client.spreadsheets().get(spreadsheetId=sheet_id).execute()
        except googleapiclient.errors.HttpError as e:
            raise ValidationError(
                "We couldn't access the sheet using the URL provided! Did you give access to the right email?"
            )

        return url

    def pre_save(self, instance):
        instance.create_integration(
            self._sheet["properties"]["title"], self._created_by, self._project
        )


class SheetUpdateForm(forms.ModelForm):
    class Meta:
        model = Sheet
        fields = ["cell_range"]

    def clean_cell_range(self):
        cell_range = self.cleaned_data["cell_range"]

        sheet_id = get_sheets_id_from_url(self.instance.url)

        from apps.base.clients import sheets_client

        client = sheets_client()
        try:
            client.spreadsheets().get(
                spreadsheetId=sheet_id, ranges=cell_range
            ).execute()
        except googleapiclient.errors.HttpError as e:
            raise ValidationError(e.reason.strip())

        return cell_range
