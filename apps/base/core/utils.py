import hashlib
import json
import re
from contextlib import contextmanager
from time import perf_counter

pattern = re.compile(r"(?<!^)(?=[A-Z])")


@contextmanager
def catchtime() -> float:
    # https://stackoverflow.com/questions/33987060/python-context-manager-that-measures-time
    start = perf_counter()
    yield lambda: perf_counter() - start


def error_name_to_snake(error):
    """Converts a exception class name to snake case"""
    return pattern.sub("_", error.__class__.__name__).lower()


def md5(content):
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def md5_kwargs(**kwargs):
    return md5(json.dumps(kwargs))


def create_column_choices(schema):
    columns = sorted([(col, col) for col in schema], key=lambda x: str.casefold(x[1]))
    return [("", "No column selected"), *columns]
