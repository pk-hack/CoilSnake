#! /usr/bin/env python

from setuptools import setup

from coilsnake.ui import information


setup(name='CoilSnake',
      version=information.VERSION,
      description="A program for modifying the EarthBound ROM.",
      long_description=open("README.md").read(),
      url="http://kiij.github.io/CoilSnake",
      requires=['Pillow'],

      tests_require=['nose'],
      test_suite="nose.main"

      #windows=['CoilSnake.py'],
      #data_files=dataFiles,
      #zipfile=None,
      #options={"py2exe": {"includes": includeModuleList}}
)