# https://stackoverflow.com/questions/33987060/python-context-manager-that-measures-time

from contextlib import contextmanager
from time import perf_counter


@contextmanager
def catchtime() -> float:
    start = perf_counter()
    yield lambda: perf_counter() - start
