import re

import pytest
from bs4 import BeautifulSoup
from bs4.element import CData, NavigableString, TemplateString

# bs4 ignores text within templates tags, but for our product they are designed
# to be displayed with javascript
BS4_TYPES = [NavigableString, TemplateString, CData]

pytestmark = pytest.mark.django_db


def assertLink(response, url, text=None, title=None, tooltip=None, htmx=False, total=1):
    __tracebackhide__ = True

    soup = BeautifulSoup(response.content)
    original_matches = soup.select("a")

    attr = "hx-get" if htmx else "href"

    matches = [m for m in original_matches if m.get(attr) == url]

    if text is not None:
        matches = [m for m in matches if text in m.get_text(types=BS4_TYPES)]
    elif title is not None:
        matches = [m for m in matches if title in m["title"]]
    elif tooltip is not None:
        matches = [m for m in matches if tooltip in m["x-tooltip"]]

    assert len(matches) == total, f"Possible matches are {[match for match in matches]}"


def assertNotLink(*args, **kwargs):
    return assertLink(*args, **kwargs, total=0)


def assertSelectorLength(response, selector, length):
    __tracebackhide__ = True

    soup = BeautifulSoup(response.content)
    actual_length = len(soup.select(selector))
    assert actual_length == length, f"{actual_length} != {length}"


def assertSelectorText(response, selector, text):
    __tracebackhide__ = True

    soup = BeautifulSoup(response.content)
    assert (
        text in soup.select(selector)[0].text
    ), f"{text} not in {soup.select(selector)[0].text}"


def assertOK(response):
    __tracebackhide__ = True

    assert response.status_code == 200, f"{response.status_code} != 200"


def assertNotFound(response):
    __tracebackhide__ = True

    assert response.status_code == 404, f"{response.status_code} != 404"


def assertFormRenders(response, expected_fields=[], formSelector=None):
    __tracebackhide__ = True

    soup = BeautifulSoup(response.content)

    if formSelector is not None:
        matches = soup.select(
            f"{formSelector} input,{formSelector} select,{formSelector} textarea"
        )
    else:
        matches = soup.select("form input,select,textarea")

    IGNORE_LIST = ["csrfmiddlewaretoken", "__prefix__"]
    fields = [
        m["name"]
        for m in matches
        if not re.compile(f".*({'|'.join(IGNORE_LIST)}).*").match(m["name"])
    ]
    assert set(fields) == set(
        expected_fields
    ), f"{set(fields)} != {set(expected_fields)}"

    assert len(soup.select("form button[type=submit]")) >= 1


def assertSelectorHasAttribute(response, selector, attribute):
    soup = BeautifulSoup(response.content)
    element = soup.select(selector)[0]
    assert element.has_attr(attribute)


def assertFormChoicesLength(form, field_name, length):
    assert len(list(form.fields[field_name].choices)) == length


def assertLoginRedirect(client, url):
    r = client.get(url)
    assert r.status_code == 302, f"{r.status_code} != 302"
    assert r.url == f"/login/?next={url}", f"{r.url} != /login/?next={url}"
