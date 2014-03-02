from coilsnake.model.common.table_new import LittleEndianHexIntegerTableEntry, LittleEndianIntegerTableEntry, \
    RowTableEntry
from coilsnake.model.eb.table import EbPointerTableEntry
from coilsnake.util.eb.pointer import from_snes_address, to_snes_address


MapEnemyGroupTableEntry = RowTableEntry.from_schema(
    name="Map Enemy Group Table Entry",
    schema=[type("EventFlag", (LittleEndianHexIntegerTableEntry,), {"name": "Event Flag", "size": 2}),
            type("Rate1", (LittleEndianIntegerTableEntry,), {"name": "Sub-Group 1 Rate", "size": 1}),
            type("Rate2", (LittleEndianIntegerTableEntry,), {"name": "Sub-Group 2 Rate", "size": 1})]
)

MapEnemySubGroupTableEntry = RowTableEntry.from_schema(
    name="Map Enemy Sub-Group Table Entry",
    schema=[type("Probability", (LittleEndianIntegerTableEntry,), {"name": "Probability", "size": 1}),
            type("EnemyGroup", (LittleEndianIntegerTableEntry,), {"name": "Enemy Group", "size": 2})]
)


class MapEnemyGroupPointerTableEntry(EbPointerTableEntry):
    name = "Map Enemy Group Pointer Table Entry"
    size = 4

    @classmethod
    def from_block(cls, block, offset):
        group_offset = from_snes_address(super(MapEnemyGroupPointerTableEntry, cls).from_block(block, offset))
        group_value = MapEnemyGroupTableEntry.from_block(block, group_offset)
        group_offset += MapEnemyGroupTableEntry.size

        subgroup_1 = []
        if group_value[1] > 0:
            subgroup_rate = 0
            while subgroup_rate < 8:
                subgroup_item = MapEnemySubGroupTableEntry.from_block(block, group_offset)
                group_offset += MapEnemySubGroupTableEntry.size
                subgroup_rate += subgroup_item[0]
                subgroup_1.append(subgroup_item)

        subgroup_2 = []
        if group_value[2] > 0:
            subgroup_rate = 0
            while subgroup_rate < 8:
                subgroup_item = MapEnemySubGroupTableEntry.from_block(block, group_offset)
                group_offset += MapEnemySubGroupTableEntry.size
                subgroup_rate += subgroup_item[0]
                subgroup_2.append(subgroup_item)

        return group_value, subgroup_1, subgroup_2

    @classmethod
    def to_block(cls, block, offset, value):
        group_value, subgroup_1, subgroup_2 = value
        data_size = MapEnemyGroupTableEntry.size
        if group_value[1] > 0:
            data_size += len(subgroup_1) * MapEnemySubGroupTableEntry.size
        if group_value[2] > 0:
            data_size += len(subgroup_2) * MapEnemySubGroupTableEntry.size
        pointer = block.allocate(size=data_size)
        super(MapEnemyGroupPointerTableEntry, cls).to_block(block, offset, to_snes_address(pointer))

        MapEnemyGroupTableEntry.to_block(block, pointer, group_value)
        pointer += MapEnemyGroupTableEntry.size

        if group_value[1] > 0:
            for subgroup_entry in subgroup_1:
                MapEnemySubGroupTableEntry.to_block(block, pointer, subgroup_entry)
                pointer += MapEnemySubGroupTableEntry.size

        if group_value[2] > 0:
            for subgroup_entry in subgroup_2:
                MapEnemySubGroupTableEntry.to_block(block, pointer, subgroup_entry)
                pointer += MapEnemySubGroupTableEntry.size

    @classmethod
    def to_yml_rep(cls, value):
        group_value, subgroup_1, subgroup_2 = value
        yml_rep = MapEnemyGroupTableEntry.to_yml_rep(group_value)

        subgroup_yml_rep = dict()
        for i, subgroup_entry in enumerate(subgroup_1):
            subgroup_yml_rep[i] = MapEnemySubGroupTableEntry.to_yml_rep(subgroup_entry)
        yml_rep["Sub-Group 1"] = subgroup_yml_rep

        subgroup_yml_rep = dict()
        for i, subgroup_entry in enumerate(subgroup_2):
            subgroup_yml_rep[i] = MapEnemySubGroupTableEntry.to_yml_rep(subgroup_entry)
        yml_rep["Sub-Group 2"] = subgroup_yml_rep
        return yml_rep

    @classmethod
    def from_yml_rep(cls, yml_rep):
        group_value = MapEnemyGroupTableEntry.from_yml_rep(yml_rep)
        subgroup_1 = [MapEnemySubGroupTableEntry.from_yml_rep(x) for x in yml_rep["Sub-Group 1"].itervalues()]
        subgroup_2 = [MapEnemySubGroupTableEntry.from_yml_rep(x) for x in yml_rep["Sub-Group 2"].itervalues()]
        return group_value, subgroup_1, subgroup_2

    @classmethod
    def hex_labels(cls):
        return MapEnemyGroupTableEntry.hex_labels()