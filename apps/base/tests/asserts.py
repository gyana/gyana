import pytest
from bs4 import BeautifulSoup

pytestmark = pytest.mark.django_db


def assertLink(response, url, text):
    soup = BeautifulSoup(response.content)
    matches = soup.select(f'a[href="{url}"]')

    assert len(matches) == 1
    assert text in matches[0].text


def assertSelectorLength(response, selector, length):
    soup = BeautifulSoup(response.content)
    assert len(soup.select(selector)) == length


def assertOK(response):
    assert response.status_code == 200


def assertFormRenders(response, expected_fields=[]):
    soup = BeautifulSoup(response.content)

    matches = soup.select("form input,select,textarea")
    IGNORE_LIST = ["csrfmiddlewaretoken", "hidden_live"]
    fields = [m["name"] for m in matches if m["name"] not in IGNORE_LIST]
    assert set(fields) == set(expected_fields)

    assert len(soup.select("form button[type=submit]")) >= 1
