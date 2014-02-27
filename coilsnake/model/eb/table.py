import logging
import yaml

from coilsnake.exceptions.common.exceptions import InvalidArgumentError, TableEntryInvalidYmlRepresentationError, \
    InvalidYmlRepresentationError
from coilsnake.model.common.table_new import GenericLittleEndianTable, LittleEndianIntegerTableEntry
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.pointers import EbPointer
from coilsnake.util.common.assets import open_asset
from coilsnake.util.eb.text import standard_text_from_block, standard_text_to_block


log = logging.getLogger(__name__)


class EbPointerTableEntry(LittleEndianIntegerTableEntry):
    @classmethod
    def from_yml_rep(cls, yml_rep):
        if not isinstance(yml_rep, str):
            raise TableEntryInvalidYmlRepresentationError("Could not parse value[{}] as pointer".format(yml_rep))
        elif not yml_rep:
            raise TableEntryInvalidYmlRepresentationError("Could not parse empty string as pointer")
        elif yml_rep[0] == "$":
            try:
                value = int(yml_rep[1:], 16)
            except ValueError:
                raise TableEntryInvalidYmlRepresentationError("Could not parse value[{}] as pointer".format(yml_rep))

            return super(EbPointerTableEntry, cls).from_yml_rep(value)
        else:
            try:
                value = EbPointer.label_address_map[yml_rep]
            except KeyError:
                raise TableEntryInvalidYmlRepresentationError("Unknown pointer label[{}]".format(yml_rep))

            return super(EbPointerTableEntry, cls).from_yml_rep(value)

    @classmethod
    def to_yml_rep(cls, value):
        return "${:x}".format(value)


class EbPaletteTableEntry(object):
    @classmethod
    def from_block(cls, block, offset):
        palette = EbPalette(num_subpalettes=1, subpalette_length=(cls.size / 2))
        palette.from_block(block, offset)
        print "returning {}".format(palette)
        return palette

    @classmethod
    def to_block(cls, block, offset, value):
        value.to_block(block=block, offset=offset)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        palette = EbPalette(num_subpalettes=1, subpalette_length=(cls.size / 2))
        try:
            palette.from_yml_rep(yml_rep)
        except InvalidYmlRepresentationError as e:
            raise TableEntryInvalidYmlRepresentationError(e.message)
        return palette

    @classmethod
    def to_yml_rep(cls, value):
        return value.yml_rep()


class EbStandardTextTableEntry(object):
    @classmethod
    def from_block(cls, block, offset):
        return standard_text_from_block(block, offset, cls.size)

    @classmethod
    def to_block(cls, block, offset, value):
        standard_text_to_block(block, offset, value, cls.size)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if isinstance(yml_rep, int):
            yml_rep = str(yml_rep)
        elif not isinstance(yml_rep, str):
            raise TableEntryInvalidYmlRepresentationError("Could not parse value[{}] of type[{}] as string".format(
                yml_rep, type(yml_rep).__name__))

        if len(yml_rep) > cls.size:
            raise TableEntryInvalidYmlRepresentationError("Text string[{}] exceeds size limit of {} characters".format(
                yml_rep, cls.size))

        return yml_rep

    @classmethod
    def to_yml_rep(cls, value):
        return value


class EbStandardNullTerminatedTextTableEntry(EbStandardTextTableEntry):
    @classmethod
    def to_block(cls, block, offset, value):
        standard_text_to_block(block, offset, value, cls.size - 1)
        block[offset + cls.size - 1] = 0

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if isinstance(yml_rep, int):
            yml_rep = str(yml_rep)
        elif not isinstance(yml_rep, str):
            raise TableEntryInvalidYmlRepresentationError("Could not parse value[{}] of type[{}] as string".format(
                yml_rep, type(yml_rep).__name__))

        if len(yml_rep) > cls.size - 1:
            raise TableEntryInvalidYmlRepresentationError("Text string[{}] exceeds size limit of {} characters".format(
                yml_rep, cls.size - 1))

        return yml_rep


class EbTable(GenericLittleEndianTable):
    TABLE_ENTRY_CLASS_MAP = dict(
        GenericLittleEndianTable.TABLE_ENTRY_CLASS_MAP,
        **{"pointer": (EbPointerTableEntry, ["name", "size"]),
           "palette": (EbPaletteTableEntry, ["name", "size"]),
           "standardtext": (EbStandardTextTableEntry, ["name", "size"]),
           "standardtext null-terminated": (EbStandardNullTerminatedTextTableEntry, ["name", "size"])})


_EB_SCHEMA_MAP = None

with open_asset("structures", "eb.yml") as f:
    i = 1
    for doc in yaml.load_all(f, Loader=yaml.CSafeLoader):
        if i == 1:
            i += 1
        elif i == 2:
            _EB_SCHEMA_MAP = doc
            break


def eb_table_from_offset(offset):
    log.debug("Creating EbTable object for offset[{:#x}]".format(offset))
    try:
        schema = _EB_SCHEMA_MAP[offset]
    except KeyError:
        raise InvalidArgumentError("Could not setup EbTable from unknown offset[{:#x}]".format(offset))

    return EbTable(name=schema["name"], size=schema["size"], schema_specification=schema["entries"])