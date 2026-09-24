def collect(item, values=[]):
    values.append(item)
    return values


def load(value):
    try:
        return int(value)
    except Exception:
        pass
