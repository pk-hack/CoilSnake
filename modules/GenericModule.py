from modules.Progress import updateProgress
import yaml


def replaceField(fname, oldField, newField, valueMap, resourceOpenerR,
                 resourceOpenerW):
    if newField is None:
        newField = oldField
        valueMap = dict((k.lower() if (isinstance(k, str)) else k, v)
                        for k, v in valueMap.iteritems())
        with resourceOpenerR(fname, 'yml') as f:
            data = yaml.load(f, Loader=yaml.CSafeLoader)
            for i in data:
                if data[i][oldField] in valueMap:
                    if isinstance(data[i][oldField], str):
                        data[i][newField] = valueMap[data[i]
                            [oldField].lower()].lower()
                    else:
                        data[i][newField] = valueMap[data[i][oldField]].lower()
                else:
                    data[i][newField] = data[i][oldField]
                if newField != oldField:
                    del data[i][oldField]
        with resourceOpenerW(fname, 'yml') as f:
            yaml.dump(data, f, default_flow_style=False,
                      Dumper=yaml.CSafeDumper)


class GenericModule:
    NAME = "Abstract Generic Module"
    FREE_RANGES = []

    def __init__(self):
        pass

    def compatibleWithRomtype(self, romtype):
        return True

    def free(self):
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
