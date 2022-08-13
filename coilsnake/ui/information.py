from coilsnake.util.common import project

VERSION = project.VERSION_NAMES[project.FORMAT_VERSION]
RELEASE_DATE = "August 13, 2022"

WEBSITE = "http://pk-hack.github.io/CoilSnake"
AUTHOR = "the PK Hack community"
ADDITIONAL_CREDITS = """- Some portions based on JHack, created by AnyoneEB
- Contributions by H.S, Michael1, John Soklaski,
  João Silva, ShadowOne333, stochaztic, Catador,
  cooprocks123e, and many others"""
DEPENDENCIES = [
    {"name": "CoilSnake logo and icon",
     "author": "Rydel"},
    {"name": "CoilSnake 4 logo",
     "author": "vince94"},
    {"name": "CCScript",
     "author": "Mr. Accident",
     "url": "http://starmen.net/pkhack/ccscript"},
    {"name": "CCScriptWriter",
     "author": "Lyrositor",
     "url": "https://github.com/Lyrositor/CCScriptWriter"},
    {"name": "EBYAML",
     "author": "Penguin",
     "url": "https://github.com/PKHackers/EBYAML"},
    {"name": "exhal Compression Library",
     "author": "Devin Acker",
     "url": "https://github.com/devinacker/exhal"},
    {"name": "EB++",
     "author": "Rufus",
     "url": "http://goo.gl/BnNqUM"}
]


def coilsnake_about():
    description = """CoilSnake {version} - {website}
Created by {author}
Released on {release_date}
""".format(version=VERSION, author=AUTHOR, release_date=RELEASE_DATE, website=WEBSITE)

    for dependency in DEPENDENCIES:
        description += "\n- " + dependency["name"]
        if "author" in dependency:
            description += " created by {}".format(dependency["author"])
        if "url" in dependency:
            description += "\n  {}".format(dependency["url"])

    description += "\n" + ADDITIONAL_CREDITS
    return description
