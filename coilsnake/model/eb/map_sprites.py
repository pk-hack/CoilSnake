from functools import partial

from coilsnake.model.eb.table import EbPointerTableEntry
from coilsnake.util.eb.helper import is_in_bank


class SpritePlacement(object):
    def from_block(self, block, offset):
        self.npc_id = block.read_multi(offset, 2)
        self.y = block[offset + 2]
        self.x = block[offset + 3]

    def to_block(self, block, offset):
        block.write_multi(offset, self.npc_id, 2)
        block[offset + 2] = self.y
        block[offset + 3] = self.x

    def yml_rep(self):
        return {"NPC ID": self.npc_id,
                "X": self.x,
                "Y": self.y}

    def from_yml_rep(self, yml_rep):
        self.npc_id = yml_rep["NPC ID"]
        self.x = yml_rep["X"]
        self.y = yml_rep["Y"]


class SpritePlacementTableEntry(EbPointerTableEntry):
    name = "Sprite Placement Table Entry"
    size = 2

    @classmethod
    def from_block(cls, block, offset):
        area_offset = super(SpritePlacementTableEntry, cls).from_block(block, offset)
        if not area_offset:
            return []
        area_offset |= 0x0F0000

        # Format: AA AA [BB BB YY XX]
        # AA = # of entries. BB = TPT. YY = y pos. XX = x pos.
        sprite_placements = []
        size = block.read_multi(area_offset, 2)
        for i in range(area_offset + 2, area_offset + 2 + (4 * size), 4):
            sprite_placement = SpritePlacement()
            sprite_placement.from_block(block, i)
            sprite_placements.append(sprite_placement)
        return sprite_placements

    @classmethod
    def to_block(cls, block, offset, value):
        if not value:
            super(SpritePlacementTableEntry, cls).to_block(block, offset, 0)
        else:
            pointer = block.allocate(size=(2 + 4 * len(value)),
                                     can_write_to=partial(is_in_bank, 0x0f))
            super(SpritePlacementTableEntry, cls).to_block(block, offset, pointer & 0xffff)

            block.write_multi(pointer, len(value), 2)
            pointer += 2
            for sprite_placement in value:
                sprite_placement.to_block(block, pointer)
                pointer += 4

    @classmethod
    def to_yml_rep(cls, value):
        if not value:
            return None
        else:
            return map(lambda x: x.yml_rep(), value)

    @classmethod
    def from_yml_rep(cls, yml_rep):
        if not yml_rep:
            return []
        else:
            sprite_placements = []
            for entry in yml_rep:
                sprite_placement = SpritePlacement()
                sprite_placement.from_yml_rep(entry)
                sprite_placements.append(sprite_placement)
            return sprite_placements