from coilsnake.util.common import project

VERSION = project.VERSION_NAMES[project.FORMAT_VERSION]
RELEASE_DATE = "?/?/2014"

WEBSITE = "http://kiij.github.io/CoilSnake"
AUTHOR = "MrTenda"
DEPENDENCIES = [
    {"name": "CCScript",
     "author": "Mr. Accident",
     "url":"http://starmen.net/pkhack/ccscript"},
    {"name": "CCScriptWriter",
     "author": "Lyrositor",
     "url": "https://github.com/Lyrositor/CCScriptWriter"},
    {"name": "EBYAML",
     "author": "Penguin",
     "url": "https://github.com/PKHackers/EBYAML"},
    {"name": "EarthBound Compression Library",
     "author": "Goplat"},
    {"name": "JHack",
     "author": "AnyoneEB"}
    ]


def coilsnake_about():
    description = """CoilSnake {version} by {author} ({release_date})
Website: {website}""".format(version=VERSION, author=AUTHOR, release_date=RELEASE_DATE, website=WEBSITE)

    for dependency in DEPENDENCIES:
        description += "\n* " + dependency["name"]
        if "author" in dependency:
            description += " by {}".format(dependency["author"])
        if "url" in dependency:
            description += " ({})".format(dependency["url"])

    return description