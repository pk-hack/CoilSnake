---
layout: default
title: CoilSnake
version: 2.0

introduction-content: |
  **CoilSnake** is the most powerful [mod making tool](https://en.wikipedia.org/wiki/Game_mod) for the game [*EarthBound*](https://en.wikipedia.org/wiki/EarthBound). CoilSnake has been used to create several entirely original games using the *EarthBound* engine:

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

installation-content: |
  ## Installation

  On Windows, just [run the installer](#). On Linux, install from source:

      $ sudo apt-get install python-pip python-dev libyaml-dev python-tk \
                             g++ libboost-filesystem-dev
      $ git clone https://github.com/kiij/CoilSnake.git
      $ cd CoilSnake
      $ make 
      $ sudo make install

whatnow-content: |
  ## What now?

  The [CoilSnake tutorial](https://github.com/kiij/CoilSnake/wiki/Tutorial) is the best place to get started.

contribute-content: |
  ## Contribute

  * Fork the [github repository](https://github.com/kiij/CoilSnake).
  * Add to the [wiki documentation](https://github.com/kiij/CoilSnake/wiki).
  * Submit [issues or feature  requests](https://github.com/kiij/CoilSnake/issues).
  * Show off your work on the [forum](http://forum.starmen.net/forum/Community/PKHack) or [IRC channel](irc://irc.thinstack.net/pkhax).

---

<section id="introduction">
  {{page.introduction-content | markdownify}}

  <div class="pure-g-r">
    {% for project in page.projects %}
    <div class="pure-u-1-2">
      <div class="project">
        <div class="project_button"
             style="background-image: url('{{ project.image }}'); background-position: {{ project.image-position-x}} {{project.image-position-y}};">
          <a href="{{ project.url }}">
            <span>{{project.name}}</span>
          </a>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
</section>

<section id="installation">
  <span class="topright">Latest Version: {{page.version}}</span>
  {{page.installation-content | markdownify}}
</section>

<section id="whatnow">
  {{page.whatnow-content | markdownify}}
</section>

<section id="contribute">
  <div class="topright"><iframe src="http://ghbtns.com/github-btn.html?user=kiij&amp;repo=CoilSnake&amp;type=watch&amp;count=true&amp;size=large" width="160" height="35" style="border: none;"> </iframe></div>
  {{page.contribute-content | markdownify}}
</section>
