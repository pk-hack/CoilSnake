from coilsnake.model.eb.doors import door_from_block, door_from_yml_rep, not_in_destination_bank
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import convert_values_to_hex_repr, yml_load, yml_dump
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address

from collections import OrderedDict

def sort_yml_doors(arg): # Reorder dicts
    if isinstance(arg, list):
        return [sort_yml_doors(v) for v in arg]

    if isinstance(arg, dict):
        return OrderedDict((k, sort_yml_doors(arg[k])) for k in sorted(arg.keys()))

    return arg

class DoorModule(EbModule):
    NAME = "Doors"

    def __init__(self):
        super(EbModule, self).__init__()
        self.pointer_table = eb_table_from_offset(0xD00000)
        self.door_areas = []

    def read_from_rom(self, rom):
        self.pointer_table.from_block(rom, from_snes_address(0xD00000))
        self.door_areas = []
        for i in range(self.pointer_table.num_rows):
            offset = from_snes_address(self.pointer_table[i][0])
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

    def write_to_project(self, resourceOpener):
        out = dict()
        x = y = 0
        rowOut = dict()
        for entry in self.door_areas:
            if not entry:
                rowOut[x % 32] = None
            else:
                rowOut[x % 32] = [z.yml_rep() for z in entry]
            if (x % 32) == 31:
                # Start new row
                out[y] = rowOut
                x = 0
                y += 1
                rowOut = dict()
            else:
                x += 1

        with resourceOpener("map_doors", "yml", True) as f:
            s = yml_dump(
                out,
                default_flow_style=False)
            s = convert_values_to_hex_repr(yml_str_rep=s, key="Event Flag")
            f.write(s)

    def read_from_project(self, resourceOpener):
        self.door_areas = []
        with resourceOpener("map_doors", "yml", True) as f:
            input = sort_yml_doors(yml_load(f))
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

    def write_to_rom(self, rom):
        # Deallocate the range of the ROM in which we will write the door destinations.
        # We deallocate it here instead of specifying it in FREE_RANGES because we want to be sure that this module
        # get first dibs at writing to this range. This is because door destinations needs to be written to the 0x0F
        # bank of the EB ROM, and this is one of the few ranges available in that bank.
        rom.deallocate((0x0F0000, 0x0F58EE))
        destination_offsets = dict()
        empty_area_offset = from_snes_address(rom.allocate(data=[0, 0], can_write_to=not_in_destination_bank))
        i = 0
        for door_area in self.door_areas:
            if (door_area is None) or (not door_area):
                self.pointer_table[i] = [empty_area_offset]
            else:
                num_doors = len(door_area)
                area_offset = rom.allocate(size=(2 + num_doors * 5), can_write_to=not_in_destination_bank)
                self.pointer_table[i] = [to_snes_address(area_offset)]
                rom.write_multi(area_offset, num_doors, 2)
                area_offset += 2
                for door in door_area:
                    door.write_to_block(rom, area_offset, destination_offsets)
                    area_offset += 5
            i += 1
        self.pointer_table.to_block(rom, from_snes_address(0xD00000))
