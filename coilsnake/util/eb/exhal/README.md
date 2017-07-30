# exhal / inhal
**HAL Laboratory NES/SNES/GB (de)compression tools**  
**(version 1.21)**  
by Devin Acker (Revenant), 2013-2015
https://github.com/devinacker

exhal and inhal are tools designed to decompress and recompress/insert data used by several NES, SNES and Game Boy games developed by HAL Laboratory. 

Due to the design of the original decompression algorithm (and hardware limitations), the size of a file to be compressed is limited to 64 kilobytes (65,536 bytes). Please note that depending on which system you are working with, the actual useful limit may be much smaller.

The compression routine used by inhal is very fast and capable of producing output which is smaller than that of HAL's original compressor.

Source code is available at https://github.com/devinacker and is released under the terms of the MIT license. See COPYING.txt for legal info. You are welcome to use compress.c in your own projects (if you do, I'd like to hear about it!)

**To use exhal (the decompressor):**  
exhal romfile offset outfile

**To insert compressed data into a ROM:**  
inhal [-fast] infile romfile offset

**To write compressed data to a new file:**  
inhal [-fast] -n infile outfile

Offsets can be specified in either hexadecimal (recommended) or decimal.

Using the -fast switch results in compression which is about 3 to 4 times faster, but with slightly larger output data. Use this if you don't care about data sizes being 100% identical to the original compressed data.

This is a list of games which are known to use the supported compression method, or are assumed to, based on a binary search of the games' ROMs:

* Adventures of Lolo (NES/GB)
* Adventures of Lolo 2 (NES)
* Adventures of Lolo 3 (NES)
* Alcahest (SNES) 
* Arcana / Card Master (SNES)
* EarthBound / Mother 2 (SNES)
* Ghostbusters II (GB)
* HAL's Hole in One Golf / Jumbo Ozaki no Hole in One (SNES)
* HyperZone (SNES)
* Itoi Shigesato no Bass Tsuri No. 1 (SNES)
* Kirby no KiraKira Kids (SNES)
* Kirby Super Star (SNES)
* Kirby's Adventure (NES)
* Kirby's Dream Course / Kirby Bowl (SNES)
* Kirby's Dream Land (GB)
* Kirby's Dream Land 2 (GB)
* Kirby's Dream Land 3 (SNES)
* Kirby's Pinball Land (GB)
* Kirby's Star Stacker / KiraKira Kids (GB)
* NES Open Tournament Golf (NES)
* New Ghostbusters II (NES)
* Othello World (SNES)
* Okamoto Ayako to Match Play Golf (SNES)
* Revenge of the Gator / 66 Hiki no Wani Daikoushin (GB)
* SimCity (SNES) [unused?]
* SimCity 2000 (SNES)
* Special Tee Shot (BS-X)
* Super Famicom Box BIOS (SNES)
* Trax / Totsugeki! Ponkotsu Tank (GB)
* Vegas Stakes (SNES/GB)

Also note, unfortunately, that exhal cannot automatically detect or locate compressed data. The included file "gamenotes.txt" contains an incomplete list of decompression routine addresses to make searching easier.

These tools were originally used in the development of my Kirby's Dream Course editor. I hope you find your own exciting use for them. (I'm not the only Kirby hacker in the West, right? *sob*)

## Contact me

* Email : d at revenant1.net
* IRC   : 
 * "devin"     on irc.badnik.net
 * "Revenant"  on irc.oftc.net
 * "Revenant`" on irc.synirc.net and irc.dal.net
* Forums:
 * http://jul.rustedlogic.net/profile.php?id=504
 * http://www.romhacking.net/forum/index.php?action=profile;u=10455

## Special thanks to

* andlabs for helping me make the list of supported games
* BMF54123 for naming the programs
* Tiiffi and Anthony J. Bentley for misc. build fixes
* You for downloading (and using?) my software