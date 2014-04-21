import os
import yaml


class CoilSnakePreferences(object):
    PREFERENCES_BASE_FILENAME = ".coilsnake.yml"
    PREFERENCES_FILENAME = os.path.join(os.path.expanduser("~"), PREFERENCES_BASE_FILENAME)

    def load(self):
        try:
            with open(self.PREFERENCES_FILENAME, 'r') as f:
                self.preferences = yaml.load(f, Loader=yaml.CSafeLoader)
        except IOError:
            self.preferences = {}

    def save(self):
        with open(self.PREFERENCES_FILENAME, "w") as f:
            yaml.dump(self.preferences, f, Dumper=yaml.CSafeDumper)

    def __getitem__(self, item):
        try:
            return self.preferences[item]
        except KeyError:
            return None

    def __setitem__(self, key, value):
        self.preferences[key] = value