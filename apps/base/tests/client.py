from bs4 import BeautifulSoup
from django.test.client import Client


def get_turbo_frame(client, page_url, frame_url):
    response = client.get(page_url)
    assert response.status_code == 200

    soup = BeautifulSoup(response.content)

    frames = soup.select(f'turbo-frame[src="{frame_url}"]')
    assert len(frames) == 1

    frame = frames[0]

    tf_response = client.get(frame["src"])
    assert tf_response.status_code == 200

    tf_soup = BeautifulSoup(tf_response.content)
    assert tf_soup.select("turbo-frame")[0]["id"] == frame["id"]

    return tf_response


Client.get_turbo_frame = get_turbo_frame
