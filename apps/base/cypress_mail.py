"""
Backend for test environment with persistent storage, inspired by locmem.
"""

import json
import os
from datetime import datetime
from glob import glob

from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend

MESSAGES_DIR = os.path.abspath(".mock/.messages")


def _msg_to_dict(msg):
    return {
        "payload": msg.message().get_payload(),
        **{k: v for k, v in msg.message().items()},
    }


def _get_epoch_micro():
    return int(datetime.now().timestamp() * 1_000_000)


class Outbox:
    @property
    def messages(self):
        return [json.load(open(path, "r")) for path in glob(f"{MESSAGES_DIR}/*")]

    def clear(self):
        for f in glob(f"{MESSAGES_DIR}/*"):
            os.remove(f)


class EmailBackend(BaseEmailBackend):
    """
    An email backend for use during test sessions.

    The test connection stores email messages in JSON on disk,
    rather than sending them out on the wire.

    The dummy outbox is accessible through the outbox instance attribute.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(mail, "outbox"):
            mail.outbox = Outbox()

    def send_messages(self, messages):
        """Redirect messages to the dummy outbox"""
        msg_count = 0
        for msg in messages:  # .message() triggers header validation
            msg_dict = _msg_to_dict(msg)
            # guaranteed to be written and read in same order
            with open(f"{MESSAGES_DIR}/message-{_get_epoch_micro()}.json", "w") as fp:
                json.dump(msg_dict, fp)
            msg_count += 1
        return msg_count
