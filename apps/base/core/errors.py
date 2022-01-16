import re

pattern = re.compile(r"(?<!^)(?=[A-Z])")


def error_name_to_snake(error):
    """Converts a exception class name to snake case"""
    return pattern.sub("_", error.__class__.__name__).lower()
