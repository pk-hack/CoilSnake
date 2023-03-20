---
layout: default

introduction-content: |
  **CoilSnake** is the most powerful [mod making tool](https://en.wikipedia.org/wiki/Game_mod) for the game [*EarthBound*](https://en.wikipedia.org/wiki/EarthBound). CoilSnake has been used to create several original games in the *EarthBound* engine, as well as to translate *EarthBound*:

projects:
- name: MOTHER Remake
  image: images/screenshots/mother-remake.png
  image-position-x: 0
  image-position-y: 20%
  url: https://forum.starmen.net/forum/Community/PKHack/Mother-Remake/
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
- name: Spanish EB
  image: images/screenshots/eb-spanish.png
  image-position-x: 0
  image-position-y: -15%
  url: https://forum.starmen.net/forum/Community/PKHack/EarthBound-Spanish-translation/
- name: Portuguese EB
  image: images/screenshots/eb-portuguese.png
  image-position-x: 0
  image-position-y: 10%
  url: http://www.earthboundbrasil.com/p/download.html

whatnow-content: |
  ## What now?

  The [CoilSnake tutorial](https://github.com/pk-hack/CoilSnake/wiki/Introduction) is the best place to get started.

contribute-content: |
  ## Contribute

  * Fork the [github repository](https://github.com/pk-hack/CoilSnake).
  * Add to the [wiki documentation](https://github.com/pk-hack/CoilSnake/wiki).
  * Submit [issues or feature  requests](https://github.com/pk-hack/CoilSnake/issues).
  * Show off your work on the [forum](http://forum.starmen.net/forum/Community/PKHack).

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
  <div class="topright"><iframe src="https://ghbtns.com/github-btn.html?user=pk-hack&amp;repo=CoilSnake&amp;type=watch&amp;count=true&amp;size=large" width="160" height="35" style="border: none;"> </iframe></div>
  {{page.contribute-content | markdownify}}
</section>
