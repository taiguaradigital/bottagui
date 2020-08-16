from collections import defaultdict


def nested_dict(n, type_dict):
    if n == 1:
        return defaultdict(type_dict)
    else:
        return defaultdict(lambda: nested_dict(n - 1, type_dict))


