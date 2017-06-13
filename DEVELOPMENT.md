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
  1. [Python 2.7](https://www.python.org/downloads/release/python-279/) (32-bit version)
  1. [Microsoft Visual C++ Compiler for Python 2.7](https://www.microsoft.com/download/details.aspx?id=44266)
  1. [boost 1.55](http://sourceforge.net/projects/boost/files/boost-binaries/) (32-bit vc90 version)
  1. [SetupTools](https://pypi.python.org/pypi/setuptools#windows-7-or-graphical-install)
1. Using your favorite git client, clone the [CoilSnake](https://github.com/mrtenda/CoilSnake) repository.
  1. If the `coilsnake\assets\mobile-sprout` directory is empty, clone the [mobile-sprout repository](https://github.com/mrtenda/mobile-sprout) and copy its contents to the `coilsnake\assets\mobile-sprout` directory.
1. Open the command line and cd to your local CoilSnake git repository's main directory.
1. `python.exe setup.py develop`

CoilSnake is now installed in development mode. After making code changes to the source, run your code by launching CoilSnake's GUI:

    path = c:\program files\microsoft visual studio 9.0\vc\redist\x86\Microsoft.VC90.CRT;c:\local\boost_1_55_0\lib32-msvc-9.0;%PATH%
    python.exe .\script\gui.py

### Creating a standalone Windows executable

You'll probably want to follow these steps from a fresh virtual machine. You can start up a new Windows 7 VM by the following command: `vagrant up windows`

1. Install:
    1. [Python 2.7](https://www.python.org/downloads/release/python-279/) (32-bit version)
    1. [Microsoft Visual C++ Compiler for Python 2.7](https://www.microsoft.com/download/details.aspx?id=44266)
    1. [boost 1.55](http://sourceforge.net/projects/boost/files/boost-binaries/) (32-bit vc90 version)
    1. [Pillow](http://pypi.python.org/pypi/Pillow)
    1. [PyYAML](http://pyyaml.org/wiki/PyYAML)
    1. [py2exe](http://www.py2exe.org/)
    1. [NSIS 3.x](http://nsis.sourceforge.net/Download)
1. Download [CCScriptWriter](https://github.com/Lyrositor/CCScriptWriter)
    1. `python.exe setup.py install_lib`
1. Download [ccscript_legacy](https://github.com/mraccident/ccscript_legacy)
    1. `python.exe setup.py install_lib`
1. Using your favorite git client, clone the [CoilSnake](https://github.com/mrtenda/CoilSnake) repository.
    1. If the `coilsnake\assets\mobile-sprout` directory is empty, clone the [mobile-sprout repository](https://github.com/mrtenda/mobile-sprout) and copy its contents to the `coilsnake\assets\mobile-sprout` directory.
    1. `python.exe setup.py install`
1. Create the CoilSnake EXE
    1. `path = c:\program files\microsoft visual studio 9.0\vc\redist\x86\Microsoft.VC90.CRT;c:\local\boost_1_55_0\lib32-msvc-9.0;%PATH%`
    1. `python setup_exe.py py2exe`
1. Run `coilsnake.nsi`
