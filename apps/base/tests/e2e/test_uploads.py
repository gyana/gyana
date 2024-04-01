import pytest
from playwright.sync_api import expect

from .conftest import BIGQUERY_TIMEOUT

pytestmark = pytest.mark.django_db(transaction=True)

fixtures = "apps/base/tests/e2e/fixtures"


def test_upload_valid_csv(page, live_server, project, celery_worker):
    page.force_login(live_server)
    page.goto(live_server.url + "/projects/1/integrations")

    page.get_by_text("Upload CSV").click()

    page.wait_for_url(live_server.url + "/projects/1/integrations/uploads/new")
    page.locator("input[type=file]").set_input_files(f"{fixtures}/store_info.csv")

    page.wait_for_url(live_server.url + "/projects/1/integrations/1/load")
    page.get_by_text("Validating and importing your upload...").wait_for()
    page.get_by_text("Upload successfully imported").wait_for(timeout=BIGQUERY_TIMEOUT)

    # review the table and approve
    page.get_by_text("Employees").wait_for()
    page.get_by_text("Confirm", exact=True).click()

    # bigquery file upload needs longer wait
    page.get_by_text("Preview", exact=True).wait_for(timeout=BIGQUERY_TIMEOUT)
    # validate row count
    page.get_by_text("15 rows").wait_for()

    page.wait_for_url(live_server.url + "/projects/1/integrations/1")
    # file name inferred
    page.locator('input[name="name"]').input_value == "store_info"

    # cannot edit upload setup
    expect(page.get_by_text("Sync")).not_to_be_attached()


def test_upload_streamed_with_chunks(
    page, live_server, project, celery_worker, upload_factory
):
    # prevent upload from overriding upload for previous test (used in workflows/dashboards)
    upload_factory(integration__project__team=project.team)

    page.force_login(live_server)
    page.goto(live_server.url + "/projects/1/integrations")

    # by construction file is 1.1 MB = 2 chunks
    page.evaluate("() => window.__cypressChunkSize__ = 512 * 1024;")

    page.get_by_text("Upload CSV").click()

    page.locator("input[type=file]").set_input_files(f"{fixtures}/fifa.csv")

    page.get_by_text("Confirm", exact=True).click(timeout=BIGQUERY_TIMEOUT)
    page.get_by_text("Preview", exact=True).wait_for()
    # 2250 lines of CSV including header
    page.get_by_text("2,249").wait_for()


def test_upload_failures(page, live_server, project):
    page.force_login(live_server)
    page.goto(live_server.url + "/projects/1/integrations/uploads/new")

    # invalid format - better way to test this?
    assert (
        page.locator("input[type=file]").get_attribute("accept")
        == ".csv,.tsv,text/csv,text/plain"
    )

    # file is too large
    page.goto(live_server.url + "/projects/1/integrations")
    page.evaluate("() => window.__cypressMaxSize__ = '1KB';")
    page.get_by_text("Upload CSV").click()

    page.locator("input[type=file]").set_input_files(f"{fixtures}/fifa.csv")
    page.get_by_text("File is too large fifa.csv Maximum file size is 1 KB").wait_for()

    # upload errors e.g. bad connectivity or Google is down
    page.goto(live_server.url + "/projects/1/integrations")
    page.evaluate("() => window.__cypressMaxBackoff__ = 1;")
    page.get_by_text("Upload CSV").click()

    page.route("**/*", lambda r: r.fulfill(status=500))

    page.locator("input[type=file]").set_input_files(f"{fixtures}/store_info.csv")
    page.get_by_text("Error during upload store_info.csv tap to retry").wait_for()
