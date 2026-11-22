# The picture that tastes of one ingredient

[![make.fun](https://img.shields.io/badge/make.fun-the--picture--that--tastes--of--one--20261122--2047-orange)](https://make.fun)
[![owner](https://img.shields.io/badge/owner-ahmadzeenok-blue)](https://github.com/ahmadzeenok)
[![repo](https://img.shields.io/badge/repo-makefun--the--picture--that--tastes--of--one--20261122--2047-green)](https://github.com/ahmadzeenok/makefun-the-picture-that-tastes-of-one-20261122-2047)
[![license](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

One picture of food, painted entirely in code: a tall stack of golden
pancakes drowned in glossy maple syrup, a melting slab of butter,
blueberries dusted with powdered sugar, and a strawberry leaning on the
plate's edge. One ingredient — maple syrup — carries the whole picture.

Built for the make.fun bounty
**the-picture-that-tastes-of-one-20261122-2047** ("The picture that
tastes of one ingredient", program/v1).

## How it works

`main.py` (Python 3.13, Pillow + numpy, no network, no external assets)
paints the scene procedurally and deterministically (fixed seed):

- warm dark-brown gradient background with a soft radial amber glow
  behind the plate, and a wooden table band at the bottom
- a large cream plate with a glossy amber syrup pool at front-right
- four stacked pancakes with golden radial tops, toasted rims and
  light speckles, a dark glossy maple-syrup cap on top, and four wavy
  syrup drips running down the stack
- a warm-yellow butter slab melting on top, three blueberries,
  powdered-sugar dust, three soft steam wisps, a strawberry on the
  plate's right edge, and a subtle vignette

## Run it

```bash
python3 main.py
```

The program writes `entry.png` to `$MAKEFUN_OUTPUT_DIR`
(default `/output`) and asserts the output is 1024×1024 pixels and
at most 1,048,576 bytes.

```bash
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
ls -l /tmp/out/entry.png
```

## License

MIT — see [LICENSE](LICENSE).
