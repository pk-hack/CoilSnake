def getitem_with_default(d, key, default_value):
    try:
        return d[key]
    except KeyError:
        return default_value