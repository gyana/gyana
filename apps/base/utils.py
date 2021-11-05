import random
import string


def short_hash():
    return "".join(
        random.choice(string.ascii_letters + string.digits) for n in range(6)
    )
