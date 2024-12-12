#!/usr/bin/env python3

import platform
from setuptools import setup
from setuptools.extension import Extension

extra_compile_args = []

if platform.system() != "Windows":
    extra_compile_args.append("-std=c99")

setup(
    ext_modules=[
        Extension(
            "coilsnake.util.eb.native_comp",
            ["coilsnake/util/eb/native_comp.c", "coilsnake/util/eb/exhal/compress.c"],
            extra_compile_args=extra_compile_args,
        )
    ],
    test_suite="nose.collector",
    tests_require=[
        "nose>=1.0",
        "mock>=1.0.1"
    ],
)
