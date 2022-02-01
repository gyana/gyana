import textwrap

from django.db import models

from apps.base.models import BaseModel
from apps.integrations.models import Integration

RETRY_LIMIT_DAYS = 3


class Sheet(BaseModel):

    integration = models.OneToOneField(Integration, on_delete=models.CASCADE)

    url = models.URLField()
    # Max length of sheet name seems to be 50
    sheet_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Sheet selection",
        help_text="Select a specific sheet by submitting the tab name",
    )
    cell_range = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Select a range of cells e.g. A2:D14",
    )
    # essentially the version of the file that was synced
    drive_file_last_modified_at_sync = models.DateTimeField(null=True)
    # automatically sync metadata from google drive
    drive_modified_date = models.DateTimeField(null=True)

    @property
    def table_id(self):
        return f"sheet_{self.id:09}"

    def create_integration(self, title, created_by, project, is_scheduled):
        # maximum Google Drive name length is 32767
        name = textwrap.shorten(title, width=255, placeholder="...")
        integration = Integration.objects.create(
            project=project,
            kind=Integration.Kind.SHEET,
            name=name,
            created_by=created_by,
            is_scheduled=is_scheduled,
        )
        self.integration = integration

    def sync_updates_from_drive(self):
        from apps.sheets.sheets import get_last_modified_from_drive_file

        self.drive_modified_date = get_last_modified_from_drive_file(self)
        # avoid a race condition with the sync task
        self.save(update_fields=["drive_modified_date"])

    @property
    def up_to_date_with_drive(self):
        return self.drive_modified_date == self.drive_file_last_modified_at_sync
