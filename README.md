## CoilSnake

**CoilSnake** is a tool for modifying the ROM image of the 1995 Super Nintendo game *EarthBound*. It allows users to
extract data from the ROM image, modify the extracted data, and then re-compile the data into a new ROM image.
CoilSnake supports modification of most of the data in the game, such as:

* sprites
* maps
* the script and text
* battle backgrounds
* items
* enemies
* and more!

### Installation
```
sudo apt-get install python-dev libyaml-dev
python setup.py build
sudo python setup.py install
```

### Usage
To start up the GUI:
```
coilsnake
```

To use the command line client:
```
coilsnake-cmd
```

### Development
To run CoilSnake from source without installing:
```
sudo apt-get install python-dev libyaml-dev tk8.5-dev tcl8.5-dev
sudo pip install Pillow PyYAML
make
python coilsnake.py
# or...
python coilsnake-cmd.py
```

To run the unit tests:
```
python setup.py test
```

### Support or Contact
For information about getting started with CoilSnake, please see the
[EB Hacking 101](http://www.lyros.net/files/EBHack101.pdf) document, created by
[Lyrositor](https://github.com/Lyrositor).

Having trouble with CoilSnake? Create an issue on [GitHub](https://github.com/kiij/CoilSnake/issues) or consult the
[PK Hack forum](forum.starmen.net/forum/Community/PKHack) and someone will help you sort it out.