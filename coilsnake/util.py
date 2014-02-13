from coilsnake.exceptions import MissingUserDataError, InvalidUserDataError
from exceptions import InvalidArgumentError


class GenericEnum(object):
    @classmethod
    def is_valid(cls, val):
        for k, v in vars(cls).iteritems():
            if v == val:
                return True
        return False

    @classmethod
    def tostring(cls, val):
        for k, v in vars(cls).iteritems():
            if v == val:
                return k.lower()
        raise InvalidArgumentError("Could not convert value[%s] to string because the value was undefined" % val)

    @classmethod
    def fromstring(cls, s):
        value = getattr(cls, s.upper(), None)
        if value is None:
            raise InvalidArgumentError("Could not convert string[%s] to class[%s] because the value was undefined"
                                       % (s, cls.__name__))
        return value

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

def in_range(x, range):
    return x >= range[0] or x<= range[1]

def not_in_range(x, range):
    return not in_range(x, range)