from coilsnake.Progress import updateProgress


class GenericModule:
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
        updateProgress(50)

    def write_to_rom(self, rom):
        updateProgress(50)

    def read_from_project(self, resource_open):
        updateProgress(50)

    def write_to_project(self, resource_open):
        updateProgress(50)

    def upgrade_project(self, old_version, new_version, rom, resource_open_r, resource_open_w, resource_delete):
        updateProgress(100)
