from coilsnake.exceptions.common.exceptions import TableEntryInvalidYmlRepresentationError, TableSchemaError
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.table import EbRowTableEntry
from tests.model.common.test_table import TestGenericLittleEndianTable, GenericTestTable


class TestEbTableGenericRegression(TestGenericLittleEndianTable):
    TABLE_SCHEMA = EbRowTableEntry.from_schema_specification(TestGenericLittleEndianTable.TABLE_SCHEMA_SPECIFICATION)


class TestEbTable(GenericTestTable):
    TABLE_SCHEMA_SPECIFICATION = [
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
    TABLE_SCHEMA = EbRowTableEntry.from_schema_specification(TABLE_SCHEMA_SPECIFICATION)

    BLOCK_DATA = [0x45, 0x23, 0xf1,
                  0, 0, 37, 36, 106, 25, 31, 0, 234, 20, 34, 70,
                  132, 149, 131, 164, 97,  # "TeSt1"
                  147, 96, 97, 156, 0,  # "c01l"
                  0x02, 0xda, 0xc6,
                  0, 0, 37, 36, 106, 25, 31, 0, 234, 20, 34, 70,
                  101, 120, 130, 132, 0,  # "5HRT"
                  119, 81, 0, 0, 0]  # "G!"
    TABLE_VALUES = [[0xf12345,
                     EbPalette(1, 6, [0, 0, 0, 40, 8, 72, 80, 88, 48,
                                      248, 0, 0, 80, 56, 40, 16, 136, 136]),
                     "TeSt1",
                     "c01l"],
                    [0xc6da02,
                     EbPalette(1, 6, [0, 0, 0, 40, 8, 72, 80, 88, 48,
                                      248, 0, 0, 80, 56, 40, 16, 136, 136]),
                     "5HRT",
                     "G!"]]
    YML_REP = {0: {"EB Pointer": "$f12345",
                   "EB Palette": ["(0, 0, 0)",
                                  "(40, 8, 72)",
                                  "(80, 88, 48)",
                                  "(248, 0, 0)",
                                  "(80, 56, 40)",
                                  "(16, 136, 136)"],
                   "EB Text": "TeSt1",
                   "EB Null-Terminated Text": "c01l"},
               1: {"EB Pointer": "$c6da02",
                   "EB Palette": ["(0, 0, 0)",
                                  "(40, 8, 72)",
                                  "(80, 88, 48)",
                                  "(248, 0, 0)",
                                  "(80, 56, 40)",
                                  "(16, 136, 136)"],
                   "EB Text": "5HRT",
                   "EB Null-Terminated Text": "G!"}}
    BAD_YML_REPS = [(0, "EB Pointer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Pointer": None})}),
                    (0, "EB Pointer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Pointer": 1})}),
                    (0, "EB Pointer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Pointer": ''})}),
                    (0, "EB Pointer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Pointer": '$'})}),
                    (0, "EB Pointer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Pointer": '$invalid'})}),
                    (0, "EB Pointer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Pointer": '$-1'})}),
                    (0, "EB Pointer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Pointer": '$1000000'})}),
                    (0, "EB Pointer", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Pointer": 'unknown.label'})}),
                    (0, "EB Palette", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Palette": None})}),
                    (0, "EB Palette", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Palette": 25})}),
                    (0, "EB Palette", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Palette": ["(0, 0, 0)"]})}),
                    (0, "EB Palette", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Palette": [None,
                                                            "(40, 8, 72)",
                                                            "(80, 88, 48)",
                                                            "(248, 0, 0)",
                                                            "(80, 56, 40)",
                                                            "(16, 136, 136)"]})}),
                    (0, "EB Palette", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Palette": [1,
                                                            "(40, 8, 72)",
                                                            "(80, 88, 48)",
                                                            "(248, 0, 0)",
                                                            "(80, 56, 40)",
                                                            "(16, 136, 136)"]})}),
                    (0, "EB Palette", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Palette": ["invalid",
                                                            "(40, 8, 72)",
                                                            "(80, 88, 48)",
                                                            "(248, 0, 0)",
                                                            "(80, 56, 40)",
                                                            "(16, 136, 136)"]})}),
                    (0, "EB Text", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Text": None})}),
                    (0, "EB Text", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Text": "2 long"})}),
                    (0, "EB Null-Terminated Text", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Null-Terminated Text": None})}),
                    (0, "EB Null-Terminated Text", TableSchemaError, TableEntryInvalidYmlRepresentationError,
                     {0: dict(YML_REP[0], **{"EB Null-Terminated Text": "2long"})}),
    ]