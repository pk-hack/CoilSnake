#! /usr/bin/env python

from distutils.core import setup

from coilsnake.ui import information


setup(name='CoilSnake',
      version=information.VERSION,
      description="A program for modifying the EarthBound ROM.",
      long_description=open("README.md").read(),
      url="http://kiij.github.io/CoilSnake",
      packages=["coilsnake", "coilsnake.ui", "coilsnake.tools", "coilsnake.modules", "coilsnake.modules.eb",
                "coilsnake.modules.eb0", "coilsnake.modules.smb"],
      package_data={
          'coilsnake': [
              'resources/*'
          ],
          'coilsnake.ui': [
              'resources/*'
          ],
          'coilsnake.modules': [
              'resources/ips/*/*'
          ],
          'coilsnake.modules.eb': [
              'resources/*'
          ]
      },
      entry_points={
          'console_scripts': [
              'coilsnake = coilsnake.ui.gui:main',
          ]
      },

      #windows=['CoilSnake.py'],
      #data_files=dataFiles,
      #zipfile=None,
      #options={"py2exe": {"includes": includeModuleList}}
)