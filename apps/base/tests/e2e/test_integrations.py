import pytest

pytestmark = pytest.mark.django_db(transaction=True)

BIGQUERY_TIMEOUT = 30000  # Adjust according to your utils
SHARED_SHEET = "https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit"


@pytest.fixture
def sheets(mocker):
    pass


@pytest.fixture
def drive_v2(mocker):
    pass


def test_create_sheet_integration_with_retry(
    page, live_server, project, drive_v2, sheets
):
    page.force_login(live_server)
    page.goto(live_server.url + "/projects/1")

    page.get_by_text("Create an integration to get started").click()

    page.wait_for_url(live_server.url + "/projects/1/integrations/")
    page.get_by_text("Add a Google Sheet").click()

    # start with runtime error
    page.wait_for_url(live_server.url + "/projects/1/integrations/sheets/new")
    page.fill('input[name="url"]', SHARED_SHEET)
    page.get_by_text("Advanced").click()

    page.fill('input[name="sheet_name"]', "store_info")
    page.fill('input[name="cell_range"]', "A20:D21")
    page.click('button[type="submit"]')

    page.locator('text="No columns found in the schema."').wait_for(
        timeout=BIGQUERY_TIMEOUT
    )

    # # try to retry it
    # page.click('text="Retry"')

    # # edit the configuration
    # with page.locator('#main').element_handle() as main:
    #     main.click('text="Configure"')
    # page.fill('input[name="cell_range"]', 'A1:D11')
    # page.locator('button[type="submit"]:has-text("Import")').click()

    # page.locator('text="Confirm"').click(timeout=BIGQUERY_TIMEOUT)
    # # only 10/15 rows imported
    # page.locator('text="10 rows"').wait_for()

    # # todo: next step in the flow
