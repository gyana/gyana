import pytest

from apps.integrations.models import Integration
from apps.sheets.models import Sheet
from apps.tables.models import Table
from apps.uploads.models import Upload

pytestmark = pytest.mark.django_db(transaction=True)

COPY_QUERY = "CREATE OR REPLACE TABLE {} as (SELECT * FROM {})"


def test_integration_upload_clone(upload_factory, integration_table_factory, engine):
    upload = upload_factory()
    table = integration_table_factory(integration=upload.integration)
    clone = upload.integration.make_clone()

    assert Integration.objects.count() == 2
    assert Upload.objects.count() == 2
    assert Table.objects.count() == 2

    clone_table = clone.table_set.first()
    assert clone_table.name == clone.source_obj.table_id

    assert engine.raw_sql.call_args.args[0] == COPY_QUERY.format(
        clone_table.fqn, table.fqn
    )


def test_integration_sheet_clone(sheet_factory, integration_table_factory, engine):
    sheet = sheet_factory()
    table = integration_table_factory(integration=sheet.integration)
    clone = sheet.integration.make_clone()

    assert Integration.objects.count() == 2
    assert Sheet.objects.count() == 2
    assert Table.objects.count() == 2

    clone_table = clone.table_set.first()
    assert clone_table.name == clone.source_obj.table_id
    assert clone_table.namespace == table.namespace
    assert engine.raw_sql.call_args.args[0] == COPY_QUERY.format(
        clone_table.fqn, table.fqn
    )
