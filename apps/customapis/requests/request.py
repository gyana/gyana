import time
from io import BytesIO

import requests
from requests.exceptions import Timeout

ITER_BYTE_SIZE = 2048  # 2 KB
REQUEST_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
REQUEST_TIMEOUT = 30  # seconds

# https://stackoverflow.com/q/23514256/15425660
# https://stackoverflow.com/a/22347526/15425660


def request_safe(session: requests.Session, **kwargs) -> requests.Response:
    # session.request with a maximum timeout and size

    try:
        r = session.request(**kwargs, stream=True, timeout=REQUEST_TIMEOUT)
    except Timeout:
        raise Exception(
            "Exceeded maximum timeout of 30 seconds, reach out for support."
        )

    size = 0
    start = time.time()
    ctt = BytesIO()

    for chunk in r.iter_content(ITER_BYTE_SIZE):

        if time.time() - start > REQUEST_TIMEOUT:
            raise Exception(
                "Exceeded maximum timeout of 30 seconds, reach out for support."
            )

        size += len(chunk)
        ctt.write(chunk)

        if size > REQUEST_MAX_SIZE:
            r.close()
            raise Exception(
                "Exceeded maximum response size of 10 MB, reach out for support."
            )

    r._content = ctt.getvalue()

    return r
