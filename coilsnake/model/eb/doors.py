import logging

from coilsnake.exceptions.common.exceptions import InvalidUserDataError, InvalidArgumentError, MissingUserDataError
from coilsnake.model.common.blocks import Block
from coilsnake.model.eb.pointers import EbTextPointer
from coilsnake.model.eb.table import EbEventFlagTableEntry
from coilsnake.util.common.helper import get_from_user_dict, get_enum_from_user_dict
from coilsnake.util.common.type import GenericEnum, StringRepresentationMixin, EqualityMixin


log = logging.getLogger(__name__)


class DoorType(GenericEnum):
    SWITCH, ROPE_OR_LADDER, DOOR, ESCALATOR, STAIRWAY, OBJECT, PERSON = range(7)


class StairDirection(GenericEnum):
    NW, NE, SW, SE = range(0, 0x400, 0x100)
    NOWHERE = 0x8000


class ClimbableType(GenericEnum):
    LADDER = 0
    ROPE = 0x8000


class DestinationDirection(GenericEnum):
    DOWN, UP, RIGHT, LEFT = range(4)


def in_destination_bank(offset):
    return (offset >> 16) == 0x0f


def not_in_destination_bank(offset):
    return not in_destination_bank(offset)


class GenericDoor(EqualityMixin, StringRepresentationMixin):
    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y

    def from_block(self, block, offset):
        self.y = block[offset]
        self.x = block[offset + 1]

    def write_to_block(self, block, offset, destination_locations):
        block[offset] = self.y
        block[offset + 1] = self.x
        return 5

    def write_destination_to_block(self, block, offset, destination_block, destination_locations):
        if destination_block in destination_locations:
            block.write_multi(offset + 3, destination_locations[destination_block], 2)
        else:
            destination_offset = block.allocate(data=destination_block, can_write_to=in_destination_bank)
            destination_locations[destination_block] = destination_offset & 0xffff
            block.write_multi(offset + 3, destination_offset, 2)

    def yml_rep(self):
        return {"X": self.x, "Y": self.y}

    def from_yml_rep(self, yml_rep):
        self.x = get_from_user_dict(yml_rep, "X", int)
        self.y = get_from_user_dict(yml_rep, "Y", int)


class SwitchDoor(GenericDoor):
    def __init__(self, x=None, y=None, flag=None, text_address=None):
        super(SwitchDoor, self).__init__(x, y)
        self.flag = flag
        if text_address is not None:
            self.text_pointer = EbTextPointer(address=text_address, size=4)
        else:
            self.text_pointer = EbTextPointer(size=4)

    def from_block(self, block, offset):
        super(SwitchDoor, self).from_block(block, offset)
        destination_offset = block.read_multi(offset + 3, 2) | 0xF0000
        self.flag = block.read_multi(destination_offset, 2)
        self.text_pointer.from_block(block, destination_offset + 2)

    def write_to_block(self, block, offset, destination_locations):
        super(SwitchDoor, self).write_to_block(block, offset, destination_locations)
        block[offset + 2] = DoorType.SWITCH

        with Block() as destination_block:
            destination_block.from_list([0] * 6)
            destination_block.write_multi(0, self.flag, 2)
            self.text_pointer.to_block(destination_block, 2)
            self.write_destination_to_block(block, offset, destination_block, destination_locations)

        return 5

    def yml_rep(self):
        out = super(SwitchDoor, self).yml_rep()
        out["Type"] = DoorType.tostring(DoorType.SWITCH)
        out["Event Flag"] = EbEventFlagTableEntry.to_yml_rep(self.flag)
        out["Text Pointer"] = self.text_pointer.yml_rep()
        return out

    def from_yml_rep(self, yml_rep):
        super(SwitchDoor, self).from_yml_rep(yml_rep)
        self.flag = EbEventFlagTableEntry.from_yml_rep(get_from_user_dict(yml_rep, "Event Flag", int))
        self.text_pointer.from_yml_rep(get_from_user_dict(yml_rep, "Text Pointer", str))


class RopeOrLadderDoor(GenericDoor):
    def __init__(self, x=None, y=None, climbable_type=ClimbableType.ROPE):
        super(RopeOrLadderDoor, self).__init__(x, y)
        self.climbable_type = climbable_type

    def from_block(self, block, offset):
        super(RopeOrLadderDoor, self).from_block(block, offset)
        self.climbable_type = block.read_multi(offset + 3, 2)
        if not ClimbableType.is_valid(self.climbable_type):
            raise InvalidUserDataError("Door had invalid climbability setting of %#x" % self.climbable_type)

    def write_to_block(self, block, offset, destination_locations):
        super(RopeOrLadderDoor, self).write_to_block(block, offset, destination_locations)
        block[offset + 2] = DoorType.ROPE_OR_LADDER
        block.write_multi(offset + 3, self.climbable_type, 2)
        return 5

    def yml_rep(self):
        out = super(RopeOrLadderDoor, self).yml_rep()
        try:
            out["Type"] = ClimbableType.tostring(self.climbable_type)
        except InvalidArgumentError:
            raise InvalidUserDataError("Door had invalid climbability setting of %#x" % self.climbable_type)
        return out

    def from_yml_rep(self, yml_rep):
        super(RopeOrLadderDoor, self).from_yml_rep(yml_rep)
        self.climbable_type = get_enum_from_user_dict(yml_rep, "Type", ClimbableType)


class Door(GenericDoor):
    def __init__(self, x=None, y=None, text_address=None, flag=None, destination_x=None, destination_y=None,
                 destination_direction=DestinationDirection.DOWN, destination_style=None):
        super(Door, self).__init__(x, y)
        if text_address is not None:
            self.text_pointer = EbTextPointer(address=text_address, size=4)
        else:
            self.text_pointer = EbTextPointer(size=4)
        self.flag = flag
        self.destination_x = destination_x
        self.destination_y = destination_y
        self.destination_direction = destination_direction
        self.destination_style = destination_style

    def from_block(self, block, offset):
        super(Door, self).from_block(block, offset)
        destination_offset = block.read_multi(offset + 3, 2) | 0xF0000
        self.text_pointer.from_block(block, destination_offset)
        self.flag = block.read_multi(destination_offset + 4, 2)
        self.destination_y = block[destination_offset + 6]
        self.destination_y |= (block[destination_offset + 7] & 0x3f) << 8
        self.destination_direction = (block[destination_offset + 7] & 0xc0) >> 6
        if not DestinationDirection.is_valid(self.destination_direction):
            raise InvalidUserDataError("Door had invalid destination direction of %#x" % self.destination_direction)
        self.destination_x = block.read_multi(destination_offset + 8, 2)
        self.destination_style = block[destination_offset + 10]

    def write_to_block(self, block, offset, destination_locations):
        super(Door, self).write_to_block(block, offset, destination_locations)
        block[offset + 2] = DoorType.DOOR

        with Block() as destination_block:
            destination_block.from_list([0] * 11)
            self.text_pointer.to_block(destination_block, 0)
            destination_block.write_multi(4, self.flag, 2)
            destination_block[6] = self.destination_y & 0xff
            destination_block[7] = (self.destination_y >> 8) | (self.destination_direction << 6)
            destination_block.write_multi(8, self.destination_x, 2)
            destination_block[10] = self.destination_style
            self.write_destination_to_block(block, offset, destination_block, destination_locations)

        return 5

    def yml_rep(self):
        out = super(Door, self).yml_rep()
        out["Type"] = DoorType.tostring(DoorType.DOOR)
        out["Text Pointer"] = self.text_pointer.yml_rep()
        out["Event Flag"] = EbEventFlagTableEntry.to_yml_rep(self.flag)
        out["Destination X"] = self.destination_x
        out["Destination Y"] = self.destination_y
        try:
            out["Direction"] = DestinationDirection.tostring(self.destination_direction)
        except InvalidArgumentError:
            raise InvalidUserDataError("Door had invalid destination direction of %#x" % self.destination_direction)
        out["Style"] = self.destination_style
        return out

    def from_yml_rep(self, yml_rep):
        super(Door, self).from_yml_rep(yml_rep)
        self.text_pointer.from_yml_rep(get_from_user_dict(yml_rep, "Text Pointer", str))
        self.flag = EbEventFlagTableEntry.from_yml_rep(get_from_user_dict(yml_rep, "Event Flag", int))
        self.destination_x = get_from_user_dict(yml_rep, "Destination X", int)
        self.destination_y = get_from_user_dict(yml_rep, "Destination Y", int)
        self.destination_direction = get_enum_from_user_dict(yml_rep, "Direction", DestinationDirection)
        self.destination_style = get_from_user_dict(yml_rep, "Style", int)


class EscalatorOrStairwayDoor(GenericDoor):
    def __init__(self, x=None, y=None, type=DoorType.ESCALATOR, direction=StairDirection.NOWHERE):
        super(EscalatorOrStairwayDoor, self).__init__(x, y)
        self.type = type
        self.direction = direction

    def from_block(self, block, offset):
        super(EscalatorOrStairwayDoor, self).from_block(block, offset)
        self.type = block[offset + 2]
        if not DoorType.is_valid(self.type):
            raise InvalidUserDataError("Door had invalid type of %#x" % self.type)
        self.direction = block.read_multi(offset + 3, 2)
        if not StairDirection.is_valid(self.direction):
            raise InvalidUserDataError("Door had invalid escalator/stairs direction of %#x" % self.direction)

    def write_to_block(self, block, offset, destination_locations):
        super(EscalatorOrStairwayDoor, self).write_to_block(block, offset, destination_locations)
        block[offset + 2] = self.type
        block.write_multi(offset + 3, self.direction, 2)
        return 5

    def yml_rep(self):
        out = super(EscalatorOrStairwayDoor, self).yml_rep()
        try:
            out["Type"] = DoorType.tostring(self.type)
        except InvalidArgumentError:
            raise InvalidUserDataError("Door had invalid type of %#x" % self.type)
        try:
            out["Direction"] = StairDirection.tostring(self.direction)
        except InvalidArgumentError:
            raise InvalidUserDataError("Door had invalid escalator/stairs direction of %#x" % self.direction)
        return out

    def from_yml_rep(self, yml_rep):
        super(EscalatorOrStairwayDoor, self).from_yml_rep(yml_rep)
        self.type = get_enum_from_user_dict(yml_rep, "Type", DoorType)
        self.direction = get_enum_from_user_dict(yml_rep, "Direction", StairDirection)


class NpcDoor(GenericDoor):
    def __init__(self, x=None, y=None, type=DoorType.PERSON, text_address=None):
        super(NpcDoor, self).__init__(x, y)
        self.type = type
        if text_address is None:
            self.text_pointer = EbTextPointer(size=4)
        else:
            self.text_pointer = EbTextPointer(size=4, address=text_address)

    def from_block(self, block, offset):
        super(NpcDoor, self).from_block(block, offset)
        self.type = block[offset + 2]
        if not DoorType.is_valid(self.type):
            raise InvalidUserDataError("Door had invalid type of %#x" % self.type)
        destination_offset = block.read_multi(offset + 3, 2) | 0xF0000
        self.text_pointer.from_block(block, destination_offset)

    def write_to_block(self, block, offset, destination_locations):
        super(NpcDoor, self).write_to_block(block, offset, destination_locations)
        block[offset + 2] = self.type

        with Block() as destination_block:
            destination_block.from_list([0] * 4)
            self.text_pointer.to_block(destination_block, 0)
            self.write_destination_to_block(block, offset, destination_block, destination_locations)

        return 5

    def yml_rep(self):
        out = super(NpcDoor, self).yml_rep()
        try:
            out["Type"] = DoorType.tostring(self.type)
        except InvalidArgumentError:
            raise InvalidUserDataError("Door had invalid type of %#x" % self.type)
        out["Text Pointer"] = self.text_pointer.yml_rep()
        return out

    def from_yml_rep(self, yml_rep):
        super(NpcDoor, self).from_yml_rep(yml_rep)
        self.type = get_enum_from_user_dict(yml_rep, "Type", DoorType)
        self.text_pointer.from_yml_rep(get_from_user_dict(yml_rep, "Text Pointer", str))


# Mapping from type number to class
DOOR_TYPE_ID_TO_CLASS_MAP = [
    SwitchDoor,
    RopeOrLadderDoor,
    Door,
    EscalatorOrStairwayDoor,
    EscalatorOrStairwayDoor,
    NpcDoor,
    NpcDoor
]


def door_from_block(block, offset):
    try:
        door = DOOR_TYPE_ID_TO_CLASS_MAP[block[offset + 2]]()
        door.from_block(block, offset)
        return door
    except IndexError:
        log.debug("Ignoring a door at {:#x} with an invalid type of {:#x}".format(offset, block[offset + 2]))
        return None
    except InvalidUserDataError as e:
        log.debug("Ignoring a door at {:#x} that contained invalid data: {}".format(offset, e.message))
        return None


DOOR_TYPE_NAME_TO_CLASS_MAP = {
    DoorType.tostring(DoorType.SWITCH): SwitchDoor,
    ClimbableType.tostring(ClimbableType.ROPE): RopeOrLadderDoor,
    ClimbableType.tostring(ClimbableType.LADDER): RopeOrLadderDoor,
    DoorType.tostring(DoorType.DOOR): Door,
    DoorType.tostring(DoorType.ESCALATOR): EscalatorOrStairwayDoor,
    DoorType.tostring(DoorType.STAIRWAY): EscalatorOrStairwayDoor,
    DoorType.tostring(DoorType.PERSON): NpcDoor,
    DoorType.tostring(DoorType.OBJECT): NpcDoor
}


def door_from_yml_rep(yml_rep):
    try:
        door_type_yml_rep = yml_rep["Type"]
    except KeyError:
        message = "Door was missing \"Type\" attribute"
        raise MissingUserDataError(message)

    try:
        door = DOOR_TYPE_NAME_TO_CLASS_MAP[door_type_yml_rep]()
    except KeyError:
        message = "Door had unknown \"Type\" of \"%s\"" % door_type_yml_rep
        raise InvalidUserDataError(message)

    door.from_yml_rep(yml_rep)
    return door