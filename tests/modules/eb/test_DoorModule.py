import os

from nose.tools import assert_equal, assert_true, assert_dict_equal
from nose.tools.nontrivial import nottest

from coilsnake.modules.eb.DoorModule import DoorModule
from coilsnake.model.common.blocks import Rom
from tests.coilsnake_test import BaseTestCase, TemporaryWritableFileTestCase, TEST_DATA_DIR


class TestDoorModule(BaseTestCase, TemporaryWritableFileTestCase):
    def setup(self):
        super(TestDoorModule, self).setup()
        self.module = DoorModule()

    def teardown(self):
        super(TestDoorModule, self).teardown()
        del self.module

    @nottest
    def test_read_from_rom_using_rom(self, rom):
        self.module.read_from_rom(rom)

        # Very simple verification by checking the amount of different types of doors that were read
        assert_equal(len(self.module.door_areas), 40 * 32)
        num_door_types = dict()
        num_empty_areas = 0
        for area in self.module.door_areas:
            if area is not None and len(area) > 0:
                for door in area:
                    if door.__class__.__name__ not in num_door_types:
                        num_door_types[door.__class__.__name__] = 1
                    else:
                        num_door_types[door.__class__.__name__] += 1
            else:
                num_empty_areas += 1
        assert_equal(num_empty_areas, 679)
        assert_dict_equal(num_door_types, {
            "SwitchDoor": 6,
            "EscalatorOrStairwayDoor": 92,
            "Door": 1072,
            "NpcDoor": 269,
            "RopeOrLadderDoor": 641,
        })

    def test_read_from_rom(self):
        with Rom() as rom:
            rom.from_file(os.path.join(TEST_DATA_DIR, 'roms', 'real_EarthBound.smc'))
            self.test_read_from_rom_using_rom(rom)

    @nottest
    def test_read_from_project_using_filename(self, filename):
        with open(filename, 'r', encoding="utf-8") as doors_file:
            def resource_open(a, b, astext):
                return doors_file

            self.module.read_from_project(resource_open)

        # Very simple verification by checking the amount of different types of doors that were read
        assert_equal(len(self.module.door_areas), 40 * 32)
        num_door_types = dict()
        num_empty_areas = 0
        for area in self.module.door_areas:
            if area is not None and len(area) > 0:
                for door in area:
                    if door.__class__.__name__ not in num_door_types:
                        num_door_types[door.__class__.__name__] = 1
                    else:
                        num_door_types[door.__class__.__name__] += 1
            else:
                num_empty_areas += 1
        assert_equal(num_empty_areas, 679)
        assert_dict_equal(num_door_types, {
            "SwitchDoor": 6,
            "EscalatorOrStairwayDoor": 92,
            "Door": 1072,
            "NpcDoor": 269,
            "RopeOrLadderDoor": 641,
        })

    def test_write_to_project(self):
        with Rom() as rom:
            rom.from_file(os.path.join(TEST_DATA_DIR, 'roms', 'real_EarthBound.smc'))
            self.module.read_from_rom(rom)

        def resource_open(a, b, astext):
            return self.temporary_wo_file

        self.module.write_to_project(resource_open)

        assert_true(os.path.isfile(self.temporary_wo_file_name))
        self.temporary_wo_file.close()
        self.test_read_from_project_using_filename(self.temporary_wo_file_name)

    def test_write_to_rom(self):
        with Rom() as rom:
            rom.from_file(os.path.join(TEST_DATA_DIR, 'roms', 'real_EarthBound.smc'))
            self.module.read_from_rom(rom)

        def resource_open(a, b, astext):
            return self.temporary_wo_file

        self.module.write_to_project(resource_open)

        self.temporary_wo_file = open(self.temporary_wo_file_name, encoding="utf-8", newline="\n")
        self.module.read_from_project(resource_open)

        with Rom() as rom:
            rom.from_file(os.path.join(TEST_DATA_DIR, 'roms', 'real_EarthBound.smc'))
            self.module.write_to_rom(rom)
            self.test_read_from_rom_using_rom(rom)