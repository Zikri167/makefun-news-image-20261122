# The World in One Day — Sunday 22 November 2026

[![make.fun](https://make.fun/badge.svg)](https://make.fun/)
[![competition](https://make.fun/c/news-image-20261122/badge.svg)](https://make.fun/c/news-image-20261122)

A procedural broadsheet summing up the world's news of Sunday
22 November 2026 in a single 1024x1024 image.

Lead stories: Iran's missile and drone strikes on US bases in
Bahrain; Russia's overnight barrage on Ukraine; the EU–Indonesia
trade deal signed after ten years of talks. Six more stories in the
grid (COP31 deadlock, the Peru quake, the 'El Chapo Isidro' arrest,
the FBI database hack, the Crimean Bridge strikes, the Baltic ship
attack) plus an IN BRIEF column.

## Run

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
```

Python 3.13, standard library only. No network, no clock, no
randomness: two runs write byte-identical PNGs.

`main.py` lays out the page and holds the day's copy. `draw.py`
holds the canvas, the 5x7 bitmap font, the PNG encoder and the
pictograms. Everything is drawn from code — no image assets.

## License

MIT. See LICENSE.
