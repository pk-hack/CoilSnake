from functools import partial

from coilsnake.model.common.table import LittleEndianIntegerTableEntry, RowTableEntry
from coilsnake.model.eb.table import EbPointerTableEntry
from coilsnake.util.eb.helper import is_in_bank


SpritePlacementTableEntry = RowTableEntry.from_schema(
    name="SpritePlacementTableEntry",
    schema=[type("NpcId", (LittleEndianIntegerTableEntry,), {"name": "NPC ID", "size": 2}),
            type("Y", (LittleEndianIntegerTableEntry,), {"name": "Y", "size": 1}),
            type("X", (LittleEndianIntegerTableEntry,), {"name": "X", "size": 1})]
)


class SpritePlacementPointerTableEntry(EbPointerTableEntry):
    name = "Sprite Placement Pointer Table Entry"
    size = 2

    @classmethod
    def from_block(cls, block, offset):
        area_offset = super(SpritePlacementPointerTableEntry, cls).from_block(block, offset)
        if not area_offset:
            return []
        area_offset |= 0x0F0000

        # Format: AA AA [BB BB YY XX]
        # AA = # of entries. BB = TPT. YY = y pos. XX = x pos.
        sprite_placements = []
        size = block.read_multi(area_offset, 2)
        for i in range(area_offset + 2, area_offset + 2 + (4 * size), 4):
            sprite_placements.append(SpritePlacementTableEntry.from_block(block, i))
        return sprite_placements

    @classmethod
    def to_block(cls, block, offset, value):
        if not value:
            super(SpritePlacementPointerTableEntry, cls).to_block(block, offset, 0)
        else:
            pointer = block.allocate(size=(2 + 4 * len(value)),
                                     can_write_to=partial(is_in_bank, 0x0f))
            super(SpritePlacementPointerTableEntry, cls).to_block(block, offset, pointer & 0xffff)

            block.write_multi(pointer, len(value), 2)
            pointer += 2
            for sprite_placement in value:
                SpritePlacementTableEntry.to_block(block, pointer, sprite_placement)
                pointer += 4

    @classmethod
    def to_yml_rep(cls, value):
        if not value:
            return None
        else:
            return [SpritePlacementTableEntry.to_yml_rep(entry) for entry in value]

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if not yml_rep:
            return []
        else:
            return [SpritePlacementTableEntry.from_yml_rep(entry) for entry in yml_rep]