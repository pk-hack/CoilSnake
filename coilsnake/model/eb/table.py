from functools import partial

import yaml

from coilsnake.exceptions.common.exceptions import InvalidArgumentError, TableEntryInvalidYmlRepresentationError, \
    InvalidYmlRepresentationError
from coilsnake.model.common.table import LittleEndianIntegerTableEntry, Table, MatrixTable, \
    GenericLittleEndianRowTableEntry, TableEntry, LittleEndianHexIntegerTableEntry
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.pointers import EbPointer
from coilsnake.util.common.assets import open_asset
from coilsnake.util.eb.helper import is_in_bank
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address
from coilsnake.util.eb.text import standard_text_from_block, standard_text_to_block, standard_text_to_byte_list


class EbPointerTableEntry(LittleEndianIntegerTableEntry):
    @staticmethod
    def create(size):
        return type("EbPointerTableEntry_subclass",
                    (EbPointerTableEntry,),
                    {"size": size})

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

class EbHiLoMidPointerTableEntry(LittleEndianIntegerTableEntry):
    @staticmethod
    def create(size):
        return type("EbHiLoMidPointerTableEntry_subclass",
                    (EbHiLoMidPointerTableEntry,),
                    {"size": size})
                    
    @classmethod
    def from_block(cls, block, offset):
        bank = block[offset]
        addr = block.read_multi(offset + 1, 2)
        return addr | bank << 16

    @classmethod
    def to_block(cls, block, offset, value):
        block[offset] = (value & 0xff0000) >> 16
        block.write_multi(offset + 1, value & 0x00ffff, 2)

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

            return super(EbHiLoMidPointerTableEntry, cls).from_yml_rep(value)
        else:
            try:
                value = EbPointer.label_address_map[yml_rep]
            except KeyError:
                raise TableEntryInvalidYmlRepresentationError("Unknown pointer label[{}]".format(yml_rep))

            return super(EbHiLoMidPointerTableEntry, cls).from_yml_rep(value)

    @classmethod
    def to_yml_rep(cls, value):
        return "${:x}".format(value)


class EbPaletteTableEntry(TableEntry):
    @classmethod
    def from_block(cls, block, offset):
        palette = EbPalette(num_subpalettes=1, subpalette_length=(cls.size // 2))
        palette.from_block(block, offset)
        return palette

    @classmethod
    def to_block(cls, block, offset, value):
        value.to_block(block=block, offset=offset)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        palette = EbPalette(num_subpalettes=1, subpalette_length=(cls.size // 2))
        try:
            palette.from_yml_rep(yml_rep)
        except InvalidYmlRepresentationError as e:
            raise TableEntryInvalidYmlRepresentationError(str(e))
        return palette

    @classmethod
    def to_yml_rep(cls, value):
        return value.yml_rep()


class EbStandardTextTableEntry(TableEntry):
    @staticmethod
    def create(size):
        return type("EbStandardTextTableEntry_subclass",
                    (EbStandardTextTableEntry,),
                    {"size": size})

    @classmethod
    def to_block_size(cls, value):
        return len(standard_text_to_byte_list(value, cls.size, False))

    @classmethod
    def from_block(cls, block, offset):
        return standard_text_from_block(block, offset, cls.size)

    @classmethod
    def to_block(cls, block, offset, value):
        standard_text_to_block(block, offset, value, cls.size, False)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if isinstance(yml_rep, int):
            yml_rep = str(yml_rep)
        elif not isinstance(yml_rep, str):
            raise TableEntryInvalidYmlRepresentationError("Could not parse value[{}] of type[{}] as string".format(
                yml_rep, type(yml_rep).__name__))

        try:
            byte_rep = standard_text_to_byte_list(yml_rep, cls.size, False)
        except ValueError as e:
            raise TableEntryInvalidYmlRepresentationError(str(e))

        return yml_rep

    @classmethod
    def to_yml_rep(cls, value):
        return value


class EbStandardNullTerminatedTextTableEntry(EbStandardTextTableEntry):
    @staticmethod
    def create(size):
        return type("EbStandardNullTerminatedTextTableEntry_subclass",
                    (EbStandardNullTerminatedTextTableEntry,),
                    {"size": size})

    @classmethod
    def to_block_size(cls, value):
        return len(standard_text_to_byte_list(value, cls.size, True))

    @classmethod
    def to_block(cls, block, offset, value):
        standard_text_to_block(block, offset, value, cls.size, True)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if isinstance(yml_rep, int):
            yml_rep = str(yml_rep)
        elif not isinstance(yml_rep, str):
            raise TableEntryInvalidYmlRepresentationError("Could not parse value[{}] of type[{}] as string".format(
                yml_rep, type(yml_rep).__name__))

        try:
            byte_rep = standard_text_to_byte_list(yml_rep, cls.size, True)
        except ValueError as e:
            raise TableEntryInvalidYmlRepresentationError(str(e))

        return yml_rep


class EbEventFlagTableEntry(LittleEndianHexIntegerTableEntry):
    name = "Event Flag"
    size = 2


class EbPointerToVariableSizeEntryTableEntry(TableEntry):
    @staticmethod
    def create(pointer_table_entry, data_table_entry):
        return type("EbPointerToVariableSizeEntryTableEntry_{}".format(data_table_entry.__name__),
                    (EbPointerToVariableSizeEntryTableEntry,),
                    {"pointer_table_entry": pointer_table_entry,
                     "data_table_entry": data_table_entry,
                     "size": pointer_table_entry.size})

    @classmethod
    def from_block(cls, block, offset):
        data_offset = from_snes_address(cls.pointer_table_entry.from_block(block, offset))
        return cls.data_table_entry.from_block(block, data_offset)

    @classmethod
    def to_block(cls, block, offset, value):
        data_size = cls.data_table_entry.to_block_size(value)
        data_offset = block.allocate(size=data_size)
        cls.pointer_table_entry.to_block(block, offset, to_snes_address(data_offset))
        cls.data_table_entry.to_block(block, data_offset, value)

    @classmethod
    def to_yml_rep(cls, value):
        return cls.data_table_entry.to_yml_rep(value)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        return cls.data_table_entry.from_yml_rep(yml_rep)

    @classmethod
    def yml_rep_hex_labels(cls):
        return cls.data_table_entry.yml_rep_hex_labels()


class EbBankPointerToVariableSizeEntryTableEntry(EbPointerToVariableSizeEntryTableEntry):
    @staticmethod
    def create(pointer_table_entry, data_table_entry, bank):
        return type("EbBankPointerToVariableSizeEntryTableEntry_{}".format(data_table_entry.__name__),
                    (EbBankPointerToVariableSizeEntryTableEntry,),
                    {"pointer_table_entry": pointer_table_entry,
                     "data_table_entry": data_table_entry,
                     "size": pointer_table_entry.size,
                     "bank": bank})

    @classmethod
    def from_block(cls, block, offset):
        data_offset = cls.pointer_table_entry.from_block(block, offset)
        data_offset |= (cls.bank << 16)
        return cls.data_table_entry.from_block(block, data_offset)

    @classmethod
    def to_block(cls, block, offset, value):
        data_size = cls.data_table_entry.to_block_size(value)
        data_offset = block.allocate(size=data_size, can_write_to=partial(is_in_bank, cls.bank))
        cls.pointer_table_entry.to_block(block, offset, to_snes_address(data_offset))
        cls.data_table_entry.to_block(block, data_offset, value)


class EbRowTableEntry(GenericLittleEndianRowTableEntry):
    TABLE_ENTRY_CLASS_MAP = dict(
        GenericLittleEndianRowTableEntry.TABLE_ENTRY_CLASS_MAP,
        **{"pointer": (EbPointerTableEntry, ["name", "size"]),
           "hilomid pointer": (EbHiLoMidPointerTableEntry, ["name", "size"]),
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


def eb_table_from_offset(offset, single_column=None, matrix_dimensions=None, hidden_columns=None, num_rows=None,
                         name=None):
    if hidden_columns is None:
        hidden_columns = []

    try:
        schema_specification = _EB_SCHEMA_MAP[offset]
    except KeyError:
        raise InvalidArgumentError("Could not setup EbTable from unknown offset[{:#x}]".format(offset))

    if single_column:
        schema = single_column
    else:
        schema = EbRowTableEntry.from_schema_specification(schema_specification=schema_specification["entries"],
                                                           hidden_columns=hidden_columns)

    if matrix_dimensions:
        matrix_width, matrix_height = matrix_dimensions
        return MatrixTable(
            schema=schema,
            matrix_height=matrix_height,
            name=name or schema_specification["name"],
            size=schema_specification["size"])
    else:
        return Table(
            schema=schema,
            name=name or schema_specification["name"],
            size=schema_specification["size"],
            num_rows=num_rows)