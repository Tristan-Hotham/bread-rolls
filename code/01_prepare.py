"""Step 1. Business names: read every FSA food business and every named OSM bakery, cafe and fast
food outlet, find the bread roll and sandwich words in their names, place each business, and
assign it to a county.

Inputs (read in place, never copied):
  ../_data10/fsa_all_establishments.json.gz   FSA Food Hygiene Rating Scheme, all LAs (OGL v3)
  ../_data10/osm_uk_food_names.json.gz        OSM named bakeries, cafes, fast food (ODbL)
  ../how-roman-is-your-road/data/counties.geojson and data/ons/ltla.geojson (ONS boundaries, OGL v3)
Outputs:
  data/roll_word_matches.csv   one row per (business, word) match, with kept flag and exclusion reason
  data/counties.geojson        simplified county outlines used by the page (plus Northern Ireland)
  work/fsa_county_totals.json  all FSA businesses per county (the denominator)
  work/counties_full.pkl       full-resolution county geometries for step 2

Placing businesses: the FSA file gives coordinates for most businesses. When they are missing I
use the median coordinates of other businesses in the same postcode district, then the median of
the same local authority. Businesses with no postcode and no coordinates (mostly home caterers
and mobile traders) are placed at their local authority's median point.
"""
import gzip
import json
import os
import pickle
import re
import sys
from collections import Counter, defaultdict

import numpy as np
from shapely.geometry import Point, shape, mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HIST = os.path.dirname(ROOT)
sys.path.insert(0, HERE)
import words  # noqa: E402

os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)

# ------------------------------------------------------------------ counties
C = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "data", "counties.geojson")))
L = json.load(open(os.path.join(HIST, "how-roman-is-your-road", "data", "ons", "ltla.geojson")))
units = [(f["properties"]["county"], f["properties"]["nation"], shape(f["geometry"]).buffer(0)) for f in C["features"]]
ni = unary_union([shape(f["geometry"]).buffer(0) for f in L["features"] if f["properties"]["areacd"].startswith("N")])
units.append(("Northern Ireland", "Northern Ireland", ni))
names = [u[0] for u in units]
geoms = [u[2] for u in units]
tree = STRtree(geoms)
pickle.dump(units, open(os.path.join(ROOT, "work", "counties_full.pkl"), "wb"))


def county_of(lon, lat):
    p = Point(lon, lat)
    for i in tree.query(p):
        if geoms[i].contains(p):
            return names[i]
    i = tree.nearest(p)
    if geoms[i].distance(p) < 0.08:   # about 5 to 8 km: coastal points just off the outline
        return names[i]
    return ""


feats = []
for n, nat, g in units:
    s = g.simplify(0.006, preserve_topology=True)
    s = s if s.geom_type in ("Polygon", "MultiPolygon") else g
    gj = mapping(s)

    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 3), round(c[1], 3)]
    gj = {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}
    feats.append({"type": "Feature", "properties": {"county": n, "nation": nat}, "geometry": gj})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(ROOT, "data", "counties.geojson"), "w"), separators=(",", ":"))

# ------------------------------------------------------------------ FSA
PC = re.compile(r"^([A-Z]{1,2})([0-9][0-9A-Z]?)\s*([0-9][A-Z]{2})$")


def parse_pc(pc):
    pc = (pc or "").upper().strip()
    m = PC.match(pc.replace(" ", "")) if pc else None
    if not m:
        return "", ""
    return m.group(1), m.group(1) + m.group(2)


d = json.load(gzip.open(os.path.join(HIST, "_data10", "fsa_all_establishments.json.gz")))
rows = d["rows"]
dist_pts, la_pts = defaultdict(list), defaultdict(list)
parsed = []
for r in rows:
    area, dist = parse_pc(r[3])
    lat = float(r[4]) if r[4] not in ("", None) else None
    lon = float(r[5]) if r[5] not in ("", None) else None
    if lat is not None and not (49 < lat < 61.5 and -9 < lon < 2.5):
        lat = lon = None
    if lat is not None:
        if dist:
            dist_pts[dist].append((lon, lat))
        la_pts[r[6]].append((lon, lat))
    parsed.append((area, dist, lon, lat))
dist_med = {k: tuple(np.median(np.array(v), axis=0)) for k, v in dist_pts.items()}
la_med = {k: tuple(np.median(np.array(v), axis=0)) for k, v in la_pts.items()}

how = Counter()
county_tot = Counter()
county_cache = {}
fsa_place = []
for r, (area, dist, lon, lat) in zip(rows, parsed):
    if lat is not None:
        src = "own"
    elif dist in dist_med:
        lon, lat = dist_med[dist]; src = "district"
    elif r[6] in la_med:
        lon, lat = la_med[r[6]]; src = "la"
    else:
        src = "none"
    how[src] += 1
    cty = ""
    if src != "none":
        key = (round(lon, 3), round(lat, 3))
        if key not in county_cache:
            county_cache[key] = county_of(lon, lat)
        cty = county_cache[key]
    county_tot[cty] += 1
    fsa_place.append((lon, lat, src, cty, area))
print("FSA placement", dict(how))

out = []
for r, (lon, lat, src, cty, area) in zip(rows, fsa_place):
    for w, kept, why in words.classify(r[1]):
        out.append(dict(source="FSA", id=r[0], name=r[1], btype=r[2], postcode=r[3], pc_area=area, la=r[6],
                        lon=round(lon, 5) if lon is not None else "", lat=round(lat, 5) if lat is not None else "",
                        placed=src, county=cty, word=w, kept=int(kept), reason=why))

# ------------------------------------------------------------------ OSM
o = json.load(gzip.open(os.path.join(HIST, "_data10", "osm_uk_food_names.json.gz")))
osm_tot = Counter()
WKT = re.compile(r"POINT\(([-0-9.]+) ([-0-9.]+)\)")
for key in ("bakeries_tsv", "cafes_fastfood_tsv"):
    lines = o[key].strip().split("\n")[1:]
    for ln in lines:
        p = ln.split("\t")
        if len(p) < 5:
            continue
        osm = p[0].strip("<>").replace("https://www.openstreetmap.org/", "")
        kind = p[1].strip('"')
        nm = p[2].strip('"')
        m = WKT.search(p[4])
        if not m:
            continue
        lon, lat = float(m.group(1)), float(m.group(2))
        cty = county_of(lon, lat)
        osm_tot[(kind, cty)] += 1
        for w, kept, why in words.classify(nm):
            out.append(dict(source="OSM", id=osm, name=nm, btype=kind, postcode="", pc_area="", la="",
                            lon=round(lon, 5), lat=round(lat, 5), placed="own", county=cty, word=w, kept=int(kept), reason=why))

import csv  # noqa: E402
cols = ["source", "id", "name", "btype", "postcode", "pc_area", "la", "lon", "lat", "placed", "county", "word", "kept", "reason"]
with open(os.path.join(ROOT, "data", "roll_word_matches.csv"), "w", newline="", encoding="utf-8") as f:
    wr = csv.DictWriter(f, fieldnames=cols)
    wr.writeheader()
    for r in out:
        wr.writerow(r)
json.dump({"fsa_n": len(rows), "fsa_placement": dict(how), "fsa_by_county": dict(county_tot),
           "fsa_btypes": dict(Counter(r[2] for r in rows)),
           "osm_by_kind_county": {f"{k}|{c}": v for (k, c), v in osm_tot.items()},
           "osm_n": sum(osm_tot.values())},
          open(os.path.join(ROOT, "work", "fsa_county_totals.json"), "w"))
print("matches", len(out), "kept", sum(r["kept"] for r in out))
