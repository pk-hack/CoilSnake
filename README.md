CoilSnake
=========

CoilSnake is a modular ROM hacking tool. It provides a layer of abstraction and protection to ROM hacking by allowing the user to export a ROM's data to a CoilSnake project, using the relevant CoilSnake modules for each individual set of data depending on the game being read. That CoilSnake project may then be edited with external utilities. At the end, the user can later compile a CoilSnake project into a fresh ROM using CoilSnake. Of course, the process can also be reversed. In this way, the user avoids the all too common scenario in ROM hacking of one losing all of his work after making a single mistake or a utility failing, since all of his changes were stored in the ROM itself and can not easily be copied into another ROM. In addition, collaborative work becomes much, much easier.

How To Use 
----------

Examples:

Use the GUI frontend with CCScript support

    ./CoilSnakeGUI.py

Import from ROM to CoilSnake project:

    ./CoilSnake.py EB.smc MyProject/MyProject.csproj

Compile CoilSnake project into a ROM:

    ./CoilSnake.py --cleanrom EB-clean.smc MyProject/MyProject.csproj EB-new.smc

