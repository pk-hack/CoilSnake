from coilsnake.model.common.table import RowTableEntry, LittleEndianIntegerTableEntry, \
    EnumeratedLittleEndianIntegerTableEntry
from coilsnake.model.eb.table import EbPointerTableEntry, EbEventFlagTableEntry
from coilsnake.util.common.type import GenericEnum
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address


TOWN_MAP_NAMES = ["Onett", "Twoson", "Threed", "Fourside", "Scaraba", "Summers"]

TownMapEnum = GenericEnum.create("TownMapEnum", TOWN_MAP_NAMES)

TOWN_MAP_ICON_NAMES = ["Nothing", "Hamburger Shop", "Bakery", "Hotel", "Restaurant", "Hospital", "Shop",
                       "Dept Store", "Bus Stop", "South to Twoson", "North to Onett", "South to Threed",
                       "West to Twoson", "East to Desert", "West to Desert", "East to Toto", "Hint", "Ness",
                       "Small Ness", "North", "South", "West", "East"]

TownMapIconEnum = GenericEnum.create("TownMapIconEnum", TOWN_MAP_ICON_NAMES)

TownMapIconPlacementTableEntry = RowTableEntry.from_schema(
    name="Town Map Icon Placement Table Entry",
    schema=[type("TownMapIconX", (LittleEndianIntegerTableEntry,), {"name": "X", "size": 1}),
            type("TownMapIconY", (LittleEndianIntegerTableEntry,), {"name": "Y", "size": 1}),
            type("TownMapIconIcon", (EnumeratedLittleEndianIntegerTableEntry,), {
                "name": "Icon", "size": 1, "enumeration_class": TownMapIconEnum}),
            EbEventFlagTableEntry]
)


class TownMapIconPlacementPointerTableEntry(EbPointerTableEntry):
    name = "Town Map Icon Pointer Placement Table Entry"
    size = 4
    table_entry_class = TownMapIconPlacementTableEntry

    @classmethod
    def from_block(cls, block, offset):
        data_offset = from_snes_address(super(TownMapIconPlacementPointerTableEntry, cls).from_block(block, offset))
        if not data_offset:
            return []

        value = []
        while block[data_offset] != 0xff:
            value.append(cls.table_entry_class.from_block(block, data_offset))
            data_offset += cls.table_entry_class.size
        return value

    @classmethod
    def to_block(cls, block, offset, value):
        if not value:
            super(TownMapIconPlacementPointerTableEntry, cls).to_block(block, offset, 0)
        else:
            pointer = block.allocate(size=sum([cls.table_entry_class.size for x in value]) + 1)
            super(TownMapIconPlacementPointerTableEntry, cls).to_block(block, offset, to_snes_address(pointer))

            for icon_placement in value:
                cls.table_entry_class.to_block(block, pointer, icon_placement)
                pointer += cls.table_entry_class.size
            block[pointer] = 0xff

    @classmethod
    def to_yml_rep(cls, value):
        return [cls.table_entry_class.to_yml_rep(icon_placement) for icon_placement in value]

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if not yml_rep:
            return []
        else:
            return [cls.table_entry_class.from_yml_rep(icon_yml_rep) for icon_yml_rep in yml_rep]

    @classmethod
    def yml_rep_hex_labels(cls):
        return cls.table_entry_class.yml_rep_hex_labels()