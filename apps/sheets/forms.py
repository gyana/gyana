import googleapiclient
from django.core.exceptions import ValidationError
from waffle import flag_is_active

from apps.base import clients
from apps.base.forms import BaseModelForm

from .models import Sheet
from .sheets import get_sheets_id_from_url


class SheetCreateForm(BaseModelForm):
    class Meta:
        model = Sheet
        fields = ["url", "is_scheduled"]
        help_texts = {}
        labels = {
            "url": "Google Sheets URL",
            "is_scheduled": "Automatically sync new data",
        }

    def __init__(self, *args, **kwargs):
        url = kwargs.pop("url")
        self._project = kwargs.pop("project")
        self._created_by = kwargs.pop("created_by")
        request = kwargs.pop("request")

        super().__init__(*args, **kwargs)

        self.fields["url"].initial = url
        self.fields[
            "is_scheduled"
        ].help_text = f"Daily at {self._project.daily_schedule_time} in {self._project.team.timezone}"

        if not flag_is_active(request, "beta"):
            self.fields.pop("is_scheduled")

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

    def pre_save(self, instance):
        instance.create_integration(
            self._sheet["properties"]["title"], self._created_by, self._project
        )
        instance.update_next_daily_sync()


class SheetUpdateForm(BaseModelForm):
    class Meta:
        model = Sheet
        fields = ["cell_range"]

    def clean_cell_range(self):
        cell_range = self.cleaned_data["cell_range"]

        sheet_id = get_sheets_id_from_url(self.instance.url)

        client = clients.sheets()
        try:
            client.spreadsheets().get(
                spreadsheetId=sheet_id, ranges=cell_range
            ).execute()
        except googleapiclient.errors.HttpError as e:
            raise ValidationError(e.reason.strip())

        return cell_range


class SheetSettingsForm(BaseModelForm):
    class Meta:
        model = Sheet
        fields = ["is_scheduled"]
        labels = {"is_scheduled": "Automatically sync new data"}

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        super().__init__(*args, **kwargs)
        project = self.instance.integration.project
        help_text = f"Daily at {project.daily_schedule_time} in {project.team.timezone}"
        self.fields["is_scheduled"].help_text = help_text
        if not flag_is_active(request, "beta"):
            self.fields.pop("is_scheduled")

    def pre_save(self, instance):
        instance.update_next_daily_sync()
