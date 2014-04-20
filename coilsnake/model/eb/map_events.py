from functools import partial

from coilsnake.model.common.table import RowTableEntry, LittleEndianIntegerTableEntry
from coilsnake.model.eb.table import EbPointerTableEntry, EbEventFlagTableEntry
from coilsnake.util.eb.helper import is_in_bank


MapEventSubTableEntry = RowTableEntry.from_schema(
    name="Map Event Sub Table Entry",
    schema=[type("Before", (LittleEndianIntegerTableEntry,), {"name": "Before", "size": 2}),
            type("After", (LittleEndianIntegerTableEntry,), {"name": "After", "size": 2})]
)


class MapEventPointerTableEntry(EbPointerTableEntry):
    name = "Map Event Pointer Table Entry"
    size = 2

    @classmethod
    def from_block(cls, block, offset):
        data_offset = super(MapEventPointerTableEntry, cls).from_block(block, offset)
        data_offset |= (cls.bank << 16)

        value = []
        while block.read_multi(data_offset, 2) != 0:
            flag = EbEventFlagTableEntry.from_block(block, data_offset)
            data_offset += EbEventFlagTableEntry.size
            num_sub_entries = block.read_multi(data_offset, 2)
            data_offset += 2

            sub_entries = [MapEventSubTableEntry.from_block(block, x)
                           for x
                           in range(data_offset,
                                    data_offset + num_sub_entries * MapEventSubTableEntry.size,
                                    MapEventSubTableEntry.size)]
            data_offset += num_sub_entries * MapEventSubTableEntry.size
            value.append((flag, sub_entries))

        return value

    @classmethod
    def to_block(cls, block, offset, value):
        data_size = 2  # for the final [00 00] bytes which end each entry
        for _, sub_entries in value:
            data_size += EbEventFlagTableEntry.size
            data_size += 2
            data_size += MapEventSubTableEntry.size * len(sub_entries)
        pointer = block.allocate(size=data_size,
                                 can_write_to=partial(is_in_bank, cls.bank))
        super(MapEventPointerTableEntry, cls).to_block(block, offset, pointer & 0xffff)

        for flag, sub_entries in value:
            EbEventFlagTableEntry.to_block(block, pointer, flag)
            pointer += EbEventFlagTableEntry.size
            block.write_multi(pointer, len(sub_entries), 2)
            pointer += 2

            for sub_entry in sub_entries:
                MapEventSubTableEntry.to_block(block, pointer, sub_entry)
                pointer += MapEventSubTableEntry.size

        block[pointer] = 0
        block[pointer + 1] = 0

    @classmethod
    def to_yml_rep(cls, value):
        return [{EbEventFlagTableEntry.name: EbEventFlagTableEntry.to_yml_rep(flag),
                 "Tile Changes": [MapEventSubTableEntry.to_yml_rep(tile_change)
                                  for tile_change in tile_changes]}
                for flag, tile_changes in value]

    @classmethod
    def from_yml_rep(cls, yml_rep):
        return [(EbEventFlagTableEntry.from_yml_rep(entry_yml_rep[EbEventFlagTableEntry.name]),
                 [MapEventSubTableEntry.from_yml_rep(tile_change)
                  for tile_change in entry_yml_rep["Tile Changes"]])
                for entry_yml_rep in yml_rep]

    @classmethod
    def yml_rep_hex_labels(cls):
        return EbEventFlagTableEntry.yml_rep_hex_labels()