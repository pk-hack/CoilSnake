import logging

from coilsnake.model.eb.blocks import EbCompressibleBlock
from coilsnake.model.eb.enemy_groups import EnemyGroupTableEntry
from coilsnake.model.eb.palettes import EbPalette
from coilsnake.model.eb.sprites import EbBattleSprite
from coilsnake.model.eb.table import eb_table_from_offset
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.image import open_indexed_image
from coilsnake.util.common.yml import replace_field_in_yml, yml_load, yml_dump
from coilsnake.util.eb.pointer import from_snes_address, read_asm_pointer, to_snes_address, write_asm_pointer


log = logging.getLogger(__name__)


GRAPHICS_POINTER_TABLE_ASM_POINTER_OFFSET = 0x2ee0b
GRAPHICS_POINTER_TABLE_POINTER_OFFSETS = [0x2ebe0, 0x2f014, 0x2f065]
PALETTES_ASM_POINTER_OFFSET = 0x2ef74

ENEMY_CONFIGURATION_TABLE_DEFAULT_OFFSET = 0xD59589
BATTLE_SPRITES_POINTER_TABLE_DEFAULT_OFFSET = 0xCE62EE
ENEMY_GROUP_TABLE_DEFAULT_OFFSET = 0xD0C60D
ENEMY_GROUP_BACKGROUND_TABLE_DEFAULT_OFFSET = 0xCBD89A


class EnemyModule(EbModule):
    NAME = "Enemies"
    FREE_RANGES = [(0x0d0000, 0x0dffff),  # Battle Sprites
                   (0x0e0000, 0x0e6913),  # Battle Sprites continued & Battle Sprite palettes
                   (0x10d52d, 0x10dfb3)]  # Enemy Group Data

    def __init__(self):
        super(EnemyModule, self).__init__()
        self.enemy_config_table = eb_table_from_offset(offset=ENEMY_CONFIGURATION_TABLE_DEFAULT_OFFSET,
                                                       hidden_columns=["Battle Sprite", "Battle Sprite Palette"])
        self.graphics_pointer_table = eb_table_from_offset(offset=BATTLE_SPRITES_POINTER_TABLE_DEFAULT_OFFSET)
        self.enemy_group_table = eb_table_from_offset(offset=ENEMY_GROUP_TABLE_DEFAULT_OFFSET,
                                                      hidden_columns=["Pointer"])
        self.enemy_group_bg_table = eb_table_from_offset(offset=ENEMY_GROUP_BACKGROUND_TABLE_DEFAULT_OFFSET)

        self.battle_sprites = None
        self.palettes = None
        self.enemy_groups = None

    def read_from_rom(self, rom):
        self.enemy_config_table.from_block(block=rom,
                                           offset=from_snes_address(ENEMY_CONFIGURATION_TABLE_DEFAULT_OFFSET))
        self.enemy_group_bg_table.from_block(block=rom,
                                             offset=from_snes_address(ENEMY_GROUP_BACKGROUND_TABLE_DEFAULT_OFFSET))

        # Read the sprites
        log.debug("Reading battle sprites")
        self.graphics_pointer_table.from_block(
            rom, from_snes_address(read_asm_pointer(block=rom, offset=GRAPHICS_POINTER_TABLE_ASM_POINTER_OFFSET)))
        self.battle_sprites = []
        for i in range(self.graphics_pointer_table.num_rows):
            with EbCompressibleBlock() as compressed_block:
                compressed_block.from_compressed_block(
                    block=rom,
                    offset=from_snes_address(self.graphics_pointer_table[i][0]))
                sprite = EbBattleSprite()
                sprite.from_block(block=compressed_block, offset=0, size=self.graphics_pointer_table[i][1])
                self.battle_sprites.append(sprite)

        # Determine how many palettes there are
        num_palettes = 0
        for i in range(self.enemy_config_table.num_rows):
            num_palettes = max(num_palettes, self.enemy_config_table[i][14])
        num_palettes += 1

        # Read the palettes
        log.debug("Reading palettes")
        palettes_offset = from_snes_address(read_asm_pointer(block=rom, offset=PALETTES_ASM_POINTER_OFFSET))
        self.palettes = []
        for i in range(num_palettes):
            palette = EbPalette(num_subpalettes=1, subpalette_length=16)
            palette.from_block(block=rom, offset=palettes_offset)
            self.palettes.append(palette)
            palettes_offset += palette.block_size()

        # Read the groups
        log.debug("Reading enemy groups")
        self.enemy_group_table.from_block(rom, from_snes_address(ENEMY_GROUP_TABLE_DEFAULT_OFFSET))
        self.enemy_groups = []
        for i in range(self.enemy_group_table.num_rows):
            group = []
            group_offset = from_snes_address(self.enemy_group_table[i][0])
            while rom[group_offset] != 0xff:
                group.append(EnemyGroupTableEntry.from_block(block=rom, offset=group_offset))
                group_offset += EnemyGroupTableEntry.size
            self.enemy_groups.append(group)

    def write_to_rom(self, rom):
        self.enemy_config_table.to_block(block=rom,
                                         offset=from_snes_address(ENEMY_CONFIGURATION_TABLE_DEFAULT_OFFSET))
        self.enemy_group_bg_table.to_block(block=rom,
                                           offset=from_snes_address(ENEMY_GROUP_BACKGROUND_TABLE_DEFAULT_OFFSET))

        # Write the sprites
        self.graphics_pointer_table.recreate(num_rows=len(self.battle_sprites))
        for i, battle_sprite in enumerate(self.battle_sprites):
            self.graphics_pointer_table[i] = [None, battle_sprite.size()]
            with EbCompressibleBlock(size=battle_sprite.block_size()) as compressed_block:
                battle_sprite.to_block(block=compressed_block, offset=0)
                compressed_block.compress()
                graphics_offset = rom.allocate(data=compressed_block)
                self.graphics_pointer_table[i][0] = to_snes_address(graphics_offset)

        graphics_pointer_table_offset = rom.allocate(size=self.graphics_pointer_table.size)
        self.graphics_pointer_table.to_block(block=rom, offset=graphics_pointer_table_offset)
        write_asm_pointer(block=rom, offset=GRAPHICS_POINTER_TABLE_ASM_POINTER_OFFSET,
                          pointer=to_snes_address(graphics_pointer_table_offset))
        for pointer_offset in GRAPHICS_POINTER_TABLE_POINTER_OFFSETS:
            rom.write_multi(pointer_offset, item=to_snes_address(graphics_pointer_table_offset), size=3)

        # Write the palettes
        if self.palettes:
            palettes_offset = rom.allocate(size=self.palettes[0].block_size() * len(self.palettes))
            write_asm_pointer(block=rom, offset=PALETTES_ASM_POINTER_OFFSET, pointer=to_snes_address(palettes_offset))
            for palette in self.palettes:
                palette.to_block(block=rom, offset=palettes_offset)
                palettes_offset += palette.block_size()

        # Write the groups
        for i, group in enumerate(self.enemy_groups):
            offset = rom.allocate(size=(len(group) * EnemyGroupTableEntry.size + 1))
            self.enemy_group_table[i][0] = to_snes_address(offset)
            for group_entry in group:
                EnemyGroupTableEntry.to_block(block=rom, offset=offset, value=group_entry)
                offset += EnemyGroupTableEntry.size
            rom[offset] = 0xff
        self.enemy_group_table.to_block(block=rom, offset=from_snes_address(ENEMY_GROUP_TABLE_DEFAULT_OFFSET))

    def write_to_project(self, resource_open):
        with resource_open("enemy_configuration_table", "yml", True) as f:
            self.enemy_config_table.to_yml_file(f)

        # Write the battle sprite images
        log.debug("Writing battle sprites")
        for i in range(self.enemy_config_table.num_rows):
            battle_sprite_id = self.enemy_config_table[i][4]
            if battle_sprite_id > 0:
                palette_id = self.enemy_config_table[i][14]
                palette = self.palettes[palette_id]

                image = self.battle_sprites[battle_sprite_id - 1].image(palette=palette)
                with resource_open("BattleSprites/" + str(i).zfill(3), "png") as f:
                    image.save(f, "png", transparency=0)
                del image

        # Write the groups
        log.debug("Writing groups")
        out = dict()
        enemy_group_table_yml_rep = self.enemy_group_table.to_yml_rep()
        enemy_group_bg_table_yml_rep = self.enemy_group_bg_table.to_yml_rep()
        for i, group in enumerate(self.enemy_groups):
            entry = enemy_group_table_yml_rep[i]
            entry.update(enemy_group_bg_table_yml_rep[i])

            group_yml_rep = []
            for enemy_entry in group:
                group_yml_rep.append(EnemyGroupTableEntry.to_yml_rep(enemy_entry))
            entry["Enemies"] = group_yml_rep

            out[i] = entry

        with resource_open("enemy_groups", "yml", True) as f:
            yml_dump(out, f)

    def read_from_project(self, resource_open):
        with resource_open("enemy_configuration_table", "yml", True) as f:
            self.enemy_config_table.from_yml_file(f)

        # Read the sprites and palettes
        self.battle_sprites = []
        self.palettes = []

        sprite_hashes = dict()
        num_sprites = 0
        palette_hashes = dict()
        num_palettes = 0
        for i in range(self.enemy_config_table.num_rows):
            battle_sprite = EbBattleSprite()
            palette = EbPalette(num_subpalettes=1, subpalette_length=16)

            try:
                with resource_open("BattleSprites/" + str(i).zfill(3), "png") as f:
                    image = open_indexed_image(f)
                    battle_sprite.from_image(image)
                    palette.from_image(image)
                    del image
            except IOError:
                # No battle sprite
                self.enemy_config_table[i][4] = 0
                self.enemy_config_table[i][14] = 0
                continue

            sprite_hash = battle_sprite.hash()
            try:
                self.enemy_config_table[i][4] = sprite_hashes[sprite_hash] + 1
            except KeyError:
                self.enemy_config_table[i][4] = num_sprites + 1
                sprite_hashes[sprite_hash] = num_sprites
                self.battle_sprites.append(battle_sprite)
                num_sprites += 1

            palette_hash = palette.hash()
            try:
                self.enemy_config_table[i][14] = palette_hashes[palette_hash]
            except KeyError:
                self.enemy_config_table[i][14] = num_palettes
                palette_hashes[palette_hash] = num_palettes
                self.palettes.append(palette)
                num_palettes += 1

        # Read the groups
        with resource_open("enemy_groups", "yml", True) as f:
            self.enemy_group_table.from_yml_file(f)

        with resource_open("enemy_groups", "yml", True) as f:
            self.enemy_group_bg_table.from_yml_file(f)

        with resource_open("enemy_groups", "yml", True) as f:
            self.enemy_groups = []
            enemy_groups_yml_rep = yml_load(f)
            for entry in enemy_groups_yml_rep.values():
                enemy_group = entry["Enemies"]
                if type(enemy_group) == dict:
                    enemy_group = [enemy_group[x] for x in sorted(enemy_group.keys())]
                group = [EnemyGroupTableEntry.from_yml_rep(x) for x in enemy_group]
                self.enemy_groups.append(group)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version == new_version:
            return
        elif old_version == 12:
            replace_field_in_yml(resource_name="enemy_configuration_table",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key="Flash vulnerability",
                                 value_map={"100%": "99%",
                                            "70%": "50%",
                                            "40%": "10%",
                                            "5%": "0%"}),
            replace_field_in_yml(resource_name="enemy_configuration_table",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key="Hypnosis/Brainshock vulnerability",
                                 value_map={"100%": "99%"}),
            replace_field_in_yml(resource_name="enemy_configuration_table",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key="Paralysis vulnerability",
                                 value_map={"100%": "99%"})
            self.upgrade_project(
                old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        elif old_version == 3:
            replace_field_in_yml(resource_name="enemy_configuration_table",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key='"The" Flag',
                                 value_map={0: "False",
                                            1: "True"}),
            replace_field_in_yml(resource_name="enemy_configuration_table",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key="Boss Flag",
                                 value_map={0: "False",
                                            1: "True"}),
            replace_field_in_yml(resource_name="enemy_configuration_table",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key="Run Flag",
                                 value_map={6: "Unknown",
                                            7: "True",
                                            8: "False"}),
            replace_field_in_yml(resource_name="enemy_configuration_table",
                                 resource_open_r=resource_open_r,
                                 resource_open_w=resource_open_w,
                                 key="Item Rarity",
                                 value_map={0: "1/128",
                                            1: "2/128",
                                            2: "4/128",
                                            3: "8/128",
                                            4: "16/128",
                                            5: "32/128",
                                            6: "64/128",
                                            7: "128/128"})
            self.upgrade_project(
                old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
        else:
            self.upgrade_project(
                old_version + 1, new_version, rom, resource_open_r, resource_open_w, resource_delete)
