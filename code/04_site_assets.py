"""Step 4. Map overlays and compact page data.

  map/lead.png         leading word of the smoothed survey answers (Web Mercator image overlay)
  map/share_<word>.png share of each word (transparent to full colour at 60% or more)
  work/site.json       compact data embedded in index.html

The overlays are drawn from the smoothed field only where at least 10 kernel-weighted answers are
nearby, so no single answer can be read from them.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from style import WORDS, COLOR  # noqa: E402
import words as W  # noqa: E402
import pandas as pd  # noqa: E402

os.makedirs(os.path.join(ROOT, "map"), exist_ok=True)
F = np.load(os.path.join(ROOT, "work", "fields.npz"))
P = F["P"].astype(np.float32)
mask = F["mask"]
top1 = F["top1"]
x0, y0, cell = float(F["x0"]), float(F["y0"]), float(F["cell"])
ny, nx = mask.shape
R = json.load(open(os.path.join(ROOT, "data", "results.json")))

# Web Mercator target grid
LON0, LON1, LAT0, LAT1 = -8.4, 2.0, 49.8, 59.6


def merc_y(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


Wd = 900
Hd = int(round(Wd * (merc_y(LAT1) - merc_y(LAT0)) / math.radians(LON1 - LON0)))
lons = LON0 + (np.arange(Wd) + 0.5) / Wd * (LON1 - LON0)
my = merc_y(LAT1) - (np.arange(Hd) + 0.5) / Hd * (merc_y(LAT1) - merc_y(LAT0))
lats = np.degrees(2 * np.arctan(np.exp(my)) - math.pi / 2)
LO, LA = np.meshgrid(lons, lats)
X, Y = Transformer.from_crs(4326, 27700, always_xy=True).transform(LO, LA)
ci = np.floor((X - x0) / cell).astype(int)
ri = np.floor((Y - y0) / cell).astype(int)
ok = (ci >= 0) & (ci < nx) & (ri >= 0) & (ri < ny)
ci2, ri2 = np.clip(ci, 0, nx - 1), np.clip(ri, 0, ny - 1)
m = ok & mask[ri2, ci2]


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


img = np.zeros((Hd, Wd, 4), dtype=np.uint8)
t = top1[ri2, ci2]
ts = np.take_along_axis(P[:, ri2, ci2], t[None], 0)[0]
for k, w in enumerate(WORDS):
    sel = m & (t == k)
    img[sel, :3] = rgb(COLOR[w])
    img[sel, 3] = (255 * (0.55 + 0.45 * np.clip((ts[sel] - 0.3) / 0.4, 0, 1))).astype(np.uint8)
Image.fromarray(img).save(os.path.join(ROOT, "map", "lead.png"), optimize=True)
for k, w in enumerate(WORDS[:-1]):
    im = np.zeros((Hd, Wd, 4), dtype=np.uint8)
    sh = P[k, ri2, ci2]
    im[m, :3] = rgb(COLOR[w])
    im[m, 3] = (255 * np.clip(sh[m] / 0.6, 0, 1) ** 0.8).astype(np.uint8)
    Image.fromarray(im).save(os.path.join(ROOT, "map", f"share_{w}.png"), optimize=True)

# lines
L = json.load(open(os.path.join(ROOT, "data", "roll_lines.geojson")))
lines = [[f["properties"]["kind"], f["properties"]["a"], f["properties"]["b"], f["geometry"]["coordinates"]] for f in L["features"]]
# hexes (published aggregates, n >= 10)
H = json.load(open(os.path.join(ROOT, "data", "survey_hexes.geojson")))
hexes = []
for f in H["features"]:
    p = f["properties"]
    ring = f["geometry"]["coordinates"][0][:-1]
    hexes.append([[[round(a[1], 3), round(a[0], 3)] for a in ring], p["n"], p["n_od"], p["n_dh"], WORDS.index(p["top"]),
                  [p[w] for w in WORDS], p["county"]])
# business names: kept roll and sandwich words with a location (open data: FSA OGL v3, OSM ODbL)
M = pd.read_csv(os.path.join(ROOT, "data", "roll_word_matches.csv"), keep_default_na=False)
K = M[(M.kept == 1) & M.word.isin(W.ROLL_WORDS + ["butty", "sarnie", "piece"])].copy()
K["key"] = K.name.str.lower().str.replace(r"[^a-z0-9]", "", regex=True) + "|" + K.county + "|" + K.word
K = K.sort_values("source").drop_duplicates("key")   # FSA first, then OSM duplicates dropped
K = K[K.lat != ""]
BW = ["roll", "bap", "cob", "batch", "barm", "ovenbottom", "stottie", "breadcake", "scuffler", "butty", "sarnie", "piece"]
biz = [[round(float(r.lat), 4), round(float(r.lon), 4), BW.index(r.word), r["name"][:60], r.source, 1 if r.placed == "own" else 0] for _, r in K.iterrows()]
site = {"R": R, "hexes": hexes, "lines": lines, "biz": biz, "bw": BW, "bounds": [[LAT0, LON0], [LAT1, LON1]]}
json.dump(site, open(os.path.join(ROOT, "work", "site.json"), "w"), separators=(",", ":"))
print("site.json", os.path.getsize(os.path.join(ROOT, "work", "site.json")) // 1024, "KB; lead.png", Wd, Hd, "biz", len(biz))
