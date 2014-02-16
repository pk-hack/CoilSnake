import yaml
from re import sub
import logging

from coilsnake.model.eb.doors import door_from_block, door_from_yml_rep, not_in_destination_bank
from coilsnake.modules.eb.EbTablesModule import EbTable
from coilsnake.Progress import updateProgress
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address


log = logging.getLogger(__name__)


class DoorModule(EbModule):
    NAME = "Doors"

    def __init__(self):
        super(EbModule, self).__init__()
        self.pointer_table = EbTable(0xD00000)
        self.door_areas = []

    def read_from_rom(self, rom):
        self.pointer_table.readFromRom(rom)
        updateProgress(5)
        pct = 45.0 / (40 * 32)
        self.door_areas = []
        for i in range(self.pointer_table.height()):
            offset = from_snes_address(self.pointer_table[i, 0].val())
            door_area = []
            num_doors = rom.read_multi(offset, 2)
            offset += 2
            for j in range(num_doors):
                door = door_from_block(rom, offset)
                if door is None:
                    # If we've found an invalid door, stop reading from this door group.
                    # This is expected, since a clean ROM contains some invalid doors.
                    break
                door_area.append(door)
                offset += 5
            self.door_areas.append(door_area)
            i += 1
            updateProgress(pct)

    def write_to_project(self, resourceOpener):
        out = dict()
        x = y = 0
        rowOut = dict()
        pct = 45.0 / (40 * 32)
        for entry in self.door_areas:
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
        self.door_areas = []
        pct = 45.0 / (40 * 32)
        self.door_areas = []
        with resourceOpener("map_doors", "yml") as f:
            updateProgress(5)
            input = yaml.load(f, Loader=yaml.CSafeLoader)
            for y in input:
                row = input[y]
                for x in row:
                    if row[x] is None:
                        self.door_areas.append(None)
                    else:
                        entry = []
                        for door in row[x]:
                            d = door_from_yml_rep(door)
                            entry.append(d)
                        self.door_areas.append(entry)
                    updateProgress(pct)

    def write_to_rom(self, rom):
        self.pointer_table.clear(32 * 40)
        # Deallocate the range of the ROM in which we will write the door destinations.
        # We deallocate it here instead of specifying it in FREE_RANGES because we want to be sure that this module
        # get first dibs at writing to this range. This is because door destinations needs to be written to the 0x0F
        # bank of the EB ROM, and this is one of the few ranges available in that bank.
        rom.deallocate((0x0F0000, 0x0F58EE))
        destination_offsets = dict()
        empty_area_offset = from_snes_address(rom.allocate(data=[0, 0], can_write_to=not_in_destination_bank))
        pct = 45.0 / (40 * 32)
        i = 0
        for door_area in self.door_areas:
            if (door_area is None) or (not door_area):
                self.pointer_table[i, 0].setVal(empty_area_offset)
            else:
                num_doors = len(door_area)
                area_offset = rom.allocate(size=(2 + num_doors * 5), can_write_to=not_in_destination_bank)
                self.pointer_table[i, 0].setVal(to_snes_address(area_offset))
                rom.write_multi(area_offset, num_doors, 2)
                area_offset += 2
                for door in door_area:
                    door.write_to_block(rom, area_offset, destination_offsets)
                    area_offset += 5
            i += 1
            updateProgress(pct)
        self.pointer_table.writeToRom(rom)
        updateProgress(5)
