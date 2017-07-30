class EqualityMixin(object):
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = None


class StringRepresentationMixin(object):
    def __repr__(self):
        return "<{}({})>".format(
            self.__class__.__name__,
            ', '.join(["{}={}".format(k, repr(self.__dict__[k])) for k in self.__dict__ if k[0] != '_'])
        )

    __str__ = __repr__


class GenericEnum(object):
    @staticmethod
    def create(name, values):
        return type("{}_GenericEnum".format(name),
                    (GenericEnum,),
                    dict(zip([str(x).upper() for x in values], range(len(values)))))

    @classmethod
    def is_valid(cls, val):
        for k, v in vars(cls).items():
            if v == val:
                return True
        return False

    @classmethod
    def tostring(cls, val):
        for k, v in vars(cls).items():
            if v == val:
                return k.lower()
        from coilsnake.exceptions.common.exceptions import InvalidArgumentError

        raise InvalidArgumentError("Could not convert value[%s] to string because the value was undefined"
                                   % val)

    @classmethod
    def fromstring(cls, s):
        value = getattr(cls, s.upper(), None)
        if value is None:
            from coilsnake.exceptions.common.exceptions import InvalidArgumentError

            raise InvalidArgumentError("Could not convert string[%s] to class[%s] because the value was "
                                       "undefined"
                                       % (s, cls.__name__))
        return value

    @classmethod
    def values(cls):
        return [x for x in vars(cls).keys() if not x.startswith("_")]


def enum_class_from_name_list(names):
    return type("CustomEnum",
                (GenericEnum,),
                dict(zip([str(x).upper() for x in names], range(len(names)))))