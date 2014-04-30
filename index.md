---
layout: default
title: CoilSnake
version: 2.0
tagline: A program for modifying the EarthBound ROM.
featured-screenshot: images/screenshots/octocat-battle.png
short-description: |
  **CoilSnake** is the most powerful [mod making tool](https://en.wikipedia.org/wiki/Game_mod) for the game [*EarthBound*](https://en.wikipedia.org/wiki/EarthBound). CoilSnake has been used to create several entirely original games within the *EarthBound* engine:
projects:
- name: MOTHER Remake
  image: images/screenshots/mother-remake.png
  image-position-x: 0
  image-position-y: 20%
  url: http://forum.starmen.net/forum/Community/PKHack/Mother-Remake/page/1/
- name: Unearthed
  image: images/screenshots/unearthed.png
  image-position-x: 0
  image-position-y: 40%
  url: http://theworldissquare.com/unearthed/
- name: "Hallow's End"
  image: images/screenshots/hallows-end.png
  image-position-x: 0
  image-position-y: 20%
  url: http://hacks.lyros.net/portfolio/hallows-end/
- name: Holiday Hex
  image: images/screenshots/holiday-hex.png
  image-position-x: 0
  image-position-y: 35%
  url: http://hacks.lyros.net/portfolio/holiday-hex/
- name: EquestriaBound
  image: images/screenshots/equestriabound.png
  image-position-x: 0 
  image-position-y: 35% 
  url: http://forum.starmen.net/forum/Community/PKHack/EquestriaBound/page/1/ 

---

<span class="version">Latest Version: {{page.version}}</span>

## Installation 
    
On Windows, just [run the installer](#). On Linux, install from source:

    $ sudo apt-get install python-pip python-dev libyaml-dev python-tk \
                           g++ libboost-filesystem-dev
    $ git clone https://github.com/kiij/CoilSnake.git
    $ cd CoilSnake
    $ make
    $ sudo make install

## What now?

The [CoilSnake tutorial](https://github.com/kiij/CoilSnake/wiki/Tutorial) is the best place to get started.

## Contribute

* Fork the [github repository](https://github.com/kiij/CoilSnake).
* Add to the [wiki documentation](https://github.com/kiij/CoilSnake/wiki).
* Submit [issues or feature  requests](https://github.com/kiij/CoilSnake/issues).
* Show off your work on the [forum](http://forum.starmen.net/forum/Community/PKHack) or [IRC channel](irc://irc.thinstack.net/pkhax).
