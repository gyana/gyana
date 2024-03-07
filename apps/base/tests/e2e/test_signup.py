import re

import pytest
from django.core import mail

pytestmark = pytest.mark.django_db(transaction=True)


def test_signup(page, live_server):
    # signup from website
    page.goto(live_server.url + "/signup")
    page.fill('input[name="email"]', "new@gyana.com")
    page.fill('input[name="password1"]', "seewhatmatters")
    page.click('button[type="submit"]')

    page.wait_for_url(live_server.url + "/confirm-email/")
    assert len(mail.outbox) == 1
    url = re.search(r"\bhttps?://\S+\b", mail.outbox[0].body).group(0)
    page.goto(url)

    # onboarding
    page.fill('input[name="first_name"]', "Waitlist")
    page.fill('input[name="last_name"]', "User")
    page.click('input[name="marketing_allowed"][value="True"]')
    page.click('text="Next"')

    page.select_option('select[name="company_industry"]', "Agency")
    page.select_option('select[name="company_role"]', "Marketing")
    page.select_option('select[name="company_size"]', "2-10")
    page.select_option('select[name="source_channel"]', "onlineads")
    page.click('button[type="submit"]')

    # new team
    assert f"/teams" in page.url
    page.fill('input[name="name"]', "My team")
    page.click('button[type="submit"]')

    # new project
    assert f"/teams/1" in page.url
    page.click('text="Create a new project"')

    page.wait_for_url(live_server.url + "/teams/1/projects/new")
    page.fill('input[name="name"]', "Metrics")
    description = page.locator('textarea[name="description"]')
    assert description.is_enabled()
    description.fill("All the company metrics")
    page.click('button[type="submit"]')

    page.wait_for_url(live_server.url + "/projects/1")
    page.locator(".project").locator('text="Metrics"').wait_for()
    page.locator('text="All the company metrics"').wait_for()
