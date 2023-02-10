from bs4 import BeautifulSoup
from django.test.client import Client


def get_child_htmx_partial(client, page_response, frame_url):

    soup = BeautifulSoup(page_response.content)

    frames = soup.select(f'[hx-get="{frame_url}"]')
    assert (
        len(frames) == 1
    ), f"""unable to find turbo frame in DOM with src {frame_url}
possible matches are {[f['src'] for f in soup.select('[hx-get]')]}"""

    frame = frames[0]

    tf_response = client.get(frame["hx-get"])
    assert tf_response.status_code == 200

    return tf_response


def get_htmx_partial(client, page_url, *frame_urls):
    # Validate and return response for turbo frame in a page, possibly recursively

    response = client.get(page_url)
    assert response.status_code == 200

    assert len(frame_urls) > 0

    for frame_url in frame_urls:
        response = get_child_htmx_partial(client, response, frame_url)

    return response


Client.get_htmx_partial = get_htmx_partial
