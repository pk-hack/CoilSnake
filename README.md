## [CoilSnake](http://kiij.github.io/CoilSnake/)

**CoilSnake** is the most powerful [mod making tool](https://en.wikipedia.org/wiki/Game_mod) for the game
[*EarthBound*](https://en.wikipedia.org/wiki/EarthBound).
CoilSnake deconstructs the game's assets into individual text and PNG files, and then lets you "build" a new ROM
using modified assets.
Most of the game's data is editable by CoilSnake, making it possible to create entirely new games in the EarthBound
engine.

### Installation

#### Windows

Download the Windows version of CoilSnake [here](http://kiij.github.io/CoilSnake/).

#### Linux

    sudo apt-get install python-pip python-dev libyaml-dev python-tk \
                         g++ libboost-filesystem-dev
    git clone https://github.com/kiij/CoilSnake.git
    cd CoilSnake
    make
    sudo make install

After installing, you can start up the GUI with:

    coilsnake

To use the command line interface:

    coilsnake-cli

### Development

If you are developing CoilSnake, you may wish to install it in “development mode”,
which makes CoilSnake available on `sys.path` but also allows it to be edited directly from its source checkout.

    make
    python setup.py develop
    ./script/gui.py  # Launch the GUI
    ./script/cli.py  # Launch the CLI

### Running the Tests

    make test

### Support or Contact

* Submit [issues or feature  requests](https://github.com/kiij/CoilSnake/issues).
* Read the [CoilSnake tutorial](https://github.com/kiij/CoilSnake/wiki/Tutorial).
* Visit the [forum](http://forum.starmen.net/forum/Community/PKHack) or [IRC channel](irc://irc.thinstack.net/pkhax).