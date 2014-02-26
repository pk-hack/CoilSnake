from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.table import EbTable
from tests.model.common.test_table_new import TestGenericLittleEndianTable, GenericTestTable


class TestEbTableGenericRegression(TestGenericLittleEndianTable):
    TABLE_CLASS = EbTable


class TestEbTable(GenericTestTable):
    TABLE_CLASS = EbTable
    TABLE_SCHEMA = [
        {"name": "EB Pointer",
         "type": "pointer",
         "size": 3},
        {"name": "EB Palette",
         "type": "palette",
         "size": 12},
        {"name": "EB Text",
         "type": "standardtext",
         "size": 5},
        {"name": "EB Null-Terminated Text",
         "type": "standardtext null-terminated",
         "size": 5}
    ]
    BLOCK_DATA = [0x45, 0x23, 0xf1,
                  0, 0, 37, 36, 106, 25, 31, 0, 234, 20, 34, 70,
                  132, 149, 131, 164, 97,  # "TeSt1"
                  147, 96, 97, 156, 0]  # "c01l"
    TABLE_VALUES = [[0xf12345,
                     EbPalette(1, 6, [0, 0, 0, 40, 8, 72, 80, 88, 48,
                                      248, 0, 0, 80, 56, 40, 16, 136, 136]),
                     "TeSt1",
                     "c01l"]]
    YML_REP = {0: {"EB Pointer": "$f12345",
                   "EB Palette": ["(0, 0, 0)",
                                  "(40, 8, 72)",
                                  "(80, 88, 48)",
                                  "(248, 0, 0)",
                                  "(80, 56, 40)",
                                  "(16, 136, 136)"],
                   "EB Text": "TeSt1",
                   "EB Null-Terminated Text": "c01l"}}