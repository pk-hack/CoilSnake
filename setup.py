#!/usr/bin/env python

from setuptools import setup, find_packages
from setuptools.extension import Extension
import platform

extra_compile_args = []

if platform.system() != "Windows":
      extra_compile_args = ["-std=c99"]

setup(
    name="coilsnake",
    version="3.33",
    description="CoilSnake",
    url="https://mrtenda.github.io/CoilSnake",
    packages=find_packages(),
    include_package_data=True,

    install_requires=[
        "Pillow>=3.0.0",
        "PyYAML>=3.11",
        "CCScriptWriter>=1.2",
        "ccscript>=1.339"
    ],
    dependency_links=[
        "https://github.com/Lyrositor/CCScriptWriter/tarball/master#egg=CCScriptWriter-1.2",
        "https://github.com/jamsilva/ccscript_legacy/tarball/master#egg=ccscript-1.339"
    ],
    ext_modules=[
        Extension(
            "coilsnake.util.eb.native_comp",
            ["coilsnake/util/eb/native_comp.c", "coilsnake/util/eb/exhal/compress.c"],
            extra_compile_args=extra_compile_args,
        )
    ],
    entry_points={
        "console_scripts": [
            "coilsnake = coilsnake.ui.gui:main",
            "coilsnake-cli = coilsnake.ui.cli:main"
        ]
    },

    test_suite="nose.collector",
    tests_require=[
        "nose>=1.0",
        "mock>=1.0.1"
    ],
)
