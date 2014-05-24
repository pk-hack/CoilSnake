class EqualityMixin(object):
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)


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
        if type(values) == list:
            values = {str(k).upper(): v for k, v in zip(values, range(len(values)))}
        elif type(values) == dict:
            values = {str(v).upper(): k for k, v in values.iteritems()}
        else:
            from coilsnake.exceptions.common.exceptions import InvalidArgumentError
            raise InvalidArgumentError("Could not create GenericEnum with values of type {}".format(values))
        return type("{}_GenericEnum".format(name),
                    (GenericEnum,),
                    values)

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
        from coilsnake.exceptions.common.exceptions import InvalidArgumentError

        raise InvalidArgumentError("Could not convert value[{}] to string because the value was undefined".format(val))

    @classmethod
    def fromstring(cls, s):
        value = getattr(cls, s.upper(), None)
        if value is None:
            from coilsnake.exceptions.common.exceptions import InvalidArgumentError

            raise InvalidArgumentError(("Could not convert string[{}] to class[{}] because the value was "
                                       "undefined").format(s, cls.__name__))
        return value

    @classmethod
    def values(cls):
        return [x for x in vars(cls).iterkeys() if not x.startswith("_")]