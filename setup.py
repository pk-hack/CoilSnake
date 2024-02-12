#!/usr/bin/env python

import os
import platform
from setuptools import setup, find_packages
from setuptools.extension import Extension

extra_compile_args = []

if platform.system() != "Windows":
    extra_compile_args = ["-std=c99"]

install_requires = [
    "Pillow>=3.0.0",
    "PyYAML>=3.11",
    "CCScriptWriter>=1.2",
    "ccscript>=1.500"
]

if platform.system() == "Darwin":
    install_requires.append("pyobjc-framework-Cocoa")

setup(
    name="coilsnake",
    version="4.2",
    description="CoilSnake",
    url="https://pk-hack.github.io/CoilSnake",
    packages=find_packages(),
    include_package_data=True,

    install_requires=install_requires,
    dependency_links=[
        "https://github.com/Lyrositor/CCScriptWriter/tarball/master#egg=CCScriptWriter-1.2",
        "https://github.com/charasyn/ccscript_legacy/archive/refs/tags/v1.500.tar.gz#egg=ccscript-1.500"
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
