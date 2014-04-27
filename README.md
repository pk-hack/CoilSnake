## CoilSnake

**CoilSnake** is a tool for modifying the ROM image of the 1995 Super Nintendo game *EarthBound*.
CoilSnake allows you to edit the game's assets as text and PNG files, then "build" a new ROM using those assets.

CoilSnake supports modification of most of the data in *EarthBound*, including:

* sprites
* maps
* the script
* battle backgrounds
* items
* enemies
* and more!

### Installation
#### Windows
Download the Windows version of CoilSnake [here](http://kiij.github.io/CoilSnake/).

#### Linux
```
sudo apt-get install python-pip python-dev libyaml-dev python-tk g++ libboost-filesystem-dev
make
sudo make install
```

### Usage
After installing, you can start up the GUI with:
```
coilsnake
```

To use the command line interface:
```
coilsnake-cli
```

### Development
If you are developing CoilSnake, you may wish to install it in “development mode”,
which makes CoilSnake available on sys.path but also allows it to be edited directly from its source checkout.
```
make
python setup.py develop
./script/gui.py  # Launch the GUI
./script/cli.py  # Launch the CLI
```

### Running The Tests
To run the unit tests:
```
make test
```

### Support or Contact
For information about getting started with CoilSnake, please see the
[EB Hacking 101](http://www.lyros.net/files/EBHack101.pdf) document, created by
[Lyrositor](https://github.com/Lyrositor).

Having trouble with CoilSnake? Create an issue on [GitHub](https://github.com/kiij/CoilSnake/issues) or consult the
[PK Hack forum](forum.starmen.net/forum/Community/PKHack) and someone will help you sort it out.