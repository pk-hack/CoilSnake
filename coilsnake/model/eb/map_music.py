from coilsnake.model.common.table import TableEntry, LittleEndianIntegerTableEntry, RowTableEntry
from coilsnake.model.eb.table import EbEventFlagTableEntry


MapMusicSubTableEntry = RowTableEntry.from_schema(
    name="Map Music Sub Table Entry",
    schema=[EbEventFlagTableEntry,
            type("Music", (LittleEndianIntegerTableEntry,), {"name": "Music", "size": 2})]
)


class MapMusicTableEntry(TableEntry):
    name = "Map Music Table Entry"

    @classmethod
    def from_block(cls, block, offset):
        subentries = []
        while True:
            subentry = MapMusicSubTableEntry.from_block(block, offset)
            subentries.append(subentry)
            offset += MapMusicSubTableEntry.size
            if subentry[0] == 0:
                break
        return subentries

    @classmethod
    def to_block_size(cls, value):
        return MapMusicSubTableEntry.size * len(value)

    @classmethod
    def to_block(cls, block, offset, value):
        for subentry in value:
            MapMusicSubTableEntry.to_block(block, offset, subentry)
            offset += MapMusicSubTableEntry.size

    @classmethod
    def to_yml_rep(cls, value):
        return [MapMusicSubTableEntry.to_yml_rep(subentry) for subentry in value]

    @classmethod
    def from_yml_rep(cls, yml_rep):
        return [MapMusicSubTableEntry.from_yml_rep(subentry) for subentry in yml_rep]

    @classmethod
    def yml_rep_hex_labels(cls):
        return MapMusicSubTableEntry.yml_rep_hex_labels()