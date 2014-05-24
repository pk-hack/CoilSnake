from abc import abstractmethod
import logging

from coilsnake.exceptions.common.exceptions import InvalidArgumentError, IndexOutOfRangeError, \
    TableEntryInvalidYmlRepresentationError, TableError, TableEntryMissingDataError, TableEntryError, TableSchemaError
from coilsnake.util.common.helper import getitem_with_default, not_in_inclusive_range
from coilsnake.util.common.type import GenericEnum
from coilsnake.util.common.yml import convert_values_to_hex_repr, yml_load, yml_dump

log = logging.getLogger(__name__)


class TableEntry(object):
    name = "Unnamed TableEntry"

    @classmethod
    @abstractmethod
    def from_block(cls, block, offset):
        pass

    @classmethod
    @abstractmethod
    def to_block(cls, block, offset, value):
        pass

    @classmethod
    @abstractmethod
    def from_yml_rep(cls, yml_rep):
        pass

    @classmethod
    @abstractmethod
    def to_yml_rep(cls, value):
        pass

    @classmethod
    def yml_rep_hex_labels(cls):
        """Returns the keys for values which should be converted to hexidecimal in the yml representation returned by
        to_yml_rep."""
        return []


class BooleanTableEntry(TableEntry):
    @classmethod
    def from_block(cls, block, offset):
        return block.read_multi(offset, cls.size) != 0

    @classmethod
    def to_block(cls, block, offset, value):
        if value:
            block.write_multi(offset, 1, cls.size)
        else:
            block.write_multi(offset, 0, cls.size)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if isinstance(yml_rep, bool):
            return yml_rep
        else:
            raise TableEntryInvalidYmlRepresentationError("Could not parse value[{}] as a boolean. Valid values are "
                                                          "\"True\" or \"False\".".format(yml_rep))

    @classmethod
    def to_yml_rep(cls, value):
        return value


class LittleEndianIntegerTableEntry(TableEntry):
    @staticmethod
    def create(name, size):
        return type(name,
                    (LittleEndianIntegerTableEntry,),
                    {"name": name,
                     "size": size})

    @classmethod
    def from_block(cls, block, offset):
        return block.read_multi(offset, cls.size)

    @classmethod
    def to_block(cls, block, offset, value):
        block.write_multi(offset, value, cls.size)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if not isinstance(yml_rep, int):
            raise TableEntryInvalidYmlRepresentationError("Could not parse value[{}] of type[{}] as integer".format(
                yml_rep, type(yml_rep).__name__))
        elif not_in_inclusive_range(yml_rep, (0, (1 << (8 * cls.size)) - 1)):
            raise TableEntryInvalidYmlRepresentationError("Value[{}] is not valid, must be in range [{},{}]".format(
                yml_rep, 0, (1 << (8 * cls.size)) - 1))
        else:
            return yml_rep

    @classmethod
    def to_yml_rep(cls, value):
        return value


class LittleEndianHexIntegerTableEntry(LittleEndianIntegerTableEntry):
    @classmethod
    def yml_rep_hex_labels(cls):
        return [cls.name]


class LittleEndianOneBasedIntegerTableEntry(LittleEndianIntegerTableEntry):
    @classmethod
    def from_block(cls, block, offset):
        return super(LittleEndianOneBasedIntegerTableEntry, cls).from_block(block, offset) - 1

    @classmethod
    def to_block(cls, block, offset, value):
        super(LittleEndianOneBasedIntegerTableEntry, cls).to_block(block, offset, value + 1)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if yml_rep is None:
            return -1
        else:
            return super(LittleEndianOneBasedIntegerTableEntry, cls).from_yml_rep(yml_rep)

    @classmethod
    def to_yml_rep(cls, value):
        if value == -1:
            return None
        else:
            return super(LittleEndianOneBasedIntegerTableEntry, cls).to_yml_rep(value)


class EnumeratedLittleEndianIntegerTableEntry(LittleEndianIntegerTableEntry):
    @staticmethod
    def create(name, size, values):
        return type(name,
                    (EnumeratedLittleEndianIntegerTableEntry,),
                    {"name": name,
                     "size": size,
                     "enumeration_class": GenericEnum.create(name, values)})

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if isinstance(yml_rep, str):
            try:
                return cls.enumeration_class.fromstring(yml_rep)
            except InvalidArgumentError:
                raise TableEntryInvalidYmlRepresentationError(
                    "Could not parse invalid string[{}] as [{}]. Valid string values are: {}".format(
                    yml_rep, cls.name, ', '.join(cls.enumeration_class.values())))
        elif isinstance(yml_rep, int):
            return super(EnumeratedLittleEndianIntegerTableEntry, cls).from_yml_rep(yml_rep)
        else:
            raise TableEntryInvalidYmlRepresentationError("Could not parse value[{}] as [{}]".format(
                yml_rep, cls.name))

    @classmethod
    def to_yml_rep(cls, value):
        try:
            return cls.enumeration_class.tostring(value)
        except InvalidArgumentError:
            return value


class ByteListTableEntry(TableEntry):
    @staticmethod
    def create(name, size):
        return type(name, (ByteListTableEntry,), {"name": name, "size": size})

    @classmethod
    def from_block(cls, block, offset):
        return block[offset:offset + cls.size].to_list()

    @classmethod
    def to_block(cls, block, offset, value):
        block[offset:offset + cls.size] = value

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if not (isinstance(yml_rep, list) and all(isinstance(x, int) for x in yml_rep)):
            raise TableEntryInvalidYmlRepresentationError("Could not parse value[{}] to a list of integers"
                                                          .format(yml_rep))
        elif any(not_in_inclusive_range(x, (0, 0xff)) for x in yml_rep):
            raise TableEntryInvalidYmlRepresentationError("Byte list[{}] contains a value less than 0 or greater "
                                                          "than 255 (0xff)".format(yml_rep))

        return yml_rep

    @classmethod
    def to_yml_rep(cls, value):
        return cls.from_yml_rep(value)


class BitfieldTableEntry(TableEntry):
    @staticmethod
    def create(name, enumeration_class, size):
        return type(name, (BitfieldTableEntry,), {"name": name, "enumeration_class": enumeration_class, "size": size})

    @classmethod
    def from_block(cls, block, offset):
        block_value = block.read_multi(offset, cls.size)
        return cls._from_int(block_value)

    @classmethod
    def _from_int(cls, int_value):
        value = set()
        for i in range(cls.size * 8):
            if (1 << i) & int_value != 0:
                value.add(i)
        return value

    @classmethod
    def to_block(cls, block, offset, value):
        block_value = 0
        for i in value:
            block_value |= (1 << i)
        block.write_multi(offset, block_value, cls.size)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if isinstance(yml_rep, list) and all((isinstance(x, int) or isinstance(x, str)) for x in yml_rep):
            value = set()
            for entry in yml_rep:
                if isinstance(entry, str):
                    try:
                        entry = cls.enumeration_class.fromstring(entry)
                    except InvalidArgumentError:
                        raise TableEntryInvalidYmlRepresentationError("Could not parse string[{}] to type[{}]".format(
                            entry, cls.enumeration_class.__name__))

                if not (0 <= entry < (cls.size * 8)):
                    raise TableEntryInvalidYmlRepresentationError(
                        "Bitvalue value[{}] is not within a range of [0,{}) for its bitfield of size[{}]".format(
                            entry, 1 << cls.size, cls.size))

                value.add(entry)
            return value
        elif isinstance(yml_rep, int):
            if not (0 <= yml_rep < cls.size * 0x100):
                raise TableEntryInvalidYmlRepresentationError(
                    "Integer[{}] is not valid for a bitfield of size[{}]".format(yml_rep, cls.size))
            return cls._from_int(yml_rep)
        else:
            raise TableEntryInvalidYmlRepresentationError(
                "Expected list of bitvalues but instead got value[{}] of type[{}]".format(yml_rep,
                                                                                          type(yml_rep).__name__))

    @classmethod
    def to_yml_rep(cls, value):
        yml_rep = []
        for bitvalue in value:
            try:
                yml_rep.append(cls.enumeration_class.tostring(bitvalue))
            except InvalidArgumentError:
                yml_rep.append(bitvalue)
        yml_rep.sort()
        return yml_rep


class RowTableEntry(TableEntry):
    @classmethod
    def from_schema(cls, schema, name="CustomRowTableEntry", hidden_columns=set()):
        if type(hidden_columns) == list:
            hidden_columns = set(hidden_columns)
        elif type(hidden_columns) != set:
            raise InvalidArgumentError("Could not create RowTableEntry with invalid hidden_columns[{}]".format(
                hidden_columns))

        return type(name, (cls,), {"name": name,
                                   "size": sum([x.size for x in schema]),
                                   "schema": schema,
                                   "hidden_columns": hidden_columns})

    @classmethod
    def from_schema_specification(cls, schema_specification, name="CustomRowTableEntry", hidden_columns=set()):
        schema = map(cls.to_table_entry_class, schema_specification)
        return cls.from_schema(schema, name, hidden_columns)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        row = [None] * len(cls.schema)
        for i, column in enumerate(cls.schema):
            if column.name in cls.hidden_columns:
                row[i] = None
                continue

            try:
                column_yml_rep = yml_rep[column.name]
            except KeyError:
                error_message = "Column[{}] not found in yml representation".format(column.name)
                log.debug(error_message)
                raise TableSchemaError(field=column.name,
                                       cause=TableEntryMissingDataError(error_message))

            try:
                row[i] = column.from_yml_rep(column_yml_rep)
            except TableEntryError as e:
                log.debug("Error while parsing yml representation for column[{}]".format(column.name))
                raise TableSchemaError(field=column.name, cause=e)
            except Exception as e:
                log.debug("Unexpected error while parsing yml representation for column[{}]".format(column.name))
                raise TableSchemaError(field=column.name, cause=e)
        return row

    @classmethod
    def to_yml_rep(cls, value):
        yml_rep_row = dict()
        for value, column in zip(value, cls.schema):
            if column.name in cls.hidden_columns:
                continue

            try:
                yml_rep_row[column.name] = column.to_yml_rep(value)
            except Exception as e:
                log.debug("Error while serializing column[{}]".format(column.name))
                raise TableSchemaError(field=column.name, cause=e)
        return yml_rep_row

    @classmethod
    def from_block(cls, block, offset):
        row = [None] * len(cls.schema)
        for i, column in enumerate(cls.schema):
            try:
                row[i] = column.from_block(block, offset)
            except Exception as e:
                log.debug("Error while reading column[{}]]".format(column.name))
                raise TableSchemaError(field=column.name, cause=e)
            offset += column.size
        return row

    @classmethod
    def to_block(cls, block, offset, value):
        for value, column in zip(value, cls.schema):
            try:
                column.to_block(block, offset, value)
            except Exception as e:
                log.debug("Error while writing column[{}]".format(column.name))
                raise TableError(field=column.name, cause=e)
            offset += column.size

    @classmethod
    def yml_rep_hex_labels(cls):
        return [inner
                for outer in [x.yml_rep_hex_labels() for x in cls.schema]
                for inner in outer]


class GenericLittleEndianRowTableEntry(RowTableEntry):
    DEFAULT_TABLE_ENTRY_TYPE = "int"
    TABLE_ENTRY_CLASS_MAP = {"int": (LittleEndianIntegerTableEntry, ["name", "size"]),
                             "hexint": (LittleEndianHexIntegerTableEntry, ["name", "size"]),
                             "one-based int": (LittleEndianOneBasedIntegerTableEntry, ["name", "size"]),
                             "bytearray": (ByteListTableEntry, ["name", "size"]),
                             "boolean": (BooleanTableEntry, ["name", "size"])}

    @classmethod
    def to_table_entry_class(cls, column_specification):
        class_name = "GeneratedTableEntry_{}".format(column_specification["name"])
        column_specification["size"] = getitem_with_default(column_specification, "size", 1)
        column_specification["type"] = getitem_with_default(column_specification, "type", cls.DEFAULT_TABLE_ENTRY_TYPE)
        if (column_specification["type"] == "int") and ("values" in column_specification):
            return EnumeratedLittleEndianIntegerTableEntry.create(
                column_specification["name"],
                column_specification["size"],
                column_specification["values"]
            )
        elif (column_specification["type"] == "bitfield") and ("bitvalues" in column_specification):
            enumeration_class = GenericEnum.create(name=class_name, values=column_specification["bitvalues"])
            return BitfieldTableEntry.create(name=column_specification["name"],
                                             size=column_specification["size"],
                                             enumeration_class=enumeration_class)
        else:
            try:
                entry_class, parameter_list = cls.TABLE_ENTRY_CLASS_MAP[column_specification["type"]]
            except KeyError:
                raise InvalidArgumentError("Unknown table column type[{}]".format(column_specification["type"]))

            try:
                parameters = dict(map(lambda x: (x, column_specification[x]), parameter_list))
            except KeyError:
                raise InvalidArgumentError("Column[{}] in table schema not provided with all required attributes[{}]"
                                           .format(column_specification["name"], parameter_list))

            return type(class_name, (entry_class,), parameters)


class Table(object):
    def __init__(self, schema, name="Anonymous Table", size=None, num_rows=None):
        self.name = name

        if size is None and num_rows is None:
            raise InvalidArgumentError("Cannot create table[{}] with null size and null num_rows".format(self.name))

        self.schema = schema

        self.recreate(num_rows=num_rows, size=size)

    def recreate(self, num_rows=None, size=None):
        if num_rows is not None:
            self.num_rows = num_rows
        else:
            if size % self.schema.size != 0:
                raise InvalidArgumentError("Cannot create table[{}] with rows of size[{}] and total size[{}]".format(
                    self.name, self.schema.size, size))
            self.num_rows = size / self.schema.size

        self.size = self.schema.size * self.num_rows
        self.values = [None for i in range(self.num_rows)]

    def from_block(self, block, offset):
        for i in range(self.num_rows):
            try:
                self.values[i] = self.schema.from_block(block, offset)
            except TableSchemaError as e:
                raise TableError(table_name=self.name, entry=i, field=e.field, cause=e)

            offset += self.schema.size

    def to_block(self, block, offset):
        original_offset = offset
        for i, row in enumerate(self.values):
            try:
                self.schema.to_block(block, offset, row)
            except TableSchemaError as e:
                raise TableError(table_name=self.name, entry=i, field=e.field, cause=e)

            offset += self.schema.size
        return original_offset

    def from_yml_rep(self, yml_rep):
        if yml_rep is None:
            raise TableError(table_name=self.name, entry=None, field=None,
                             cause=TableEntryMissingDataError("No data found, please check the file"))
        for i in range(self.num_rows):
            try:
                yml_rep_row = yml_rep[i]
            except KeyError as e:
                raise TableError(table_name=self.name, entry=i, field=None,
                                 cause=TableEntryMissingDataError(
                                     "Row[{}] not found in table yml representation".format(i)))

            try:
                self.values[i] = self.schema.from_yml_rep(yml_rep_row)
            except TableSchemaError as e:
                raise TableError(table_name=self.name, entry=i, field=e.field, cause=e)

    def to_yml_rep(self):
        yml_rep = {}
        for i, row in enumerate(self.values):
            try:
                yml_rep[i] = self.schema.to_yml_rep(row)
            except TableSchemaError as e:
                raise TableError(table_name=self.name, entry=i, field=e.field, cause=e)
        return yml_rep

    def from_yml_file(self, f):
        yml_rep = yml_load(f)
        self.from_yml_rep(yml_rep)

    def to_yml_file(self, f, default_flow_style=False):
        yml_str_rep = yml_dump(self.to_yml_rep(), default_flow_style=default_flow_style)

        # Rewrite hexints in hexidecimal
        # The YAML parser does not offer this option, so this has to be done with a regex
        for hex_label in self.schema.yml_rep_hex_labels():
            yml_str_rep = convert_values_to_hex_repr(yml_str_rep, hex_label)

        f.write(yml_str_rep)

    def __getitem__(self, index):
        row = index
        if 0 <= row < self.num_rows:
            return self.values[row]
        else:
            raise IndexOutOfRangeError("Cannot get row[{}] from table of size[{}]".format(row, self.num_rows))

    def __setitem__(self, index, value):
        row = index
        if 0 <= row < self.num_rows:
            self.values[row] = value
        else:
            raise IndexOutOfRangeError("Cannot set row[{}] in table of size[{}]".format(row, self.num_rows))


class MatrixTable(Table):
    def __init__(self, schema, matrix_height, name="Anonymous Table", size=None, num_rows=None):
        super(MatrixTable, self).__init__(schema=schema, name=name, size=size, num_rows=num_rows)

        if self.num_rows % matrix_height != 0:
            raise InvalidArgumentError("Could not create MatrixTable with num_rows[{}] not evenly divisible "
                                       "by matrix_height[{}]".format(self.num_rows, matrix_height))
        self.matrix_height = matrix_height
        self.matrix_width = self.num_rows / matrix_height

    def from_yml_rep(self, yml_rep):
        yml_rep_unmatrixed = dict()
        for y in range(self.matrix_height):
            for x in range(self.matrix_width):
                yml_rep_unmatrixed[y * self.matrix_width + x] = yml_rep[y][x]
        super(MatrixTable, self).from_yml_rep(yml_rep_unmatrixed)

    def to_yml_rep(self):
        yml_rep_unmatrixed = super(MatrixTable, self).to_yml_rep()
        yml_rep = dict()
        for y in range(self.matrix_height):
            yml_rep_matrix_row = dict()
            for x in range(self.matrix_width):
                yml_rep_matrix_row[x] = yml_rep_unmatrixed[y * self.matrix_width + x]
            yml_rep[y] = yml_rep_matrix_row
        return yml_rep