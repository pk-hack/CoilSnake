#!/usr/bin/env python

from setuptools import setup, find_packages
from distutils.command.install import install
from setuptools.extension import Extension
import os
import sys
import stat


class CoilSnakeInstallCommand(install):
    def run(self):
        install.run(self)

        # Remove the current directory from the front of sys.path
        sys.path.pop(0)
        # Mark the installed "ccc" executable as executable by everyone
        from coilsnake.util.common.assets import ccc_file_name
        ccc_fname = ccc_file_name()
        print "Making {} executable".format(ccc_fname)
        os.chmod(ccc_fname, stat.S_IXOTH)

setup(
    name="coilsnake",
    version="2.0",
    description="CoilSnake",
    url="http://kiij.github.io/CoilSnake",
    packages=find_packages(),
    include_package_data=True,

    install_requires=[
        "Pillow>=2.4.0",
        "PyYAML>=3.11",
        "CCScriptWriter>=1.1"
    ],
    dependency_links=[
        "http://github.com/Lyrositor/CCScriptWriter/tarball/master#egg=CCScriptWriter-1.1"
    ],
    ext_modules=[
        Extension("coilsnake.util.eb.native_comp", ["coilsnake/util/eb/native_comp.c"])
    ],
    entry_points={
        "console_scripts": [
            "coilsnake = coilsnake.ui.gui:main",
            "coilsnake-cli = coilsnake.ui.cli:main"
        ]
    },
    cmdclass={
        "install": CoilSnakeInstallCommand,
    },

    test_suite="nose.collector",
    tests_require=[
        "nose>=1.0",
        "mock>=1.0.1"
    ],
)
