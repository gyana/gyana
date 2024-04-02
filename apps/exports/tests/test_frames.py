from django.core.files.uploadedfile import SimpleUploadedFile
import pytest
from pytest_django.asserts import assertContains, assertRedirects

from apps.base.tests.asserts import assertOK
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db


@pytest.fixture
def run_export_task(mocker):
    return mocker.patch(
        "apps.exports.frames.run_export_task",
    )


def test_export_create_node(
    client, node_factory, run_export_task, logged_in_user, project
):
    node = node_factory(kind=Node.Kind.INPUT, workflow__project=project)
    EXPORT_URL = f"/exports/new/node/{node.id}"

    r = client.get(EXPORT_URL)
    assertOK(r)
    assertContains(r, "fa-download")

    r = client.post(EXPORT_URL)
    assertRedirects(r, EXPORT_URL, status_code=303)
    assert run_export_task.delay.call_count == 1
    assert run_export_task.delay.call_args.args[1] == logged_in_user.id


def test_export_create_integration_table(
    client, integration_table_factory, run_export_task, logged_in_user, project
):
    table = integration_table_factory(integration__project=project)
    EXPORT_URL = f"/exports/new/integration_table/{table.id}"

    r = client.get(EXPORT_URL)
    assertOK(r)
    assertContains(r, "fa-download")

    r = client.post(EXPORT_URL)
    assertRedirects(r, EXPORT_URL, status_code=303)
    assert run_export_task.delay.call_count == 1
    assert run_export_task.delay.call_args.args[1] == logged_in_user.id


def test_export_download(client, export_factory):
    export = export_factory(file=SimpleUploadedFile("file.csv", b"content"))
    r = client.get(f"/exports/{export.id}/download")

    assertOK(r)
    assert r["Content-Type"] == "application/octet-stream"
    assert f'attachment; filename="{export.file.name}"' in r["Content-Disposition"]
