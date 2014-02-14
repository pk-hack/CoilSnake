import os
import os.path
from nose.tools import assert_equal, assert_true, assert_dict_equal, assert_false, assert_is_none

from coilsnake.modules.eb import CccInterfaceModule, EbModule
from tests.coilsnake_test import CoilSnakeTestCase


class TestCccInterfaceModule(CoilSnakeTestCase):
    def setup(self):
        self.setup_mock()
        self.setup_temporary_wo_file()
        self.module = CccInterfaceModule.CccInterfaceModule()

    def teardown(self):
        self.teardown_temporary_wo_file()
        del self.module

    def test_write_to_project(self):
        def resource_open(a, b):
            return self.temporary_wo_file

        self.module.write_to_project(resource_open)

        assert_true(os.path.isfile(self.temporary_wo_file_name))
        assert_equal(0, os.path.getsize(self.temporary_wo_file_name))

    def test_read_from_project(self):
        with open(os.path.join(self.TEST_DATA_DIR, 'summary.txt'), 'r') as summary_file:
            def resource_open(a, b):
                return summary_file

            self.module.read_from_project(resource_open)

        assert_equal((EbModule.toRegAddr(0xf10000), EbModule.toRegAddr(0xf19430)), self.module.used_range)
        assert_dict_equal(
            {
                'file1.test1': 0xc23456,
                'file1.test2': 0xf18cfb,
                'file1.label_with_a_very_very_very_very_long_name': 0xf18e4f,
                'short_module.entry1': 0xf00d13
            },
            EbModule.address_labels)

    def test_read_from_project_empty_summary(self):
        def resource_open(a, b):
            return self.temporary_wo_file

        self.module.write_to_project(resource_open)

        with open(self.temporary_wo_file_name, 'r') as summary_file:
            def resource_open(a, b):
                return summary_file

            self.module.read_from_project(resource_open)

        assert_is_none(self.module.used_range)
        assert_false(EbModule.address_labels)

    def test_read_from_project_blank_summary(self):
        with open(os.path.join(self.TEST_DATA_DIR, 'summary_blank.txt'), 'r') as summary_file:
            def resource_open(a, b):
                return summary_file

            self.module.read_from_project(resource_open)

        assert_is_none(self.module.used_range)
        assert_false(EbModule.address_labels)

    def test_write_to_rom(self):
        self.module.write_to_rom(self.mock)
        assert_false(self.mock.mark_allocated.called)

        self.module.used_range = (0x312345, 0x345678)
        self.module.write_to_rom(self.mock)

        self.mock.mark_allocated.assert_called_once_with((0x312345, 0x345678))