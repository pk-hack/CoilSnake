from nose.tools import assert_equal, assert_true, assert_dict_equal, assert_false, assert_is_none, raises,\
    assert_list_equal, assert_raises, assert_not_equal
from nose.tools.nontrivial import nottest
import os

from coilsnake.modules.eb.EbModule import address_labels
from coilsnake.modules.eb.DoorModule import EbPointer, EbTextPointer, DoorType, SwitchDoor, NpcDoor, \
    EscalatorOrStairwayDoor, StairDirection, RopeOrLadderDoor, ClimbableType, Door, DestinationDirection, DoorModule
from coilsnake.data_blocks import Block, AllocatableBlock, Rom
from coilsnake.exceptions import InvalidArgumentError, MissingUserDataError, InvalidUserDataError
from coilsnake.modules.eb.exceptions import InvalidEbTextPointerError
from tests.coilsnake_test import CoilSnakeTestCase


class TestEbPointer(CoilSnakeTestCase):
    def setup(self):
        self.pointer = EbPointer()
        address_labels["a.b"] = 0x1314ab

    @raises(InvalidArgumentError)
    def test_zero_size(self):
        EbPointer(size=0)

    @raises(InvalidArgumentError)
    def test_negative_size(self):
        EbPointer(size=-1)

    def test_from_block(self):
        block = Block()
        block.from_list(range(0, 0x100))

        self.pointer.from_block(block, 0)
        assert_equal(self.pointer.address, 0x020100)
        self.pointer.from_block(block, 5)
        assert_equal(self.pointer.address, 0x070605)
        self.pointer.from_block(block, 0xfd)
        assert_equal(self.pointer.address, 0xfffefd)

    def test_to_block(self):
        block = Block()
        block.from_list(range(1, 6))

        self.pointer.address = 0xabcdef
        self.pointer.to_block(block, 1)
        assert_list_equal(block[0:5].to_list(), [1, 0xef, 0xcd, 0xab, 5])

    def test_from_yml_rep(self):
        self.pointer.from_yml_rep("$123456")
        assert_equal(self.pointer.address, 0x123456)
        self.pointer.from_yml_rep("a.b")
        assert_equal(self.pointer.address, 0x1314ab)

        assert_raises(MissingUserDataError, self.pointer.from_yml_rep, None)
        assert_raises(InvalidUserDataError, self.pointer.from_yml_rep, "")
        assert_raises(InvalidUserDataError, self.pointer.from_yml_rep, "$")
        assert_raises(InvalidUserDataError, self.pointer.from_yml_rep, "not.real_label")
        assert_raises(InvalidUserDataError, self.pointer.from_yml_rep, True)

    def test_str(self):
        self.pointer.address = 0xfe4392
        assert_equal(str(self.pointer), "$fe4392")


class TestEbTextPointer(CoilSnakeTestCase):
    def setup(self):
        self.pointer = EbTextPointer(size=4)

    def test_from_block(self):
        block = Block()
        block.from_list([0xc0, 0xc1, 0xc2, 0x00,
                         0xff, 0xff, 0xff, 0x00,
                         0xef, 0xfe, 0x02, 0x00,
                         0x01, 0x02, 0x03, 0x01])

        self.pointer.from_block(block, 0)
        assert_equal(self.pointer.address, 0xc2c1c0)
        self.pointer.from_block(block, 4)
        assert_equal(self.pointer.address, 0xffffff)

        assert_raises(InvalidEbTextPointerError, self.pointer.from_block, block, 8)
        assert_raises(InvalidEbTextPointerError, self.pointer.from_block, block, 12)

    def test_from_yml_rep(self):
        self.pointer.from_yml_rep("$c30201")
        assert_equal(self.pointer.address, 0xc30201)

        assert_raises(InvalidEbTextPointerError, self.pointer.from_yml_rep, "$070102")
        assert_raises(InvalidEbTextPointerError, self.pointer.from_yml_rep, "$1000000")


class GenericTestDoor(CoilSnakeTestCase):
    DOOR_TYPE = None
    DOOR_CLASS = None
    DOOR = None

    DOOR_OFFSET = 0x10
    NEW_DOOR_OFFSET = 0x123

    def setup(self):
        self.block = AllocatableBlock()
        self.block.from_list([0]*0x100000)
        self.block[self.DOOR_OFFSET:self.DOOR_OFFSET+5] = self.DOOR_DATA

    def teardown(self):
        del self.block

    def test_baseline(self):
        pass

    def test_from_block(self):
        new_door = self.DOOR_CLASS()
        new_door.from_block(self.block, self.DOOR_OFFSET)
        assert_equal(new_door, self.door)

    def test_to_block(self):
        self.door.write_to_block(self.block, self.NEW_DOOR_OFFSET, {})
        assert_list_equal(self.block[self.DOOR_OFFSET:self.DOOR_OFFSET+3].to_list(),
                          [self.door.y, self.door.x, self.DOOR_TYPE])

    def test_yml_rep(self):
        assert_dict_equal(self.door.yml_rep(), self.YML_REP)

    def test_from_yml_rep(self):
        new_door = self.DOOR_CLASS()
        new_door.from_yml_rep(self.YML_REP)
        assert_equal(new_door, self.door)


class TestEscalatorDoor(GenericTestDoor):
    DOOR_TYPE = DoorType.ESCALATOR
    DOOR_CLASS = EscalatorOrStairwayDoor

    DOOR_DATA = [123, 251, DoorType.ESCALATOR, 0x00, 0x03]
    YML_REP = { "Direction": "se",
                "Type": "escalator",
                "X": 251,
                "Y": 123}

    def setup(self):
        super(TestEscalatorDoor, self).setup()
        self.door = EscalatorOrStairwayDoor(x=251, y=123, type=self.DOOR_TYPE, direction=StairDirection.SE)


class TestStairwayDoor(GenericTestDoor):
    DOOR_TYPE = DoorType.STAIRWAY
    DOOR_CLASS = EscalatorOrStairwayDoor

    DOOR_DATA = [123, 251, DoorType.STAIRWAY, 0x00, 0x01]
    YML_REP = { "Direction": "ne",
                "Type": "stairway",
                "X": 251,
                "Y": 123}

    def setup(self):
        super(TestStairwayDoor, self).setup()
        self.door = EscalatorOrStairwayDoor(x=251, y=123, type=self.DOOR_TYPE, direction=StairDirection.NE)


class TestRopeDoor(GenericTestDoor):
    DOOR_TYPE = DoorType.ROPE_OR_LADDER
    DOOR_CLASS = RopeOrLadderDoor

    DOOR_DATA = [123, 251, DoorType.ROPE_OR_LADDER, 0x00, 0x80]
    YML_REP = { "Type": "rope",
                "X": 251,
                "Y": 123}

    def setup(self):
        super(TestRopeDoor, self).setup()
        self.door = RopeOrLadderDoor(x=251, y=123, climbable_type=ClimbableType.ROPE)


class TestLadderDoor(GenericTestDoor):
    DOOR_TYPE = DoorType.ROPE_OR_LADDER
    DOOR_CLASS = RopeOrLadderDoor

    DOOR_DATA = [169, 42, DoorType.ROPE_OR_LADDER, 0x00, 0x00]
    YML_REP = { "Type": "ladder",
                "X": 42,
                "Y": 169}

    def setup(self):
        super(TestLadderDoor, self).setup()
        self.door = RopeOrLadderDoor(x=42, y=169, climbable_type=ClimbableType.LADDER)


class GenericTestDestinationDoor(GenericTestDoor):
    DESTINATION_OFFSET = 0xF0AB0
    NEW_DESTINATION_OFFSET = 0x0F1BC0

    def setup(self):
        self.block = AllocatableBlock()
        self.block.from_list([0]*0x100000)
        self.block.deallocate((self.NEW_DESTINATION_OFFSET, 0x0F58EE))
        self.block[self.DOOR_OFFSET:self.DOOR_OFFSET+3] = self.DOOR_DATA
        self.block.write_multi(self.DOOR_OFFSET+3, self.DESTINATION_OFFSET & 0xffff, 2)
        self.block[self.DESTINATION_OFFSET:self.DESTINATION_OFFSET+len(self.DESTINATION_DATA)] = self.DESTINATION_DATA

    def test_to_block(self):
        super(GenericTestDestinationDoor, self).test_to_block()
        assert_equal(self.block.read_multi(self.NEW_DOOR_OFFSET+3, 2), self.NEW_DESTINATION_OFFSET & 0xffff)
        assert_list_equal(self.block[self.NEW_DESTINATION_OFFSET:(
            self.NEW_DESTINATION_OFFSET+len(self.DESTINATION_DATA))].to_list(),
                          self.DESTINATION_DATA)

    def test_to_block_reuse_destination(self):
        tmp_address_labels = dict()
        self.door.write_to_block(self.block, self.NEW_DOOR_OFFSET, tmp_address_labels)
        self.door.write_to_block(self.block, self.NEW_DOOR_OFFSET+5, tmp_address_labels)
        assert_list_equal(self.block[self.NEW_DOOR_OFFSET:self.NEW_DOOR_OFFSET+5].to_list(),
                     self.block[self.NEW_DOOR_OFFSET+5:self.NEW_DOOR_OFFSET+10].to_list())
        assert_equal(len(tmp_address_labels), 1)

    def test_to_block_dont_reuse_destination(self):
        tmp_address_labels = dict()
        self.door.write_to_block(self.block, self.NEW_DOOR_OFFSET, tmp_address_labels)
        # This works because every door with a destination has a text_pointer
        self.door.text_pointer.address += 1
        self.door.write_to_block(self.block, self.NEW_DOOR_OFFSET+5, tmp_address_labels)
        assert_list_equal(self.block[self.NEW_DOOR_OFFSET:self.NEW_DOOR_OFFSET+3].to_list(),
                          self.block[self.NEW_DOOR_OFFSET+5:self.NEW_DOOR_OFFSET+8].to_list())
        assert_not_equal(self.block[self.NEW_DOOR_OFFSET+3:self.NEW_DOOR_OFFSET+5].to_list(),
                         self.block[self.NEW_DOOR_OFFSET+8:self.NEW_DOOR_OFFSET+10].to_list())
        assert_equal(len(tmp_address_labels), 2)


class TestSwitchDoor(GenericTestDestinationDoor):
    DOOR_TYPE = DoorType.SWITCH
    DOOR_CLASS = SwitchDoor

    DOOR_DATA = [123, 251, DoorType.SWITCH]
    DESTINATION_DATA = [0x98, 0x80, 0x45, 0x32, 0xf1, 0x00]
    YML_REP = {
        "X": 251,
        "Y": 123,
        "Type": "switch",
        "Text Pointer": "$f13245",
        "Event Flag": 0x8098
    }

    def setup(self):
        super(TestSwitchDoor, self).setup()
        self.door = SwitchDoor(x=251, y=123, flag=0x8098, text_address=0x00f13245)


class TestPersonDoor(GenericTestDestinationDoor):
    DOOR_TYPE = DoorType.PERSON
    DOOR_CLASS = NpcDoor

    DOOR_DATA = [123, 251, DoorType.PERSON]
    DESTINATION_DATA = [0xa5, 0x92, 0xea, 0x00]
    YML_REP = {
        "X": 251,
        "Y": 123,
        "Type": "person",
        "Text Pointer": "$ea92a5",
    }

    def setup(self):
        super(TestPersonDoor, self).setup()
        self.door = NpcDoor(x=251, y=123, type=self.DOOR_TYPE, text_address=0x00ea92a5)


class TestObjectDoor(GenericTestDestinationDoor):
    DOOR_TYPE = DoorType.OBJECT
    DOOR_CLASS = NpcDoor

    DOOR_DATA = [123, 251, DoorType.OBJECT]
    DESTINATION_DATA = [0xa5, 0x82, 0xea, 0x00]
    YML_REP = {
        "X": 251,
        "Y": 123,
        "Type": "object",
        "Text Pointer": "$ea82a5",
    }

    def setup(self):
        super(TestObjectDoor, self).setup()
        self.door = NpcDoor(x=251, y=123, type=self.DOOR_TYPE, text_address=0x00ea82a5)

class TestDoor(GenericTestDestinationDoor):
    DOOR_TYPE = DoorType.DOOR
    DOOR_CLASS = Door

    DOOR_DATA = [111, 222, DoorType.DOOR]
    DESTINATION_DATA = [0xaf, 0x31, 0xc5, 0x0, # Text Pointer
                        0x31, 0x02, # Event Flag
                        0x13, 0x43, # Y & Direction
                        0x11, 0x07, # X
                        0x42] # Style
    YML_REP = {
        "X": 222,
        "Y": 111,
        "Type": "door",
        "Destination X": 0x711,
        "Destination Y": 0x313,
        "Direction": "up",
        "Event Flag": 0x231,
        "Style": 0x42,
        "Text Pointer": "$c531af"
    }

    def setup(self):
        super(TestDoor, self).setup()
        self.door = Door(x=222, y=111, text_address=0x00c531af, flag=0x231, destination_x=0x711,
                         destination_y=0x313, destination_direction=DestinationDirection.UP,
                         destination_style=0x42)

class TestDoorModule(CoilSnakeTestCase):
    def setup(self):
        self.setup_temporary_wo_file()
        self.module = DoorModule()

    def teardown(self):
        self.teardown_temporary_wo_file()
        del self.module

    @nottest
    def test_read_from_rom_using_rom(self, rom):
        self.module.read_from_rom(rom)

        # Very simple verification by checking the amount of different types of doors that were read
        assert_equal(len(self.module.door_areas), 40*32)
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
            rom.from_file(os.path.join(self.TEST_DATA_DIR, 'roms', 'true_EarthBound.smc'))
            self.test_read_from_rom_using_rom(rom)

    @nottest
    def test_read_from_project_using_filename(self, filename):
        with open(filename, 'r') as doors_file:
            def resource_open(a, b):
                return doors_file

            self.module.read_from_project(resource_open)

        # Very simple verification by checking the amount of different types of doors that were read
        assert_equal(len(self.module.door_areas), 40*32)
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

    def test_read_from_project(self):
        self.test_read_from_project_using_filename(os.path.join(self.TEST_DATA_DIR, 'true_map_doors.yml'))

    def test_write_to_project(self):
        with Rom() as rom:
            rom.from_file(os.path.join(self.TEST_DATA_DIR, 'roms', 'true_EarthBound.smc'))
            self.module.read_from_rom(rom)

        def resource_open(a, b):
            return self.temporary_wo_file
        self.module.write_to_project(resource_open)

        assert_true(os.path.isfile(self.temporary_wo_file_name))
        self.temporary_wo_file.close()
        self.test_read_from_project_using_filename(self.temporary_wo_file_name)

    def test_write_to_rom(self):
        with open(os.path.join(self.TEST_DATA_DIR, 'true_map_doors.yml'), 'r') as doors_file:
            def resource_open(a, b):
                return doors_file

            self.module.read_from_project(resource_open)

        with Rom() as rom:
            rom.from_file(os.path.join(self.TEST_DATA_DIR, 'roms', 'true_EarthBound.smc'))
            self.module.write_to_rom(rom)
            self.test_read_from_rom_using_rom(rom)