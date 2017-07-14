from coilsnake.exceptions.common.exceptions import TableSchemaError, \
    TableEntryError
from coilsnake.model.common.table import LittleEndianIntegerTableEntry, \
    RowTableEntry, TableEntry
from coilsnake.model.eb.table import EbEventFlagTableEntry


EnemyGroupTableEntry = RowTableEntry.from_schema(
    name="Enemy Group Entry",
    schema=[LittleEndianIntegerTableEntry.create("Amount", 1),
            LittleEndianIntegerTableEntry.create("Enemy", 2)]
)

MapEnemyGroupHeaderTableEntry = RowTableEntry.from_schema(
    name="Map Enemy Group Header Table Entry",
    schema=[EbEventFlagTableEntry,
            type("Rate1", (LittleEndianIntegerTableEntry,), {"name": "Sub-Group 1 Rate", "size": 1}),
            type("Rate2", (LittleEndianIntegerTableEntry,), {"name": "Sub-Group 2 Rate", "size": 1})]
)

MapEnemySubGroupTableEntry = RowTableEntry.from_schema(
    name="Map Enemy Sub-Group Table Entry",
    schema=[type("Probability", (LittleEndianIntegerTableEntry,), {"name": "Probability", "size": 1}),
            type("EnemyGroup", (LittleEndianIntegerTableEntry,), {"name": "Enemy Group", "size": 2})]
)


class MapEnemyGroupTableEntry(TableEntry):
    name = "Map Enemy Group Table Entry"

    @classmethod
    def from_block(cls, block, offset):
        header_value = MapEnemyGroupHeaderTableEntry.from_block(block, offset)
        offset += MapEnemyGroupHeaderTableEntry.size

        subgroup_1 = []
        if header_value[1] > 0:
            subgroup_rate = 0
            while subgroup_rate < 8:
                subgroup_item = MapEnemySubGroupTableEntry.from_block(block, offset)
                offset += MapEnemySubGroupTableEntry.size
                subgroup_rate += subgroup_item[0]
                subgroup_1.append(subgroup_item)

        subgroup_2 = []
        if header_value[2] > 0:
            subgroup_rate = 0
            while subgroup_rate < 8:
                subgroup_item = MapEnemySubGroupTableEntry.from_block(block, offset)
                offset += MapEnemySubGroupTableEntry.size
                subgroup_rate += subgroup_item[0]
                subgroup_2.append(subgroup_item)

        return header_value, subgroup_1, subgroup_2

    @classmethod
    def to_block_size(cls, value):
        header_value, subgroup_1, subgroup_2 = value
        data_size = MapEnemyGroupHeaderTableEntry.size
        if header_value[1] > 0:
            data_size += len(subgroup_1) * MapEnemySubGroupTableEntry.size
        if header_value[2] > 0:
            data_size += len(subgroup_2) * MapEnemySubGroupTableEntry.size
        return data_size

    @classmethod
    def to_block(cls, block, offset, value):
        header_value, subgroup_1, subgroup_2 = value
        MapEnemyGroupHeaderTableEntry.to_block(block, offset, header_value)
        offset += MapEnemyGroupHeaderTableEntry.size

        if header_value[1] > 0:
            for subgroup_entry in subgroup_1:
                MapEnemySubGroupTableEntry.to_block(block, offset, subgroup_entry)
                offset += MapEnemySubGroupTableEntry.size

        if header_value[2] > 0:
            for subgroup_entry in subgroup_2:
                MapEnemySubGroupTableEntry.to_block(block, offset, subgroup_entry)
                offset += MapEnemySubGroupTableEntry.size

    @classmethod
    def to_yml_rep(cls, value):
        group_value, subgroup_1, subgroup_2 = value
        yml_rep = MapEnemyGroupHeaderTableEntry.to_yml_rep(group_value)

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
        group_value = MapEnemyGroupHeaderTableEntry.from_yml_rep(yml_rep)
        subgroup_1 = cls._subgroup_from_yml_rep(yml_rep["Sub-Group 1"], "Sub-Group 1")
        subgroup_2 = cls._subgroup_from_yml_rep(yml_rep["Sub-Group 2"], "Sub-Group 2")
        return group_value, subgroup_1, subgroup_2
    
    @classmethod
    def _subgroup_from_yml_rep(cls, subgroup_yml_rep, field_id):
        if not subgroup_yml_rep:
            return []
        subgroup = [MapEnemySubGroupTableEntry.from_yml_rep(x) for x in subgroup_yml_rep.values()]
        subgroup_sum = sum([x[0] for x in subgroup])
        if subgroup_sum != 8:
            raise TableSchemaError(field=field_id,
                                   cause=TableEntryError(
                                       ("A Map Enemy Sub-Group's probabilities have a sum exactly 8, "
                                        "instead has a sum of {}").format(subgroup_sum)))
        return subgroup

    @classmethod
    def yml_rep_hex_labels(cls):
        return MapEnemyGroupHeaderTableEntry.yml_rep_hex_labels()