# CoilSnake Development Guide

## Linux

Because Python is notorious for being difficult to maintain a clean installation of, I recommend developing either in a Python virtualenv or in an actual virtual machine.

### Using a virtualenv

1. `apt-get install` any system dependencies requried by CoilSnake. These are listed in the official [CoilSnake installation instructions](https://mrtenda.github.io/CoilSnake/download.html).
1. `sudo pip install virtualenv`
1. `virtualenv CoilSnake_virtualenv --no-site-packages`
1. `source CoilSnake_virtualenv/bin/activate`
  * The above command sets up your CoilSnake virtual development environment. When you open a new terminal for CoilSnake development, always re-run the above command in order to re-enter the virtual development environment. For more information about how this works, see [virtualenv's documentation](https://pypi.python.org/pypi/virtualenv/1.7).
1. `git clone --recursive https://github.com/mrtenda/CoilSnake.git`
1. `cd CoilSnake`
1. `make`
1. `python setup.py develop`

CoilSnake is now installed in development mode in its own virtualenv, so it does not interfere with other parts of your system. After making code changes to the source, run your code by launching CoilSnake's GUI or CLI:

    python script/gui.py
    # or...
    python script/cli.py

### Using a virtual machine

1. `git clone --recursive https://github.com/mrtenda/CoilSnake.git`
1. `cd CoilSnake`
1. `vagrant up ubuntu`
1. `vagrant ssh ubuntu`
1. `cd /vagrant`
1. `sudo python setup.py develop`

CoilSnake is now installed in development mode on the virtual machine. After making code changes to the source, you can test it by running CoilSnake's CLI interface.

    python script/cli.py
    
Please note that the included Vagrant configuration does not run a GUI, meaning that you won't be able to test CoilSnake's GUI with it.

## Windows

1. Install:
    1. [Python 3.6](https://www.python.org/downloads/release/python-362/) (64-bit version)
    1. [Visual C++ 2015 Build Tools](http://landinghub.visualstudio.com/visual-cpp-build-tools)
    1. [PyYAML](http://pyyaml.org/wiki/PyYAML)
        1. If using Python 3.6, download unoffical wheels [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyyaml)
        1. `pip install PyYAML-3.12-cp36-cp36m-win_amd64.whl`
1. Using your favorite git client, clone the [CoilSnake](https://github.com/mrtenda/CoilSnake) repository.
    1. If the `coilsnake\assets\mobile-sprout` directory is empty, clone the [mobile-sprout repository](https://github.com/mrtenda/mobile-sprout) and copy its contents to the `coilsnake\assets\mobile-sprout` directory.
1. Open the command line and cd to your local CoilSnake git repository's main directory.
1. `python setup.py develop`

CoilSnake is now installed in development mode. After making code changes to the source, run your code by launching CoilSnake's GUI:

    python .\script\gui.py

### Creating a standalone Windows executable

You'll probably want to follow these steps from a fresh virtual machine. You can start up a new Windows 7 VM by the following command: `vagrant up windows`

1. Install:
    1. [Python 3.6](https://www.python.org/downloads/release/python-362/) (64-bit version)
    1. [Visual C++ 2015 Build Tools](http://landinghub.visualstudio.com/visual-cpp-build-tools)
    1. [NSIS 3.x](http://nsis.sourceforge.net/Download)
    1. [PyYAML](http://pyyaml.org/wiki/PyYAML)
        1. If using Python 3.6, download unoffical wheels [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyyaml)
        1. `pip install PyYAML-3.12-cp36-cp36m-win_amd64.whl`
    1. [cx_freeze](https://anthony-tuininga.github.io/cx_Freeze/)
        1. `pip install cx_Freeze`
1. Using your favorite git client, clone the [CoilSnake](https://github.com/mrtenda/CoilSnake) repository.
    1. If the `coilsnake\assets\mobile-sprout` directory is empty, clone the [mobile-sprout repository](https://github.com/mrtenda/mobile-sprout) and copy its contents to the `coilsnake\assets\mobile-sprout` directory.
1. Open the command line and cd to your local CoilSnake git repository's main directory.
1. Ensure CoilSnake dependencies are installed in a non-compressed form using pip (cx_freeze doesn't work well with compressed eggs)
    1. `pip install --process-dependency-links .`
1. Create the CoilSnake EXE
    1. `python setup.py develop`
    1. `python setup_exe.py build_exe`
1. Run `coilsnake.nsi`
