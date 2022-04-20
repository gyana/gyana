import googleapiclient
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.base import clients
from apps.base.account import is_scheduled_paid_only
from apps.base.forms import BaseModelForm, LiveFormsetMixin

from .models import Sheet
from .sheets import get_cell_range, get_sheets_id_from_url


class FormExtraMixin:
    def __init__(self, *args, **kwargs):
        if not hasattr(self, "extra_fields"):
            raise ValueError("FormExtraMixin has no extra_fields specified.")

        super().__init__(*args, **kwargs)


class SheetCreateForm(FormExtraMixin, BaseModelForm):
    extra_fields = ["sheet_name", "cell_range"]

    is_scheduled = forms.BooleanField(
        required=False, label="Automatically sync new data"
    )

    class Meta:
        model = Sheet
        fields = ["url", "sheet_name", "cell_range"]
        help_texts = {"url": "You can revoke our access at any time"}
        labels = {"url": "Enter your Google Sheet URL"}

    def __init__(self, *args, **kwargs):
        url = kwargs.pop("url")
        self._project = kwargs.pop("project")
        self._created_by = kwargs.pop("created_by")

        super().__init__(*args, **kwargs)

        self.fields["url"].initial = url
        is_scheduled_paid_only(self.fields["is_scheduled"], self._project)

    def clean_url(self):
        url = self.cleaned_data["url"]
        sheet_id = get_sheets_id_from_url(url)

        if sheet_id == "":
            raise ValidationError("The URL to the sheet seems to be invalid.")

        client = clients.sheets()
        try:
            self._sheet = client.spreadsheets().get(spreadsheetId=sheet_id).execute()
        except googleapiclient.errors.HttpError as e:
            raise ValidationError(
                "We couldn't access the sheet using the URL provided! Did you give access to the right email?"
            )

        return url

    def clean_cell_range(self):
        if not self.cleaned_data.get("url"):
            raise ValidationError("Sheet URL is required")

        url = self.cleaned_data["url"]
        sheet_name = self.cleaned_data["sheet_name"]
        cell_range = self.cleaned_data["cell_range"]
        sheet_id = get_sheets_id_from_url(url)

        client = clients.sheets()
        try:
            client.spreadsheets().get(
                spreadsheetId=sheet_id, ranges=get_cell_range(sheet_name, cell_range)
            ).execute()
        except googleapiclient.errors.HttpError as e:
            raise ValidationError(e.reason.strip())

        return cell_range

    def pre_save(self, instance):
        instance.create_integration(
            self._sheet["properties"]["title"],
            self._created_by,
            self._project,
            self.cleaned_data["is_scheduled"],
        )

    def post_save(self, instance):
        instance.integration.project.update_schedule()


class SheetUpdateForm(LiveFormsetMixin, BaseModelForm):
    is_scheduled = forms.BooleanField(
        required=False, label="Automatically sync new data"
    )

    class Meta:
        model = Sheet
        fields = ["sheet_name", "cell_range", "is_scheduled"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_scheduled"].initial = self.instance.integration.is_scheduled
        is_scheduled_paid_only(
            self.fields["is_scheduled"], self.instance.integration.project
        )

    def clean_cell_range(self):
        sheet_name = self.cleaned_data["sheet_name"]
        cell_range = self.cleaned_data["cell_range"]
        sheet_id = get_sheets_id_from_url(self.instance.url)

        client = clients.sheets()
        try:
            client.spreadsheets().get(
                spreadsheetId=sheet_id, ranges=get_cell_range(sheet_name, cell_range)
            ).execute()
        except googleapiclient.errors.HttpError as e:
            raise ValidationError(e.reason.strip())

        return cell_range

    def pre_save(self, instance):
        with transaction.atomic():
            self.instance.integration.is_scheduled = self.cleaned_data["is_scheduled"]
            self.instance.integration.save()
            self.instance.integration.project.update_schedule()
