from nose.tools import assert_dict_equal, assert_list_equal

from coilsnake.model.common.blocks import Block
from coilsnake.model.common.table_new import GenericLittleEndianTable
from tests.coilsnake_test import BaseTestCase


class GenericTestTable(BaseTestCase):
    def test_from_block(self):
        table = self.TABLE_CLASS(num_rows=len(self.TABLE_VALUES),
                                 schema_specification=self.TABLE_SCHEMA)
        block = Block()
        block.from_list(self.BLOCK_DATA)
        table.from_block(block, 0)

        assert_list_equal(table.values, self.TABLE_VALUES)

    def test_to_block(self):
        block = Block()
        block.from_list([0] * len(self.BLOCK_DATA))
        table = self.TABLE_CLASS(num_rows=len(self.TABLE_VALUES),
                                 schema_specification=self.TABLE_SCHEMA)
        table.values = self.TABLE_VALUES
        table.to_block(block, 0)

        assert_list_equal(block.to_list(), self.BLOCK_DATA)

    def test_from_yml_rep(self):
        table = self.TABLE_CLASS(num_rows=len(self.TABLE_VALUES),
                                 schema_specification=self.TABLE_SCHEMA)
        table.from_yml_rep(self.YML_REP)

        assert_list_equal(table.values, self.TABLE_VALUES)

    def test_to_yml_rep(self):
        table = self.TABLE_CLASS(num_rows=len(self.TABLE_VALUES),
                                 schema_specification=self.TABLE_SCHEMA)
        table.values = self.TABLE_VALUES
        assert_dict_equal(table.to_yml_rep(), self.YML_REP)


class TestGenericLittleEndianTable(GenericTestTable):
    TABLE_CLASS = GenericLittleEndianTable
    TABLE_SCHEMA = [
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
         "values": ["Zeroth", "First", "Second", "Third", "Fourth", "Fifth"]}
    ]
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
                  255,  # Second row
                  0, 0, 0,
                  0xcd, 0xab,
                  0x99,
                  0x08, 0x80,
                  0, 0, 0,
                  0xff, 0x00, 0x9f, 0xf1, 0xaa,
                  1,
                  0, 0,
                  6]
    TABLE_VALUES = [[72,  # First row
                     0x1abcde,
                     0xf235,
                     0x10,
                     0x1110,
                     0x252423,
                     [0x00, 0x11, 0x22, 0x33, 0x44],
                     False,
                     True,
                     3],
                    [255,
                     0,
                     0xabcd,
                     0x99,
                     0x8008,
                     0x1,
                     [0xff, 0x00, 0x9f, 0xf1, 0xaa],
                     True,
                     False,
                     6]]
    YML_REP = {0: {"Default Integer": 72,
                   "Sized Integer": 0x1abcde,
                   "Sized Typed Integer": 0xf235,
                   "Hex Integer": 0x10,
                   "Sized Hex Integer": 0x1110,
                   "One-Based Integer": 0x252423,
                   "Byte Array": [0x00, 0x11, 0x22, 0x33, 0x44],
                   "Default Boolean": False,
                   "Sized Boolean": True,
                   "Enumerated Integer": "third"},
               1: {"Default Integer": 255,
                   "Sized Integer": 0,
                   "Sized Typed Integer": 0xabcd,
                   "Hex Integer": 0x99,
                   "Sized Hex Integer": 0x8008,
                   "One-Based Integer": 1,
                   "Byte Array": [0xff, 0x00, 0x9f, 0xf1, 0xaa],
                   "Default Boolean": True,
                   "Sized Boolean": False,
                   "Enumerated Integer": 6}
    }