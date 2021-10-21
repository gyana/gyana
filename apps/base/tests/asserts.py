import pytest
from bs4 import BeautifulSoup

pytestmark = pytest.mark.django_db


def assertLink(response, url, text=None, title=None, target_top=False):
    soup = BeautifulSoup(response.content)
    matches = soup.select(f'a[href="{url}"]')
    if text is not None:
        matches = [m for m in matches if text in m.text]
    elif title is not None:
        matches = [m for m in matches if title in m["title"]]
    else:
        assert False
    assert len(matches) == 1

    # for turbo frames
    if target_top:
        match = matches[0]
        assert match.target == "_top"


def assertSelectorLength(response, selector, length):
    soup = BeautifulSoup(response.content)
    actual_length = len(soup.select(selector))
    assert actual_length == length, f"{actual_length} != {length}"


def assertSelectorText(response, selector, text):
    soup = BeautifulSoup(response.content)
    assert text in soup.select(selector)[0].text


def assertOK(response):
    assert response.status_code == 200, f"{response.status_code} != 200"


def assertNotFound(response):
    assert response.status_code == 404, f"{response.status_code} != 404"


def assertFormRenders(response, expected_fields=[]):
    soup = BeautifulSoup(response.content)

    matches = soup.select("form input,select,textarea")
    IGNORE_LIST = ["csrfmiddlewaretoken", "hidden_live"]
    fields = [m["name"] for m in matches if m["name"] not in IGNORE_LIST]
    assert set(fields) == set(
        expected_fields
    ), f"{set(fields)} != {set(expected_fields)}"

    assert len(soup.select("form button[type=submit]")) >= 1
