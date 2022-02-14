## [CoilSnake](https://pk-hack.github.io/CoilSnake/)

![You engage the OctoCat.](https://pk-hack.github.io/CoilSnake/images/screenshots/octocat-battle.png)

**CoilSnake** is the most powerful [mod making tool](https://en.wikipedia.org/wiki/Game_mod) for the game
[*EarthBound*](https://en.wikipedia.org/wiki/EarthBound).
CoilSnake deconstructs the game's assets into individual text and PNG files, and then lets you "build" a new ROM
using modified assets.
Most of the game's data is editable by CoilSnake, making it possible to create entirely new games in the *EarthBound*
engine.

### Download

Download and usage instructions for Windows and Linux can be found on the
[CoilSnake website](https://pk-hack.github.io/CoilSnake/download.html).

### General Troubleshooting

* **I can't decompile the script**

  Make sure that you decompile a vanilla EarthBound ROM _first_, so that the assets get decompiled first, and then try to decompile the script. The ccscript folder won't get populated until you decompile the ROM first.
* **Fatal error detected: Failed to execute script gui**

  This issue is caused due to a corrupted CoilSnake preferences file (possibly caused by old version of CoilSnake being used before). To fix it, browse your user directory ("C:/Users/{your user name}" in Windows) and delete the file named ".coilsnake.yml". Then open CoilSnake again.
* **Some anti-virus softwares (Windows Defender, Avast, etc.) detect CoilSnake as a virus/Trojan/etc. Is CoilSnake safe to open?**

  CoilSnake is 100% safe to open in a Windows machine, as long as you are downloading it from the proper GitHub release page, or the PK Hack Forums release thread. Any other source outside of the specified ones in this repository is discouraged for downloading. If you still don't feel confident, comfortable or safe trying to open the CoilSnake executable, you can always follow the instructions in the Development file to compile and create an executable from source for yourself.

### Support or Contact

* Submit [issues or feature requests](https://github.com/pk-hack/CoilSnake/issues).
* Read the [CoilSnake tutorial](https://github.com/pk-hack/CoilSnake/wiki/Introduction).
* Visit the [forum](https://forum.starmen.net/forum/Community/PKHack).
* Join the [PK Hack Discord server](https://discord.gg/UHVw5Rp2e4).
