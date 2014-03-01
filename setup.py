#! /usr/bin/env python

from setuptools import setup, find_packages
from setuptools.extension import Extension

from coilsnake.ui import information


setup(
    name="coilsnake",
    version=information.VERSION,
    description="A program for modifying the EarthBound ROM.",
    url="http://kiij.github.io/CoilSnake",
    packages=find_packages(),
    include_package_data=True,

    install_requires=["Pillow", "PyYAML"],
    ext_modules=[
        Extension("coilsnake.modules.eb.NativeComp", ["coilsnake/modules/eb/NativeComp.c"])
    ],
    entry_points={
        "console_scripts": [
            "coilsnake = coilsnake.ui.gui:main",
            "coilsnake-cmd = coilsnake.ui.cli:main"
        ]
    },

    test_suite="nose.collector",
    tests_require=["nose>=1.0", "mock"],
)