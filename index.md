---
layout: default

introduction-content: |
  **CoilSnake** is the most powerful [mod making tool](https://en.wikipedia.org/wiki/Game_mod) for the game [*EarthBound*](https://en.wikipedia.org/wiki/EarthBound). CoilSnake has been used to create several original games in the *EarthBound* engine, as well as to translate *EarthBound*:

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
- name: Portuguese EB
  image: images/screenshots/eb-portuguese.png
  image-position-x: 0
  image-position-y: 10%
  url: http://www.earthboundbrasil.com/p/download.html
- name: French EB
  image: images/screenshots/eb-french.png
  image-position-x: 0
  image-position-y: 4%
  url: http://www.ultimate-consoles.fr/page/index.html/_/super-nintendo/les-news-snes/trad-earthbound-le-patch-fr-v11-r199

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

<section id="s_introduction">
  {{page.introduction-content | markdownify}}

  <div class="projects">
    {% for project in page.projects %}
      <div class="project_button"
           style="background-image: url('{{ project.image }}'); background-position: {{ project.image-position-x}} {{project.image-position-y}};">
        <a href="{{ project.url }}">
          <span>{{project.name}}</span>
        </a>
      </div>
    {% endfor %}
  </div>
</section>

<section id="s_download">
  {% capture download_section %}{% include download_section.md %}{% endcapture %}
  {{ download_section | markdownify }}
</section>

<section id="s_whatnow">
  {{page.whatnow-content | markdownify}}
</section>

<section id="s_contribute">
  <div class="topright"><iframe src="http://ghbtns.com/github-btn.html?user=kiij&amp;repo=CoilSnake&amp;type=watch&amp;count=true&amp;size=large" width="160" height="35" style="border: none;"> </iframe></div>
  {{page.contribute-content | markdownify}}
</section>
