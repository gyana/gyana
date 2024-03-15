import hashlib


def md5(content):
    return hashlib.md5(content.encode("utf-8")).hexdigest()


TABLE_NAME = "`project.dataset`.table"
