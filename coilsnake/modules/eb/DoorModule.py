import yaml
from re import sub
import logging

from coilsnake.modules.eb.EbTablesModule import EbTable, PointerTableEntry
from coilsnake.modules.eb.EbDataBlocks import DataBlock
from coilsnake.modules.Table import ValuedIntTableEntry
from coilsnake.Progress import updateProgress
from coilsnake.modules.eb import EbModule
from coilsnake.modules.eb.exceptions import InvalidEbTextPointerError
from coilsnake.exceptions import InvalidArgumentError, InvalidUserDataError, MissingUserDataError
from coilsnake.data_blocks import Block
from coilsnake.util import get_from_user_dict, get_enum_from_user_dict, GenericEnum

# Enumeration types for door attributes:

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

# Classes to represent doors
class EbPointer(object):
    def __init__(self, size=3):
        self.size = 3

    def from_block(self, block, offset):
        self.address = block.read_multi(offset, self.size)

    def to_block(self, block, offset):
        block.write_multi(offset, self.address, self.size)

    def from_yml_rep(self, yml_rep):
        self.address = None

        if yml_rep is None:
            raise MissingUserDataError("Pointer was not specified")
        elif isinstance(yml_rep, str):
            try:
                if yml_rep[0] == '$':
                    self.address = int(yml_rep[1:], 16)
            except IndexError:
                raise InvalidUserDataError("Pointer \"%s\" was invalid" % yml_rep)

            if self.address is None:
                try:
                    self.address = EbModule.address_labels[yml_rep]
                except KeyError:
                    raise InvalidUserDataError("Invalid label \"%s\" provided for pointer" % yml_rep)
        else:
            raise InvalidUserDataError("Pointer \"%s\" was invalid" % yml_rep)

    def __str__(self):
        return "$%x" % self.address


class EbTextPointer(EbPointer):
    def from_block(self, block, offset):
        super(EbTextPointer, self).from_block(block, offset)

        if (self.address != 0) and ((self.address < 0xc00000) or (self.address > 0xffffff)):
            raise InvalidEbTextPointerError("Pointer had invalid address %#x" % self.address)

    def from_yml_rep(self, yml_rep):
        super(EbTextPointer, self).from_yml_rep(yml_rep)

        if (self.address != 0) and ((self.address < 0xc00000) or (self.address > 0xffffff)):
            raise InvalidEbTextPointerError("Pointer had invalid address %#x" % self.address)



def in_destination_bank(offset):
    return (offset >> 16) == 0x0f

def not_in_destination_bank(offset):
    return not in_destination_bank(offset)


class GenericDoor(object):
    def from_block(self, block, offset):
        self.y = block[offset]
        self.x = block[offset + 1]

    def write_to_block(self, block, offset, destination_locations):
        block[offset] = self.y
        block[offset+1] = self.x
        return 5

    def write_destination_to_block(self, block, offset, destination_block, destination_locations):
        destination_hash = hash(destination_block)

        if destination_hash in destination_locations:
            block.write_multi(offset + 3, destination_locations[destination_hash], 2)
        else:
            destination_offset = block.allocate(data=destination_block, can_write_to=in_destination_bank)
            destination_locations[destination_hash] = destination_offset & 0xffff
            block.write_multi(offset+3, destination_offset, 2)

    def yml_rep(self):
        return {"X": self.x, "Y": self.y}

    def from_yml_rep(self, yml_rep):
        self.x = get_from_user_dict(yml_rep, "X", int)
        self.y = get_from_user_dict(yml_rep, "Y", int)


class SwitchDoor(GenericDoor):
    def __init__(self):
        self.text_pointer = EbTextPointer(size=4)

    def from_block(self, block, offset):
        super(SwitchDoor, self).from_block(block, offset)
        destination_offset = block.read_multi(offset + 3, 2) | 0xF0000
        self.flag = block.read_multi(destination_offset, 2)
        self.text_pointer.from_block(block, destination_offset + 2)

    def write_to_block(self, block, offset, destination_locations):
        super(SwitchDoor, self).write_to_block(block, offset, destination_locations)
        block[offset+2] = DoorType.SWITCH

        with Block() as destination_block:
            destination_block.from_list([0] * 6)
            destination_block.write_multi(0, self.flag, 2)
            self.text_pointer.to_block(destination_block, 2)
            self.write_destination_to_block(block, offset, destination_block, destination_locations)

        return 5

    def yml_rep(self):
        out = super(SwitchDoor, self).yml_rep()
        out["Type"] = DoorType.tostring(DoorType.SWITCH)
        out["Event Flag"] = self.flag
        out["Text Pointer"] = str(self.text_pointer)
        return out

    def from_yml_rep(self, yml_rep):
        super(SwitchDoor, self).from_yml_rep(yml_rep)
        self.flag = get_from_user_dict(yml_rep, "Event Flag", int)
        self.text_pointer.from_yml_rep(get_from_user_dict(yml_rep, "Text Pointer", str))


class RopeOrLadderDoor(GenericDoor):
    def from_block(self, block, offset):
        super(RopeOrLadderDoor, self).from_block(block, offset)
        self.climbable_type = block.read_multi(offset + 3, 2)
        if not ClimbableType.is_valid(self.climbable_type):
            raise InvalidUserDataError("Door had invalid climbability setting of %#x" % self.climbable_type)

    def write_to_block(self, block, offset, destination_locations):
        super(RopeOrLadderDoor, self).write_to_block(block, offset, destination_locations)
        block[offset+2] = DoorType.ROPE_OR_LADDER
        block.write_multi(offset+3, self.climbable_type, 2)
        return 5

    def yml_rep(self):
        out = super(RopeOrLadderDoor, self).yml_rep()
        try:
            out["Type"] = ClimbableType.tostring(self.climbable_type)
        except InvalidArgumentError as e:
            raise InvalidUserDataError("Door had invalid climbability setting of %#x" % self.climbable_type)
        return out

    def from_yml_rep(self, yml_rep):
        super(RopeOrLadderDoor, self).from_yml_rep(yml_rep)
        self.climbable_type = get_enum_from_user_dict(yml_rep, "Type", ClimbableType)

class Door(GenericDoor):
    def __init__(self):
        self.text_pointer = EbTextPointer(size=4)

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
        block[offset+2] = DoorType.DOOR

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
        out["Text Pointer"] = str(self.text_pointer)
        out["Event Flag"] = self.flag
        out["Destination X"] = self.destination_x
        out["Destination Y"] = self.destination_y
        try:
            out["Direction"] = DestinationDirection.tostring(self.destination_direction)
        except InvalidArgumentError as e:
            raise InvalidUserDataError("Door had invalid destination direction of %#x" % self.destination_direction)
        out["Style"] = self.destination_style
        return out

    def from_yml_rep(self, yml_rep):
        out = super(Door, self).from_yml_rep(yml_rep)
        self.text_pointer.from_yml_rep(get_from_user_dict(yml_rep, "Text Pointer", str))
        self.flag = get_from_user_dict(yml_rep, "Event Flag", int)
        self.destination_x = get_from_user_dict(yml_rep, "Destination X", int)
        self.destination_y = get_from_user_dict(yml_rep, "Destination Y", int)
        self.destination_direction = get_enum_from_user_dict(yml_rep, "Direction", DestinationDirection)
        self.destination_style = get_from_user_dict(yml_rep, "Style", int)


class EscalatorOrStairwayDoor(GenericDoor):
    def from_block(self, block, offset):
        super(EscalatorOrStairwayDoor, self).from_block(block, offset)
        self.type = block[offset+2]
        if not DoorType.is_valid(self.type):
            raise InvalidUserDataError("Door had invalid type of %#x" % self.type)
        self.direction = block.read_multi(offset + 3, 2)
        if not StairDirection.is_valid(self.direction):
            raise InvalidUserDataError("Door had invalid escalator/stairs direction of %#x" % self.direction)

    def write_to_block(self, block, offset, destination_locations):
        super(EscalatorOrStairwayDoor, self).write_to_block(block, offset, destination_locations)
        block[offset+2] = self.type
        block.write_multi(offset+3, self.direction, 2)
        return 5

    def yml_rep(self):
        out = super(EscalatorOrStairwayDoor, self).yml_rep()
        try:
            out["Type"] = DoorType.tostring(self.type)
        except InvalidArgumentError as e:
            raise InvalidUserDataError("Door had invalid type of %#x" % self.type)
        try:
            out["Direction"] = StairDirection.tostring(self.direction)
        except InvalidArgumentError as e:
            raise InvalidUserDataError("Door had invalid escalator/stairs direction of %#x" % self.direction)
        return out

    def from_yml_rep(self, yml_rep):
        out = super(EscalatorOrStairwayDoor, self).from_yml_rep(yml_rep)
        self.type = get_enum_from_user_dict(yml_rep, "Type", DoorType)
        self.direction = get_enum_from_user_dict(yml_rep, "Direction", StairDirection)

class NpcDoor(GenericDoor):
    def __init__(self):
        self.text_pointer = EbTextPointer(size=4)

    def from_block(self, block, offset):
        super(NpcDoor, self).from_block(block, offset)
        self.type = block[offset+2]
        if not DoorType.is_valid(self.type):
            raise InvalidUserDataError("Door had invalid type of %#x" % self.type)
        destination_offset = block.read_multi(offset + 3, 2) | 0xF0000
        self.text_pointer.from_block(block, destination_offset)

    def write_to_block(self, block, offset, destination_locations):
        super(NpcDoor, self).write_to_block(block, offset, destination_locations)
        block[offset+2] = self.type

        with Block() as destination_block:
            destination_block.from_list([0] * 4)
            self.text_pointer.to_block(destination_block, 0)
            self.write_destination_to_block(block, offset, destination_block, destination_locations)

        return 5

    def yml_rep(self):
        out = super(NpcDoor, self).yml_rep()
        try:
            out["Type"] = DoorType.tostring(self.type)
        except InvalidArgumentError as e:
            raise InvalidUserDataError("Door had invalid type of %#x" % self.type)
        out["Text Pointer"] = str(self.text_pointer)
        return out

    def from_yml_rep(self, yml_rep):
        out = super(NpcDoor, self).from_yml_rep(yml_rep)
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
        door = DOOR_TYPE_ID_TO_CLASS_MAP[block[offset+2]]()
        door.from_block(block, offset)
        return door
    except IndexError:
        log.warning("Ignoring a door at %#x with an invalid type of %#x", offset, block[offset+2])
        return None
    except InvalidUserDataError as e:
        log.warning("Ignoring a door at %#x that contained invalid data: %s", offset, e.message)
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
        log.error(message)
        raise MissingUserDataError(message)

    try:
        door = DOOR_TYPE_NAME_TO_CLASS_MAP[door_type_yml_rep]()
    except KeyError:
        message = "Door had unknown \"Type\" of \"%s\"" % door_type_yml_rep
        log.error(message)
        raise InvalidUserDataError(message)

    door.from_yml_rep(yml_rep)
    return door


class DoorModule(EbModule.EbModule):
    NAME = "Doors"

    def __init__(self):
        EbModule.EbModule.__init__(self)
        self._ptrTbl = EbTable(0xD00000)
        self._entries = []

    def read_from_rom(self, rom):
        """
        @type rom: coilsnake.data_blocks.Rom
        """
        self._ptrTbl.readFromRom(rom)
        updateProgress(5)
        pct = 45.0 / (40 * 32)
        for i in range(self._ptrTbl.height()):
            offset = EbModule.toRegAddr(self._ptrTbl[i, 0].val())
            entry = []
            numDoors = rom.read_multi(offset, 2)
            offset += 2
            for j in range(numDoors):
                door = door_from_block(rom, offset)
                if door is None:
                    # If we've found an invalid door, stop reading from this door group.
                    # This is expected, since a clean ROM contains some invalid doors.
                    break
                entry.append(door)
                offset += 5
            self._entries.append(entry)
            i += 1
            updateProgress(pct)

    def write_to_project(self, resourceOpener):
        out = dict()
        x = y = 0
        rowOut = dict()
        pct = 45.0 / (40 * 32)
        for entry in self._entries:
            if not entry:
                rowOut[x % 32] = None
            else:
                rowOut[x % 32] = map(lambda z: z.yml_rep(), entry)
            if (x % 32) == 31:
                # Start new row
                out[y] = rowOut
                x = 0
                y += 1
                rowOut = dict()
            else:
                x += 1
            updateProgress(pct)
        with resourceOpener("map_doors", "yml") as f:
            s = yaml.dump(
                out,
                default_flow_style=False,
                Dumper=yaml.CSafeDumper)
            s = sub("Event Flag: (\d+)", lambda i: "Event Flag: " + hex(int(i.group(0)[12:])), s)
            f.write(s)
        updateProgress(5)

    def read_from_project(self, resourceOpener):
        self._entries = []
        pct = 45.0 / (40 * 32)
        with resourceOpener("map_doors", "yml") as f:
            updateProgress(5)
            input = yaml.load(f, Loader=yaml.CSafeLoader)
            for y in input:
                row = input[y]
                for x in row:
                    if row[x] is None:
                        self._entries.append(None)
                    else:
                        entry = []
                        for door in row[x]:
                            d = door_from_yml_rep(door)
                            entry.append(d)
                        self._entries.append(entry)
                    updateProgress(pct)

    def write_to_rom(self, rom):
        """
        @type rom: coilsnake.data_blocks.Rom
        """
        self._ptrTbl.clear(32 * 40)
        # Deallocate the range of the ROM in which we will write the door destinations.
        # We deallocate it here instead of specifying it in FREE_RANGES because we want to be sure that this module
        # get first dibs at writing to this range. This is because door destinations needs to be written to the 0x0F
        # bank of the EB ROM, and this is one of the few ranges available in that bank.
        rom.deallocate((0x0F0000, 0x0F58EE))
        destination_offsets = dict()
        empty_area_offset = EbModule.toSnesAddr(rom.allocate(data=[0, 0], can_write_to=not_in_destination_bank))
        pct = 45.0 / (40 * 32)
        i = 0
        for door_area in self._entries:
            if (door_area is None) or (not door_area):
                self._ptrTbl[i, 0].setVal(empty_area_offset)
            else:
                num_doors = len(door_area)
                area_offset = rom.allocate(size=(2 + num_doors * 5), can_write_to=not_in_destination_bank)
                self._ptrTbl[i, 0].setVal(EbModule.toSnesAddr(area_offset))
                rom.write_multi(area_offset, num_doors, 2)
                area_offset += 2
                for door in door_area:
                    door.write_to_block(rom, area_offset, destination_offsets)
                    area_offset += 5
            i += 1
            updateProgress(pct)
        self._ptrTbl.writeToRom(rom)
        updateProgress(5)
