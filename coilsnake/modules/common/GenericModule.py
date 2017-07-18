class GenericModule(object):
    NAME = "Abstract Generic Module"
    FREE_RANGES = []

    @staticmethod
    def is_compatible_with_romtype(romtype):
        return True

    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def read_from_rom(self, rom):
        pass

    def write_to_rom(self, rom):
        pass

    def read_from_project(self, resource_open):
        pass

    def write_to_project(self, resource_open):
        pass

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        pass
