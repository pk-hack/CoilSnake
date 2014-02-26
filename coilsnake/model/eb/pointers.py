from coilsnake.exceptions.common.exceptions import InvalidArgumentError, MissingUserDataError, InvalidUserDataError
from coilsnake.exceptions.eb.exceptions import InvalidEbTextPointerError
from coilsnake.util.common.type import EqualityMixin, StringRepresentationMixin


class EbPointer(EqualityMixin, StringRepresentationMixin):
    label_address_map = dict()

    def __init__(self, address=None, size=3):
        if size is None or size <= 0:
            raise InvalidArgumentError("Cannot create pointer with non-positive size[%d]" % size)
        self.size = 3
        if address is not None:
            self.address = address

    def from_block(self, block, offset):
        self.address = block.read_multi(offset, self.size)

    def to_block(self, block, offset):
        block.write_multi(offset, self.address, self.size)

    def from_yml_rep(self, yml_rep):
        self.address = None

        if yml_rep is None:
            raise MissingUserDataError("Pointer was not specified")
        elif isinstance(yml_rep, str):
            try:
                if yml_rep[0] == '$':
                    self.address = int(yml_rep[1:], 16)
            except (IndexError, ValueError):
                raise InvalidUserDataError("Pointer \"%s\" was invalid" % yml_rep)

            if self.address is None:
                try:
                    self.address = EbPointer.label_address_map[yml_rep]
                except KeyError:
                    raise InvalidUserDataError("Unknown label \"%s\" provided for pointer" % yml_rep)
        else:
            raise InvalidUserDataError("Pointer \"%s\" was invalid" % yml_rep)

    def yml_rep(self):
        return "$%x" % self.address


class EbTextPointer(EbPointer):
    def from_block(self, block, offset):
        super(EbTextPointer, self).from_block(block, offset)

        if (self.address != 0) and (self.address < 0xc00000 or self.address > 0xffffff):
            raise InvalidEbTextPointerError("Pointer had invalid address %#x" % self.address)

    def from_yml_rep(self, yml_rep):
        super(EbTextPointer, self).from_yml_rep(yml_rep)

        if (self.address != 0) and (self.address < 0xc00000 or self.address > 0xffffff):
            raise InvalidEbTextPointerError("Pointer had invalid address %#x" % self.address)