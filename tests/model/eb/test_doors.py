from nose.tools import assert_equal, assert_list_equal, assert_dict_equal, assert_not_equal

from coilsnake.model.common.blocks import AllocatableBlock
from coilsnake.model.eb.doors import Door, DoorType, NpcDoor, DestinationDirection, EscalatorOrStairwayDoor, \
    StairDirection, RopeOrLadderDoor, ClimbableType, SwitchDoor
from tests.coilsnake_test import BaseTestCase


class GenericTestDoor(BaseTestCase):
    DOOR_TYPE = None
    DOOR_CLASS = None
    DOOR = None

    DOOR_OFFSET = 0x10
    NEW_DOOR_OFFSET = 0x123

    def setup(self):
        self.block = AllocatableBlock()
        self.block.from_list([0] * 0x100000)
        self.block[self.DOOR_OFFSET:self.DOOR_OFFSET + 5] = self.DOOR_DATA

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
        assert_list_equal(self.block[self.DOOR_OFFSET:self.DOOR_OFFSET + 3].to_list(),
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
    YML_REP = {"Direction": "se",
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
    YML_REP = {"Direction": "ne",
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
    YML_REP = {"Type": "rope",
               "X": 251,
               "Y": 123}

    def setup(self):
        super(TestRopeDoor, self).setup()
        self.door = RopeOrLadderDoor(x=251, y=123, climbable_type=ClimbableType.ROPE)


class TestLadderDoor(GenericTestDoor):
    DOOR_TYPE = DoorType.ROPE_OR_LADDER
    DOOR_CLASS = RopeOrLadderDoor

    DOOR_DATA = [169, 42, DoorType.ROPE_OR_LADDER, 0x00, 0x00]
    YML_REP = {"Type": "ladder",
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
        self.block.from_list([0] * 0x100000)
        self.block.deallocate((self.NEW_DESTINATION_OFFSET, 0x0F58EE))
        self.block[self.DOOR_OFFSET:self.DOOR_OFFSET + 3] = self.DOOR_DATA
        self.block.write_multi(self.DOOR_OFFSET + 3, self.DESTINATION_OFFSET & 0xffff, 2)
        self.block[self.DESTINATION_OFFSET:self.DESTINATION_OFFSET + len(self.DESTINATION_DATA)] = self.DESTINATION_DATA

    def test_to_block(self):
        super(GenericTestDestinationDoor, self).test_to_block()
        assert_equal(self.block.read_multi(self.NEW_DOOR_OFFSET + 3, 2), self.NEW_DESTINATION_OFFSET & 0xffff)
        assert_list_equal(self.block[self.NEW_DESTINATION_OFFSET:(
            self.NEW_DESTINATION_OFFSET + len(self.DESTINATION_DATA))].to_list(),
                          self.DESTINATION_DATA)

    def test_to_block_reuse_destination(self):
        tmp_address_labels = dict()
        self.door.write_to_block(self.block, self.NEW_DOOR_OFFSET, tmp_address_labels)
        self.door.write_to_block(self.block, self.NEW_DOOR_OFFSET + 5, tmp_address_labels)
        assert_list_equal(self.block[self.NEW_DOOR_OFFSET:self.NEW_DOOR_OFFSET + 5].to_list(),
                          self.block[self.NEW_DOOR_OFFSET + 5:self.NEW_DOOR_OFFSET + 10].to_list())
        assert_equal(len(tmp_address_labels), 1)

    def test_to_block_do_not_reuse_destination(self):
        tmp_address_labels = dict()
        self.door.write_to_block(self.block, self.NEW_DOOR_OFFSET, tmp_address_labels)
        # This works because every door with a destination has a text_pointer
        self.door.text_pointer.address += 1
        self.door.write_to_block(self.block, self.NEW_DOOR_OFFSET + 5, tmp_address_labels)
        assert_list_equal(self.block[self.NEW_DOOR_OFFSET:self.NEW_DOOR_OFFSET + 3].to_list(),
                          self.block[self.NEW_DOOR_OFFSET + 5:self.NEW_DOOR_OFFSET + 8].to_list())
        assert_not_equal(self.block[self.NEW_DOOR_OFFSET + 3:self.NEW_DOOR_OFFSET + 5].to_list(),
                         self.block[self.NEW_DOOR_OFFSET + 8:self.NEW_DOOR_OFFSET + 10].to_list())
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
    DESTINATION_DATA = [0xaf, 0x31, 0xc5, 0x0,  # Text Pointer
                        0x31, 0x02,  # Event Flag
                        0x13, 0x43,  # Y & Direction
                        0x11, 0x07,  # X
                        0x42]  # Style
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