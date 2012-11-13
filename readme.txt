CoilSnake Manual of Random Stuff

Tutorial: http://datacrystal.romhacking.net/wiki/CoilSnake_Tutorial

In General:
- All PNG files need to be Indexed PNGs. That is, they need to have a palette instead of being in RGB mode.
- If your PNG does not get saved correctly to the rom, it probably has too many unique tiles. Or maybe you are using too many different colors per 8x8 tile, if the problem is in a logo screen or town map.

CCScript:
- CCScript homepage: http://starmen.net/pkhack/ccscript/
- All script files must be placed in the "ccscript" subdirectory of the project, and must use the ".ccs" extension.
- You can specify a CCScript label in place of any pointer in a yml file. Use the "module_name.label_name" syntax.
  - Example: in items.yml, you can change "Help Text Pointer: $c53711" to "Help Text Pointer: myScript.myLabel" if you have a label called "myLabel" in ccscript/myScript.ccs
- Some other modules may overwrite changes made by your ccscripts if you're using them to do stuff besides text. I don't recommend using CCScript for anything other than text in conjunction with CoilSnake unless if you know what you're doing.

Battle Backgrounds:
- "Colour depth" in battle_bg.yml specifies the BPP to be used
- 4BPP bgs can have 16 unique colors including transparency. 2BPP bgs can have 4 unique colors including transparency.
- 2BPP bgs seem to be able to have more unique tiles than 4BPP bgs.
- 2BPP bgs must be layered with another 2BPP bg when displayed, otherwise glitchiness might happen. Use the enemy_groups.yml file to set up layering.

Enemies:
- Even though you can have 255 unique palettes for battle sprites, you can only have a certain number of unique palettes onscreen at once while playing the game due to hardware limitations.
- If you do not need an enemy to have a battle sprite, simply delete the corresponding image. You can also create new images for enemies that do not already have a battle sprite image.
- Valid battle sprite dimensions are 0x0, 32x32, 64x32, 32x64, 64x64, 128x64, and 128x128.

Map Enemy Groups:
- Probabilities for each subgroup must add up to 8.

Sprite Groups:
- The sprite palettes are specified in sprite_group_palettes.yml. Edit them there if you want to.
- Palettes in each sprite image must exactly match one of the palettes in sprite_group_palettes.yml
- Use the "show grid" function on your favorite image editing software to make editing the PNGs easier. Use a grid-size of 8x8.
- "Swim Flags" determine whether a sprite will sink or not when in Deep Darkness water. True = don't sink at all. This is used for present boxes, Krakens, etc.
- Remember to change the "Length" attribute appropriately for the Sprite Group you're editing in sprite_groups.yml

Logos:
- The first color of the company logo image's palette will be used as the background
- Only the graphics from GasStation1.png will be used. GasStation2.png and GasStation3.png are only used for their palette.

Window Graphics:
- The Windows2 pngs are the window borders used for flavored palettes. Windows1 contains the borders used for "Plain" flavor.
- Only graphical changes from Windows1_0.png and Windows2_0.png are saved to the rom.
  - The other PNGs are only to be used for editing palette colors.
- Each flavor has 8 palettes of 4 colors. Total 32 colors. These colors are all in the palette of the Windows1 pngs.
  - The palette of Windows2 is the same as the last palette of Windows1. The Windows2 palette will override Windows1's last palette when written the rom.

PSI Abilities:
- Last entry must have psi name of 0
