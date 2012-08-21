from modules.Progress import updateProgress
import EbTablesModule

import yaml

class MiscTablesModule(EbTablesModule.EbTablesModule):
    _name = "Misc Tables"
    _tableIDs = [
            0xC3FD8D, # Attract mode text
            0xD5F645, # Timed Item Delivery
#            0xE01FC8, # Text Window Flavor palettes
            0xE12F8A, # Photographer
            0xEFA37A, # Command Window text?
            0xCF8985, # NPC Configuration Table
            0xD5EA77, # Condiment Table
            0xD5EBAB, # Scripted Teleport Destination Table
            0xD5F2FB, # Hotspots Table
            0xC3F2B5, # Playable Character Graphics Control Table
            0xD58D7A, # PSI Names
            0xD58A50, # PSI Abilities
            0xD57B68, # Battle Actions Table
            0xD5EA5B, # Statistic Growth Variables
            0xD58F49, # Level-up EXP Table
            0xD5F5F5, # Initial Stats Table
            0xD57880, # PSI Teleport Destination Table
            0xD57AAE, # Phone Contacts Table
            0xD576B2, # Store Inventory Table
            0xD5F4BB, # Timed Item Transformations
            0xD5F4CF, # Don't Care
            0xD55000, # Item Data
            0xC23109, # Consolation Item
            0xC3E250, # Windows
#            0xC3F054, # Font Ptr Tbl
#            0xC4C05E, # File select text # TODO need to fix this
#            0xC8CDED, # Compressed text ptr tbl
            0xCCF47F, # PSI Anim Pals
#            0xCCF58F, # PSI Anim Ptrs
#            0xCEDC45, # Swirl Ptr Tbl
            0xCEF806 # Sound stone pal
#            0xCF58EF, # Music Event Ptr Tbl
#            0xD01598, # Map Event Tile Ptr Tbl

            ]
    def upgradeProject(self, oldVersion, newVersion, rom, resourceOpenerR,
            resourceOpenerW):
        # Helper function
        def replaceField(fname, oldField, newField, valueMap):
            if newField == None:
                newField = oldField
            valueMap = dict((k.lower(), v) for k,v in valueMap.iteritems())
            with resourceOpenerR(fname, 'yml') as f:
                data = yaml.load(f, Loader=yaml.CSafeLoader)
                for i in data:
                    if data[i][oldField] in valueMap:
                        data[i][newField] = valueMap[data[i][oldField].lower()].lower()
                    else:
                        data[i][newField] = data[i][oldField]
                    if newField != oldField:
                        del data[i][oldField]
            with resourceOpenerW(fname, 'yml') as f:
                yaml.dump(data, f, default_flow_style=False,
                        Dumper=yaml.CSafeDumper)

        if oldVersion == newVersion:
            updateProgress(100)
            return
        elif oldVersion == 1:
            # PSI_ABILITY_TABLE: "Target" -> "Usability Outside of Battle"
            # Values: "Nobody"  -> "Other"
            #         "Enemies" -> "Unusable
            #         "Allies"  -> "Usable"
            replaceField('psi_ability_table', 
                    "Target", "Usability Outside of Battle", 
                    { "Nobody": "Other",
                        "Enemies": "Unusable",
                        "Allies": "Usable" })
            replaceField('battle_action_table',
                    "Direction", None,
                    { "Party": "Enemy",
                        "Enemy": "Party" })

            self.upgradeProject(oldVersion+1, newVersion, rom, resourceOpenerR,
                    resourceOpenerW)
        else:
            raise RuntimeException("Don't know how to upgrade from version",
                    oldVersion, "to", newVersion)
