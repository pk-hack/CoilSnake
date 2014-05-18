from itertools import izip

from coilsnake.exceptions.common.exceptions import MissingUserDataError, InvalidUserDataError, InvalidArgumentError


def getitem_with_default(d, key, default_value):
    try:
        return d[key]
    except KeyError:
        return default_value


def in_inclusive_range(x, rang):
    return rang[0] <= x <= rang[1]


def not_in_inclusive_range(x, rang):
    return not in_inclusive_range(x, rang)


def get_from_user_dict(yml_rep, key, object_type):
    try:
        value = yml_rep[key]
    except KeyError:
        raise MissingUserDataError("Attribute \"%s\" was not provided" % key)

    if not isinstance(value, object_type):
        raise InvalidUserDataError("Attribute \"%s\" was not of type %s" % (key, object_type.__name__))

    return value


def get_enum_from_user_dict(yml_rep, key, enum_class):
    try:
        value = yml_rep[key]
    except KeyError:
        raise MissingUserDataError("Attribute \"%s\" was not provided" % key)

    if not isinstance(value, str):
        raise InvalidUserDataError("Attribute \"%s\" was not a string" % key)

    try:
        return enum_class.fromstring(value)
    except InvalidArgumentError:
        raise InvalidUserDataError("Attribute \"%s\" had unknown value \"%s\"" % (key, value))


def lower_if_str(x):
    if isinstance(x, str):
        return x.lower()
    else:
        return x


def grouped(iterable, n):
    return izip(*[iter(iterable)]*n)


def min_max(x, low, high):
    if x < low:
        return low
    else:
        return min(x, high)