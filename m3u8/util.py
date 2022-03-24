import re


_camel_to_snake_pattern = re.compile(r'(?<!^)(?=[A-Z])')


def camel_to_snake(s: str) -> str:
    return _camel_to_snake_pattern.sub('_', s).lower()
