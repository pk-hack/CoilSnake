from nose.tools import assert_list_equal, assert_tuple_equal, assert_dict_equal, assert_equal
from nose.tools.nontrivial import raises

from coilsnake.exceptions.common.exceptions import TableSchemaError
from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.enemy_groups import MapEnemyGroupTableEntry
from tests.coilsnake_test import BaseTestCase


TEST_CASES = [
    {"block_rep": [0x45, 0x03, 50, 60,
                   8, 0x08, 0x01,
                   8, 0x53, 0x02],
     "value_rep": ([0x345, 50, 60],
                   [[8, 0x108]],
                   [[8, 0x253]]),
     "yml_rep": {"Event Flag": 0x345,
                 "Sub-Group 1 Rate": 50,
                 "Sub-Group 2 Rate": 60,
                 "Sub-Group 1": {0: {"Probability": 8, "Enemy Group": 0x108}},
                 "Sub-Group 2": {0: {"Probability": 8, "Enemy Group": 0x253}}}
     },
    {"block_rep": [0x45, 0x03, 50, 0,
                   8, 0x08, 0x01],
     "value_rep": ([0x345, 50, 0],
                   [[8, 0x108]],
                   []),
     "yml_rep": {"Event Flag": 0x345,
                 "Sub-Group 1 Rate": 50,
                 "Sub-Group 2 Rate": 0,
                 "Sub-Group 1": {0: {"Probability": 8, "Enemy Group": 0x108}},
                 "Sub-Group 2": {}},
     },
    {"block_rep": [0x45, 0x03, 0, 50,
                   8, 0x08, 0x01],
     "value_rep": ([0x345, 0, 50],
                   [],
                   [[8, 0x108]]),
     "yml_rep": {"Event Flag": 0x345,
                 "Sub-Group 1 Rate": 0,
                 "Sub-Group 2 Rate": 50,
                 "Sub-Group 1": {},
                 "Sub-Group 2": {0: {"Probability": 8, "Enemy Group": 0x108}}},
     },
    {"block_rep": [0x23, 0x01, 40, 50,
                   2, 0x08, 0x01, 3, 0x23, 0x00, 1, 0x1f, 0x00, 2, 0x88, 0x01,
                   7, 0x53, 0x02, 1, 0x69, 0x00],
     "value_rep": ([0x123, 40, 50],
                   [[2, 0x108], [3, 0x23], [1, 0x1f], [2, 0x188]],
                   [[7, 0x253], [1, 0x69]]),
     "yml_rep": {"Event Flag": 0x123,
                 "Sub-Group 1 Rate": 40,
                 "Sub-Group 2 Rate": 50,
                 "Sub-Group 1": {0: {"Probability": 2, "Enemy Group": 0x108},
                                 1: {"Probability": 3, "Enemy Group": 0x23},
                                 2: {"Probability": 1, "Enemy Group": 0x1f},
                                 3: {"Probability": 2, "Enemy Group": 0x188}},
                 "Sub-Group 2": {0: {"Probability": 7, "Enemy Group": 0x253},
                                 1: {"Probability": 1, "Enemy Group": 0x69}}}
     },
]


class TestMapEnemyGroupTableEntry(BaseTestCase):
    def test_from_block(self):
        for test_case in TEST_CASES:
            block = Block()
            block.from_list(test_case["block_rep"])
            value = MapEnemyGroupTableEntry.from_block(block, 0)
            assert_tuple_equal(test_case["value_rep"], value)

    def test_to_block(self):
        for test_case in TEST_CASES:
            block_size = MapEnemyGroupTableEntry.to_block_size(test_case["value_rep"])
            assert_equal(len(test_case["block_rep"]), block_size)

            block = Block(size=block_size)
            MapEnemyGroupTableEntry.to_block(block, 0, test_case["value_rep"])
            assert_list_equal(test_case["block_rep"], block.to_list())

    def test_to_yml_rep(self):
        for test_case in TEST_CASES:
            yml_rep = MapEnemyGroupTableEntry.to_yml_rep(test_case["value_rep"])
            assert_dict_equal(test_case["yml_rep"], yml_rep)

    def test_from_yml_rep(self):
        for test_case in TEST_CASES:
            value_rep = MapEnemyGroupTableEntry.from_yml_rep(test_case["yml_rep"])
            assert_tuple_equal(test_case["value_rep"], value_rep)

    @raises(TableSchemaError)
    def test_from_yml_rep_low_probability(self):
        MapEnemyGroupTableEntry.from_yml_rep(
            {"Event Flag": 0x345,
             "Sub-Group 1 Rate": 50,
             "Sub-Group 2 Rate": 0,
             "Sub-Group 1": {0: {"Probability": 7, "Enemy Group": 0x108}},
             "Sub-Group 2": {}},
        )

    @raises(TableSchemaError)
    def test_from_yml_rep_high_probability(self):
        MapEnemyGroupTableEntry.from_yml_rep(
            {"Event Flag": 0x345,
             "Sub-Group 1 Rate": 50,
             "Sub-Group 2 Rate": 0,
             "Sub-Group 1": {0: {"Probability": 9, "Enemy Group": 0x108}},
             "Sub-Group 2": {}},
        )

    def test_hex_labels(self):
        assert_equal(["Event Flag"], MapEnemyGroupTableEntry.yml_rep_hex_labels())