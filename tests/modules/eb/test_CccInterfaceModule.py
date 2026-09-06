import os
import os.path

import unittest.mock as mock

from coilsnake.model.eb.pointers import EbPointer
from coilsnake.modules.eb import CccInterfaceModule
from coilsnake.util.eb.pointer import from_snes_address
from tests.coilsnake_test import BaseTestCase, TemporaryWritableFileTestCase, TEST_DATA_DIR


class TestCccInterfaceModule(BaseTestCase, TemporaryWritableFileTestCase):
    def setUp(self):
        super(TestCccInterfaceModule, self).setUp()
        self.mock = mock.Mock()
        self.module = CccInterfaceModule.CccInterfaceModule()

    def tearDown(self):
        super(TestCccInterfaceModule, self).tearDown()
        del self.mock
        del self.module

    def test_write_to_project(self):
        def resource_open(a, b, c):
            return self.temporary_wo_file

        self.module.write_to_project(resource_open)

        self.assertTrue(os.path.isfile(self.temporary_wo_file_name))
        self.assertEqual(0, os.path.getsize(self.temporary_wo_file_name))

    def test_read_from_project(self):
        with open(os.path.join(TEST_DATA_DIR, 'summary.txt'), 'r') as summary_file:
            def resource_open(a, b, c):
                return summary_file

            self.module.read_from_project(resource_open)

        self.assertEqual((from_snes_address(0xf10000), from_snes_address(0xf19430)), self.module.used_range)
        self.assertDictEqual(
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

        self.assertIsNone(self.module.used_range)
        self.assertFalse(EbPointer.label_address_map)

    def test_read_from_project_blank_summary(self):
        with open(os.path.join(TEST_DATA_DIR, 'summary_blank.txt'), 'r') as summary_file:
            def resource_open(a, b, c):
                return summary_file

            self.module.read_from_project(resource_open)

        self.assertIsNone(self.module.used_range)
        self.assertFalse(EbPointer.label_address_map)

    def test_write_to_rom(self):
        self.module.write_to_rom(self.mock)
        self.assertFalse(self.mock.mark_allocated.called)

        self.module.used_range = (0x312345, 0x345678)
        self.module.write_to_rom(self.mock)

        self.mock.mark_allocated.assert_called_once_with((0x312345, 0x345678))
