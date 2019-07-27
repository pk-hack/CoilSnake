import os
import os.path

import mock
from nose.tools import assert_equal, assert_true, assert_dict_equal, assert_false, assert_is_none

from coilsnake.model.eb.pointers import EbPointer
from coilsnake.modules.eb import CccInterfaceModule
from coilsnake.util.eb.pointer import from_snes_address
from tests.coilsnake_test import BaseTestCase, TemporaryWritableFileTestCase, TEST_DATA_DIR


class TestCccInterfaceModule(BaseTestCase, TemporaryWritableFileTestCase):
    def setup(self):
        super(TestCccInterfaceModule, self).setup()
        self.mock = mock.Mock()
        self.module = CccInterfaceModule.CccInterfaceModule()

    def teardown(self):
        super(TestCccInterfaceModule, self).teardown()
        del self.mock
        del self.module

    def test_write_to_project(self):
        def resource_open(a, b, c):
            return self.temporary_wo_file

        self.module.write_to_project(resource_open)

        assert_true(os.path.isfile(self.temporary_wo_file_name))
        assert_equal(0, os.path.getsize(self.temporary_wo_file_name))

    def test_read_from_project(self):
        with open(os.path.join(TEST_DATA_DIR, 'summary.txt'), 'r') as summary_file:
            def resource_open(a, b, c):
                return summary_file

            self.module.read_from_project(resource_open)

        assert_equal((from_snes_address(0xf10000), from_snes_address(0xf19430)), self.module.used_range)
        assert_dict_equal(
            {
                'file1.test1': 0xc23456,
                'file1.test2': 0xf18cfb,
                'file1.label_with_a_very_very_very_very_long_name': 0xf18e4f,
                'short_module.entry1': 0xf00d13
            },
            EbPointer.label_address_map)

    def test_read_from_project_empty_summary(self):
        def resource_open(a, b, c):
            return self.temporary_wo_file

        self.module.write_to_project(resource_open)

        with open(self.temporary_wo_file_name, 'r') as summary_file:
            def resource_open(a, b, c):
                return summary_file

            self.module.read_from_project(resource_open)

        assert_is_none(self.module.used_range)
        assert_false(EbPointer.label_address_map)

    def test_read_from_project_blank_summary(self):
        with open(os.path.join(TEST_DATA_DIR, 'summary_blank.txt'), 'r') as summary_file:
            def resource_open(a, b, c):
                return summary_file

            self.module.read_from_project(resource_open)

        assert_is_none(self.module.used_range)
        assert_false(EbPointer.label_address_map)

    def test_write_to_rom(self):
        self.module.write_to_rom(self.mock)
        assert_false(self.mock.mark_allocated.called)

        self.module.used_range = (0x312345, 0x345678)
        self.module.write_to_rom(self.mock)

        self.mock.mark_allocated.assert_called_once_with((0x312345, 0x345678))