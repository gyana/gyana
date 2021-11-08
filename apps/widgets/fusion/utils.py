import random
import string

from apps.widgets.models import Widget


def short_hash():
    return "".join(
        random.choice(string.ascii_letters + string.digits) for n in range(6)
    )


DEFAULT_WIDTH = "100%"
DEFAULT_HEIGHT = "100%"

TO_FUSION_CHART = {Widget.Kind.STACKED_LINE: "msline"}
