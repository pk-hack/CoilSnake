# coding: utf-8

from coilsnake.exceptions.common.exceptions import InvalidUserDataError
from coilsnake.modules.eb.EbModule import EbModule
from coilsnake.util.common.yml import yml_load
from coilsnake.util.eb.text import CharacterSubstitutions

MODULE_COMMENT = """# List all text characters that you would like to substitute
# As of CoilSnake 2.3, this only affects YML files, and has no impact on CCScript files.
# Example:
#
# 'я': '[B0]'"""


class CharacterSubstitutionsModule(EbModule):
    NAME = "Character Substitutions"
    FILE = 'Fonts/character_substitutions'

    def read_from_project(self, resource_open):
        with resource_open("Fonts/character_substitutions", "yml", True) as f:
            data = yml_load(f)

        if data is not None:
            for key, value in data.items():
                if not isinstance(key, str):
                    raise InvalidUserDataError("String to be replaced is not actually a string: " + key)
                if len(key) != 1:
                    raise InvalidUserDataError("String to be replaced must be a 1 character long: " + key)
                if not isinstance(value, str):
                    raise InvalidUserDataError("String to replace with is not actually a string: " + value)

        CharacterSubstitutions.character_substitutions = data

    def write_to_project(self, resource_open):
        with resource_open(self.FILE, 'yml', True) as f:
            f.write(MODULE_COMMENT)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        if old_version <= 7:
            self.write_to_project(resource_open_w)