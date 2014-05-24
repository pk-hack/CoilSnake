from nose.tools import assert_dict_equal, assert_list_equal, assert_raises, assert_equal, assert_is_instance
from nose.tools.nontrivial import raises

from coilsnake.exceptions.common.exceptions import TableError, \
    TableEntryInvalidYmlRepresentationError, TableEntryMissingDataError, TableSchemaError
from coilsnake.model.common.blocks import Block
from coilsnake.model.common.table import Table, GenericLittleEndianRowTableEntry, BitfieldTableEntry
from coilsnake.util.common.type import GenericEnum
from tests.coilsnake_test import BaseTestCase


class GenericTestTable(BaseTestCase):
    def test_from_block(self):
        table = Table(num_rows=len(self.TABLE_VALUES),
                      schema=self.TABLE_SCHEMA)
        block = Block()
        block.from_list(self.BLOCK_DATA)
        table.from_block(block, 0)

        assert_list_equal(table.values, self.TABLE_VALUES)

    def test_to_block(self):
        block = Block()
        block.from_list([0] * len(self.BLOCK_DATA))
        table = Table(num_rows=len(self.TABLE_VALUES),
                      schema=self.TABLE_SCHEMA)
        table.values = self.TABLE_VALUES
        table.to_block(block, 0)

        assert_list_equal(block.to_list(), self.BLOCK_DATA)

    def test_from_yml_rep(self):
        table = Table(num_rows=len(self.TABLE_VALUES),
                      schema=self.TABLE_SCHEMA)
        table.from_yml_rep(self.YML_REP)

        assert_list_equal(table.values, self.TABLE_VALUES)

    def test_to_yml_rep(self):
        table = Table(num_rows=len(self.TABLE_VALUES),
                      schema=self.TABLE_SCHEMA)
        table.values = self.TABLE_VALUES
        assert_dict_equal(table.to_yml_rep(), self.YML_REP)

    def test_from_yml_rep_errors(self):
        table = Table(num_rows=1,
                      schema=self.TABLE_SCHEMA)
        for row, column_name, expected_error, expected_error_cause, yml_rep in self.BAD_YML_REPS:
            print row, column_name, expected_error
            with assert_raises(TableError) as cm:
                table.from_yml_rep(yml_rep)
            e = cm.exception
            assert_equal(e.entry, 0)
            assert_equal(e.field, column_name)
            assert_is_instance(e.cause, expected_error)
            if expected_error_cause:
                assert_is_instance(e.cause.cause, expected_error_cause)


class TestGenericLittleEndianTable(GenericTestTable):
    TABLE_SCHEMA_SPECIFICATION = [
        {"name": "Default Integer"},
        {"name": "Sized Integer",
         "size": 3},
        {"name": "Sized Typed Integer",
         "type": "int",
         "size": 2},
        {"name": "Hex Integer",
         "type": "hexint"},
        {"name": "Sized Hex Integer",
         "type": "hexint",
         "size": 2},
        {"name": "One-Based Integer",
         "type": "one-based int",
         "size": 3},
        {"name": "Byte Array",
         "type": "bytearray",
         "size": 5},
        {"name": "Default Boolean",
         "type": "boolean"},
        {"name": "Sized Boolean",
         "type": "boolean",
         "size": 2},
        {"name": "Enumerated Integer",
         "type": "int",
         "values": ["Zeroth", "First", "Second", "Third", "Fourth", "Fifth"]},
        {"name": "Dict Enumerated Integer",
         "type": "int",
         "values": {20: "NiJu", 33: "SanJuSan"}},
        {"name": "Bitfield",
         "type": "bitfield",
         "bitvalues": ["bit0", "bit1", "bit2", "bit3", "bit4", "bit5", "bit6"]}
    ]
    TABLE_SCHEMA = GenericLittleEndianRowTableEntry.from_schema_specification(TABLE_SCHEMA_SPECIFICATION)

    BLOCK_DATA = [72,  # First row
                  0xde, 0xbc, 0x1a,
                  0x35, 0xf2,
                  0x10,
                  0x10, 0x11,
                  0x22, 0x24, 0x25,
                  0x00, 0x11, 0x22, 0x33, 0x44,
                  0,
                  1, 0,
                  3,
                  20,
                  0b00001011,
                  255,  # Second row
                  0, 0, 0,
                  0xcd, 0xab,
                  0x99,
                  0x08, 0x80,
                  0, 0, 0,
                  0xff, 0x00, 0x9f, 0xf1, 0xaa,
                  1,
                  0, 0,
                  6,
                  12,
                  0b11100100]
    TABLE_VALUES = [[72,  # First row
                     0x1abcde,
                     0xf235,
                     0x10,
                     0x1110,
                     0x252421,
                     [0x00, 0x11, 0x22, 0x33, 0x44],
                     False,
                     True,
                     3,
                     20,
                     {0, 1, 3}],
                    [255,
                     0,
                     0xabcd,
                     0x99,
                     0x8008,
                     -1,
                     [0xff, 0x00, 0x9f, 0xf1, 0xaa],
                     True,
                     False,
                     6,
                     12,
                     {2, 5, 6, 7}]]
    YML_REP = {0: {"Default Integer": 72,
                   "Sized Integer": 0x1abcde,
                   "Sized Typed Integer": 0xf235,
                   "Hex Integer": 0x10,
                   "Sized Hex Integer": 0x1110,
                   "One-Based Integer": 0x252421,
                   "Byte Array": [0x00, 0x11, 0x22, 0x33, 0x44],
                   "Default Boolean": False,
                   "Sized Boolean": True,
                   "Enumerated Integer": "third",
                   "Dict Enumerated Integer": "niju",
                   "Bitfield": ["bit0", "bit1", "bit3"]},
               1: {"Default Integer": 255,
                   "Sized Integer": 0,
                   "Sized Typed Integer": 0xabcd,
                   "Hex Integer": 0x99,
                   "Sized Hex Integer": 0x8008,
                   "One-Based Integer": None,
                   "Byte Array": [0xff, 0x00, 0x9f, 0xf1, 0xaa],
                   "Default Boolean": True,
                   "Sized Boolean": False,
                   "Enumerated Integer": 6,
                   "Dict Enumerated Integer": 12,
                   "Bitfield": [7, "bit2", "bit5", "bit6"]}
    }
    BAD_YML_REPS = [(0, None, TableEntryMissingDataError, None, {}),
                    (0, "Default Integer", TableSchemaError, TableEntryMissingDataError,
                     {0: {"Sized Integer": 0x1abcde,
                          "Sized Typed Integer": 0xf235,
                          "Hex Integer": 0x10,
                          "Sized Hex Integer": 0x1110,
                          "One-Based Integer": 0x252423,
                          "Byte Array": [0x00, 0x11, 0x22, 0x33, 0x44],
                          "Default Boolean": False,
                          "Sized Boolean": True,
                          "Enumerated Integer": "third",
                          "Bitfield": ["bit0", "bit1", "bit3"]}}),
                    (0, "Default Boolean", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Default Boolean": None})}),
                    (0, "Default Boolean", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Default Boolean": "invalid string"})}),
                    (0, "Default Integer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Default Integer": None})}),
                    (0, "Default Integer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Default Integer": "invalid string"})}),
                    (0, "Default Integer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Default Integer": -1})}),
                    (0, "Default Integer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Default Integer": 0x100})}),
                    (0, "Enumerated Integer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Enumerated Integer": "invalid string"})}),
                    (0, "Enumerated Integer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Enumerated Integer": None})}),
                    (0, "Enumerated Integer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Enumerated Integer": -1})}),
                    (0, "Enumerated Integer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Enumerated Integer": 0x100})}),
                    (0, "Byte Array", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Byte Array": 0})}),
                    (0, "Byte Array", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Byte Array": ["invalid string"]})}),
                    (0, "Byte Array", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Byte Array": [5, 4, -1]})}),
                    (0, "Byte Array", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Byte Array": [5, 256]})}),
                    (0, "Bitfield", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Bitfield": "invalid string"})}),
                    (0, "Bitfield", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Bitfield": ["invalid string"]})}),
                    (0, "Bitfield", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"Bitfield": [8]})}),
    ]


class TestBitfieldTableEntry(BaseTestCase):
    enumeration_class = GenericEnum.create(name="test", values=["a", "b", "c"])
    entry_class = BitfieldTableEntry.create(name="test", enumeration_class=enumeration_class, size=1)

    def test_from_yml_rep_legacy(self):
        assert_equal(self.entry_class.from_yml_rep(0), set())
        assert_equal(self.entry_class.from_yml_rep(1), {0})
        assert_equal(self.entry_class.from_yml_rep(2), {1})
        assert_equal(self.entry_class.from_yml_rep(3), {0, 1})
        assert_equal(self.entry_class.from_yml_rep(255), {0, 1, 2, 3, 4, 5, 6, 7})

    @raises(TableEntryInvalidYmlRepresentationError)
    def test_from_yml_rep_legacy_too_small(self):
        self.entry_class.from_yml_rep(-1)

    @raises(TableEntryInvalidYmlRepresentationError)
    def test_from_yml_rep_legacy_too_large(self):
        self.entry_class.from_yml_rep(256)