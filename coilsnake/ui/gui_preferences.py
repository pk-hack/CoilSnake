import os

from coilsnake.util.common.yml import yml_load, yml_dump


class CoilSnakePreferences(object):
    PREFERENCES_BASE_FILENAME = ".coilsnake.yml"
    PREFERENCES_FILENAME = os.path.join(os.path.expanduser("~"), PREFERENCES_BASE_FILENAME)

    def load(self):
        try:
            with open(self.PREFERENCES_FILENAME, 'r') as f:
                self.preferences = yml_load(f)
        except IOError:
            self.preferences = {}

    def save(self):
        with open(self.PREFERENCES_FILENAME, "w") as f:
            yml_dump(self.preferences, f, default_flow_style=False)

    def get_ccscript_offset(self):
        return self["ccscript offset"] or 0xF10000

    def set_ccscript_offset(self, offset):
        self["ccscript offset"] = offset

    def get_default_tab(self):
        if "default tab" in self.preferences:
            return self.preferences["default tab"]
        else:
            return 0

    def set_default_tab(self, default_tab):
        self["default tab"] = default_tab

    def add_profile(self, tab_name, profile_name):
        tab = self._get_preferences_profile_tab(tab_name)
        tab[profile_name] = dict()

    def delete_profile(self, tab_name, profile_name):
        tab = self._get_preferences_profile_tab(tab_name)
        if profile_name in tab:
            del tab[profile_name]

    def has_profile(self, tab_name, profile_name):
        tab = self._get_preferences_profile_tab(tab_name)
        return profile_name in tab

    def get_profiles(self, tab_name):
        tab = self._get_preferences_profile_tab(tab_name)
        profiles = list(tab.keys())
        if " default" in tab.keys():
            profiles.remove(" default")
        return profiles

    def get_default_profile(self, tab_name):
        tab = self._get_preferences_profile_tab(tab_name)
        if " default" in tab:
            return tab[" default"]
        else:
            return None

    def set_default_profile(self, tab_name, profile_name):
        tab = self._get_preferences_profile_tab(tab_name)
        tab[" default"] = profile_name

    def count_profiles(self, tab_name):
        tab = self._get_preferences_profile_tab(tab_name)
        return len(tab)

    def get_profile_value(self, tab_name, profile_name, field_id):
        profile = self._get_preferences_profile(tab_name, profile_name)
        if field_id not in profile:
            profile[field_id] = ""

        return profile[field_id]

    def set_profile_value(self, tab_name, profile_name, field_id, value):
        profile = self._get_preferences_profile(tab_name, profile_name)
        profile[field_id] = value

    def _get_preferences_profile_tab(self, tab_name):
        if "profiles" not in self.preferences:
            self.preferences["profiles"] = dict()
        if tab_name not in self.preferences["profiles"]:
            self.preferences["profiles"][tab_name] = {"Default Profile": {}}

        tab = self.preferences["profiles"][tab_name]

        if None in tab.keys():
            tab['NULL'] = tab[None]
            del tab[None]

        return tab

    def _get_preferences_profile(self, tab_name, profile_name):
        tab = self._get_preferences_profile_tab(tab_name)
        if profile_name not in tab:
            tab[profile_name] = dict()
        return tab[profile_name]

    def __getitem__(self, item):
        try:
            return self.preferences[item]
        except KeyError:
            return None

    def __setitem__(self, key, value):
        self.preferences[key] = value