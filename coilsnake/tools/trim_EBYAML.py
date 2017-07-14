#! /usr/bin/env python

# Trims an inputted EBYAML file so it only has the info CoilSnake needs
# IE: Removes all data only leaving table entries

import sys
from re import sub

import yaml

from coilsnake.util.common.yml import yml_dump


if len(sys.argv) != 3:
    sys.exit("Must supply input & output EBYAML file")

with open(sys.argv[1], "r") as f:
    with open(sys.argv[2], "w") as f2:
        i = 1
        for doc in yaml.load_all(f, Loader=yaml.CSafeLoader):
            if i == 1:
                f2.write("# This is a automatically generated trimmed version of the full EBYAML file.\n"
                         + "# This file only contains data block descriptions which have an \"entries\" entry.\n"
                         + "---\n...\n---\n")
                i += 1
            elif i == 2:
                newDoc = dict()
                for block in doc:
                    if not (doc[block] is None
                            or not ("type" in doc[block])
                            or ("data" in doc[block]["type"])
                            or not ("entries" in ("entries" in doc[block]))):
                        newDoc[block] = doc[block]
                        if "description" in newDoc[block]:
                            del(newDoc[block]["description"])
                s = yml_dump(newDoc, default_flow_style=False)
                # Convert labels to hex
                s = sub("(\d+):\n",
                        lambda i: "0x" + hex(
                            int(i.group(0)[:-2]))[2:].upper() + ":\n", s)
                f2.write(s)
                f2.write('\n...')
                break

sys.exit(0)
