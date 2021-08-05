import hashlib
import json


def get_cache_key(**kwargs):
    return hashlib.md5(json.dumps(kwargs).encode("utf-8")).hexdigest()
