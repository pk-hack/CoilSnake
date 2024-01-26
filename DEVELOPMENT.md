# CoilSnake Development Guide

## Environment

Because Python is notorious for being difficult to maintain a clean installation of, it is recommended to develop either in a Python virtualenv or in an actual virtual machine.

### Using a virtualenv

1. `sudo pip3 install virtualenv`
1. `virtualenv CoilSnake_virtualenv --no-site-packages`
1. `source CoilSnake_virtualenv/bin/activate`
    - The above command sets up your CoilSnake virtual development environment. When you open a new terminal for CoilSnake development, always re-run the above command in order to re-enter the virtual development environment. For more information about how this works, see [virtualenv's documentation](https://pypi.python.org/pypi/virtualenv/1.7).
1. Follow the steps mentioned below for your respective system.

### Using a virtual machine

For Windows, you'll probably want to follow the steps from a fresh virtual machine. You can start up a new Windows 10 VM by the following command: `vagrant up windows`

To make a Ubuntu VM, you can follow these instructions:

```
vagrant up ubuntu
vagrant ssh ubuntu
cd /vagrant
```

Please note that the included Vagrant configuration for Ubuntu does not run a GUI, meaning that you won't be able to test CoilSnake's GUI with it.

After installing a VM, follow the steps mentioned below for your respective system ([Linux](#linux)/[Windows](#windows)).

## Linux

1. Install any system dependencies required by CoilSnake. For Debian-based OSes, simply run:

```
sudo apt-get install python3-pip python3-dev g++ libyaml-dev \
                     python3-tk python3-pil.imagetk \
                     libjpeg-dev zlib1g-dev tk8.6-dev tcl8.6-dev
```


1. Follow the '[Generic](#generic)' instructions below.

## macOS

1. Install:
    1. [Command Line Tools for Xcode](https://developer.apple.com/downloads)
    1. [Python 3.9](https://www.python.org/downloads/release/python-392/)
        - Do not install non-official builds - this one includes Tk 8.6, with fixes and a nicer-looking UI over Tk 8.5.
    1. Homebrew:
        - `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
    1. libyaml:
        - `brew install libyaml`
    1. PyYAML with libyaml support:
        - `python3 -m pip install pyyaml`
1. Follow the '[Generic](#generic)' instructions below.

## Windows

1. Install:
    1. [Python 3.9](https://www.python.org/downloads/release/python-392/) (64-bit version)
    1. [Visual C++ 2019 Build Tools](https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16)
        - Select "C++ build tools" under the "Workloads" tab and make sure these are ticked:
            1. MSVC v140 - VS 2015 C++ x64/x86 build tools
            1. Windows 10 SDK
1. Find a path that exists on your computer similar to `C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x86` and add it to your system environment variables.
1. Follow the '[Generic](#generic)' instructions below.
1. In commands beginning with `python3` use just `python` instead.

## Generic

1. Using your favorite git client, clone the [CoilSnake](https://github.com/pk-hack/CoilSnake) repository.
1. Open the command line and `cd` to your local CoilSnake git repository's main directory.
1. `python3 -m pip install pip==18.1`
1. Install dependencies:
    - `python3 setup.py develop`
1. Build additional coilsnake dependencies:
    - `python3 setup.py build`

CoilSnake is now installed in development mode. After making code changes to the source, run your code by launching CoilSnake's GUI or CLI:

```
python3 script/gui.py
# or...
python3 script/cli.py
```

### Creating a standalone executable

Note: The steps for creating a standalone executable are currently unmaintained and likely broken for systems other than 64-bit Windows. 

1. Follow the steps above to build CoilSnake for your system.
1. Install pyinstaller:
    - `python3 -m pip install pyinstaller`
1. In the CoilSnake source directory, build the CoilSnake executable:
    - `python3 setup_exe.py`
1. Run the output file under the 'dist' directory.
