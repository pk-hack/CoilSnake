from coilsnake.modules.common.GenericModule import GenericModule


class Eb0Module(GenericModule):
    def compatibilityWithRomtype(self, romtype):
        return romtype == "Earthbound Zero"
