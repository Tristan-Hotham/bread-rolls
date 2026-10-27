"""Step 3. The main analysis: the two dialect surveys, the smoothed bread roll lines, the checks
against YouGov and Wikipedia, the age gradient, and the business names.

The survey points (Our Dialects; Dialect and Heritage Project) are read in place from
../_data10/ and are NEVER written out. Only aggregates are published: hexagons, counties and
smoothed lines, and a hexagon or county is published only when it holds at least 10 answers.

Outputs: data/results.json, data/survey_hexes.geojson, data/survey_counties.csv,
data/roll_lines.geojson, data/business_counties.csv, work/site.json
"""
import json
import math
import os
import pickle
import re
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy import ndimage
from scipy.stats import spearmanr, pearsonr, binomtest
from shapely.geometry import Point, Polygon, LineString, mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree
from skimage import measure
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HIST = os.path.dirname(ROOT)
sys.path.insert(0, HERE)
import words  # noqa: E402

TO_BNG = Transformer.from_crs(4326, 27700, always_xy=True)
TO_LL = Transformer.from_crs(27700, 4326, always_xy=True)
MIN_N = 10          # publication threshold for any aggregate cell
R = {}

# ------------------------------------------------------------------ counties
units = pickle.load(open(os.path.join(ROOT, "work", "counties_full.pkl"), "rb"))
cnames = [u[0] for u in units]
cnation = {u[0]: u[1] for u in units}
cgeoms = [u[2] for u in units]
ctree = STRtree(cgeoms)


def county_of(lon, lat):
    p = Point(lon, lat)
    for i in ctree.query(p):
        if cgeoms[i].contains(p):
            return cnames[i]
    i = ctree.nearest(p)
    return cnames[i] if cgeoms[i].distance(p) < 0.05 else ""


# ------------------------------------------------------------------ surveys
OD_MAP = {"roll": "roll", "bun": "bun", "bap": "bap", "barm": "barm", "cob": "cob", "tea cake": "teacake",
          "muffin": "muffin", "bread cake": "breadcake", "batch": "batch"}
DH_MAP = {"bread roll": "roll", "roll": "roll", "bun": "bun", "bap": "bap", "cob": "cob", "breadcake": "breadcake",
          "barm": "barm", "batch": "batch", "something else": "other"}
od = json.load(open(os.path.join(HIST, "_data10", "ourdialects_bread_points.json")))
dh = json.load(open(os.path.join(HIST, "_data10", "dialectheritage_roll_points.json")))
rows = []
for lat, lon, w in od["rows"]:
    rows.append(("OD", lat, lon, OD_MAP[re.sub(r"\s*\(.*\)$", "", w)], ""))
for lat, lon, w, age in dh["rows"]:
    rows.append(("DH", lat, lon, DH_MAP[w], age.replace("Age:", "").strip()))
S = pd.DataFrame(rows, columns=["src", "lat", "lon", "word", "age"])
S["x"], S["y"] = TO_BNG.transform(S.lon.values, S.lat.values)
cache = {}
S["county"] = [cache.setdefault((round(a, 3), round(b, 3)), county_of(b, a)) for a, b in zip(S.lat, S.lon)]
S["inside"] = S.county != ""
R["survey"] = {
    "od_n": int((S.src == "OD").sum()), "dh_n": int((S.src == "DH").sum()), "n": int(len(S)),
    "od_inside": int(((S.src == "OD") & S.inside).sum()), "dh_inside": int(((S.src == "DH") & S.inside).sum()),
    "dh_raw": dict(Counter(w for _, _, w, _ in dh["rows"])),
    "od_raw": {OD_MAP[re.sub(r"\s*\(.*\)$", "", k)]: v for k, v in Counter(w for _, _, w in od["rows"]).items()},
}
R["survey"]["inside_n"] = R["survey"]["od_inside"] + R["survey"]["dh_inside"]
R["survey"]["outside_n"] = R["survey"]["n"] - R["survey"]["inside_n"]
S = S[S.inside].reset_index(drop=True)

WORDS = ["roll", "bun", "bap", "barm", "cob", "breadcake", "teacake", "muffin", "batch", "other"]
LABEL = {"roll": "roll", "bun": "bun", "bap": "bap", "barm": "barm", "cob": "cob", "breadcake": "breadcake",
         "teacake": "teacake", "muffin": "muffin", "batch": "batch", "other": "something else"}
for src in ("OD", "DH", "ALL"):
    s = S if src == "ALL" else S[S.src == src]
    vc = s.word.value_counts()
    R["survey"][f"share_{src}"] = {w: float(vc.get(w, 0) / len(s)) for w in WORDS}
    R["survey"][f"count_{src}"] = {w: int(vc.get(w, 0)) for w in WORDS}
R["survey"]["by_nation"] = {}
for nat in ["England", "Scotland", "Wales", "Northern Ireland"]:
    s = S[S.county.map(cnation) == nat]
    vc = s.word.value_counts()
    R["survey"]["by_nation"][nat] = {"n": int(len(s)), "n_od": int((s.src == "OD").sum()), "n_dh": int((s.src == "DH").sum()),
                                     "share": {w: float(vc.get(w, 0) / max(1, len(s))) for w in WORDS}}

# ------------------------------------------------------------------ hexagons (published aggregates)
HEX = 20000.0   # distance across flats, metres


def hex_index(x, y, a=HEX):
    # pointy-top axial coordinates
    size = a / math.sqrt(3)
    q = (math.sqrt(3) / 3 * x - 1 / 3 * y) / size
    r = (2 / 3 * y) / size
    # cube round
    cx, cz = q, r
    cy = -cx - cz
    rx, ry, rz = round(cx), round(cy), round(cz)
    dx, dy, dz = abs(rx - cx), abs(ry - cy), abs(rz - cz)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return int(rx), int(rz)


def hex_poly(q, r, a=HEX):
    size = a / math.sqrt(3)
    cx = size * math.sqrt(3) * (q + r / 2)
    cy = size * 1.5 * r
    pts = [(cx + size * math.cos(math.radians(60 * i + 30)), cy + size * math.sin(math.radians(60 * i + 30))) for i in range(6)]
    return cx, cy, pts


S["hex"] = [hex_index(x, y) for x, y in zip(S.x, S.y)]
hex_feats = []
hex_rows = []
for h, g in S.groupby("hex"):
    if len(g) < MIN_N:
        continue
    cx, cy, pts = hex_poly(*h)
    lon, lat = TO_LL.transform([p[0] for p in pts], [p[1] for p in pts])
    clon, clat = TO_LL.transform(cx, cy)
    vc = g.word.value_counts()
    cnt = {w: int(vc.get(w, 0)) for w in WORDS}
    top = max(WORDS, key=lambda w: cnt[w])
    n_od, n_dh = int((g.src == "OD").sum()), int((g.src == "DH").sum())
    props = {"n": int(len(g)), "n_od": n_od, "n_dh": n_dh, "top": top, "top_share": round(cnt[top] / len(g), 3),
             "county": Counter(g.county).most_common(1)[0][0], **cnt}
    hex_feats.append({"type": "Feature", "properties": props,
                      "geometry": {"type": "Polygon", "coordinates": [[[round(a, 4), round(b, 4)] for a, b in zip(list(lon) + [lon[0]], list(lat) + [lat[0]])]]}})
    hex_rows.append(dict(q=h[0], r=h[1], lon=round(clon, 4), lat=round(clat, 4), **props))
json.dump({"type": "FeatureCollection", "features": hex_feats}, open(os.path.join(ROOT, "data", "survey_hexes.geojson"), "w"), separators=(",", ":"))
HX = pd.DataFrame(hex_rows)
all_hex = S.groupby("hex").size()
R["hex"] = {"across_km": HEX / 1000, "n_hex_any": int(len(all_hex)), "n_hex_published": int(len(HX)),
            "answers_in_published": int(HX.n.sum()), "share_answers_published": float(HX.n.sum() / len(S)),
            "top_counts": {w: int((HX.top == w).sum()) for w in WORDS}, "median_n": float(HX.n.median())}

# ------------------------------------------------------------------ counties
crow = []
for c, g in S.groupby("county"):
    d = {"county": c, "nation": cnation[c], "n": int(len(g))}
    for src in ("OD", "DH"):
        gg = g[g.src == src]
        d[f"n_{src.lower()}"] = int(len(gg))
        vc = gg.word.value_counts()
        for w in WORDS:
            d[f"{src.lower()}_{w}"] = round(vc.get(w, 0) / len(gg), 4) if len(gg) >= MIN_N else None
    vc = g.word.value_counts()
    for w in WORDS:
        d[f"all_{w}"] = round(vc.get(w, 0) / len(g), 4) if len(g) >= MIN_N else None
    d["top"] = max(WORDS, key=lambda w: vc.get(w, 0)) if len(g) >= MIN_N else ""
    d["top_od"] = max(WORDS, key=lambda w: d[f"od_{w}"] or 0) if d["n_od"] >= MIN_N else ""
    d["top_dh"] = max(WORDS, key=lambda w: d[f"dh_{w}"] or 0) if d["n_dh"] >= MIN_N else ""
    crow.append(d)
CT = pd.DataFrame(crow).sort_values("county")
CT.to_csv(os.path.join(ROOT, "data", "survey_counties.csv"), index=False)
R["counties"] = {"n_published": int((CT.n >= MIN_N).sum()), "n_total": int(len(CT)),
                 "top_counts": dict(Counter(CT[CT.n >= MIN_N].top))}

# ------------------------------------------------------------------ smoothing and lines
CELL = 2000.0
x0, x1 = S.x.min() - 60000, S.x.max() + 60000
y0, y1 = S.y.min() - 60000, S.y.max() + 60000
nx, ny = int((x1 - x0) // CELL) + 1, int((y1 - y0) // CELL) + 1
ix = ((S.x - x0) // CELL).astype(int).values
iy = ((S.y - y0) // CELL).astype(int).values
wid = S.word.map({w: i for i, w in enumerate(WORDS)}).values
counts = np.zeros((len(WORDS), ny, nx))
np.add.at(counts, (wid, iy, ix), 1)
prior = np.array([R["survey"]["share_ALL"][w] for w in WORDS])
ALPHA = 1.0


def smooth(h_km):
    sig = h_km * 1000 / CELL
    # scaled so that each answer has weight 1 at its own spot and exp(-d^2 / 2h^2) at distance d
    K = np.stack([ndimage.gaussian_filter(counts[i], sig, mode="constant", truncate=3.0) for i in range(len(WORDS))]) * (2 * math.pi * sig ** 2)
    return K, ndimage.gaussian_filter(np.pad(np.ones((1, 1)), 0), 0)  # second value unused


def self_weight(h_km):
    sig = h_km * 1000 / CELL
    imp = np.zeros((121, 121)); imp[60, 60] = 1
    return ndimage.gaussian_filter(imp, sig, mode="constant", truncate=3.0)[60, 60] * (2 * math.pi * sig ** 2)


bw = {}
for h in [4, 6, 8, 10, 12, 16, 20, 24, 32]:
    K, _ = smooth(h)
    sw = self_weight(h)
    tot = K.sum(0)
    # leave one 2 km cell out: drop every answer in the same cell, not just the answer itself,
    # so that neighbours in the same street or village do not vouch for each other
    k_own = K[wid, iy, ix] - sw * counts[wid, iy, ix]
    t_own = tot[iy, ix] - sw * counts.sum(0)[iy, ix]
    p = (k_own + ALPHA * prior[wid]) / (t_own + ALPHA)
    bw[h] = float(np.log(p).mean())
cv_best = max(bw, key=bw.get)
# The kernel width is the one that best predicts each answer from the answers around it
# (leave-one-cell-out). I also report how often the leading word at each answer's spot changes
# when the width is halved or doubled.
best_h = cv_best
dom_at = {}
for h in (best_h / 2, best_h, best_h * 2):
    Kh, _ = smooth(h)
    dom_at[h] = Kh[:, iy, ix].argmax(0)
R["smoothing"] = {"cell_km": CELL / 1000, "candidates_km": list(bw.keys()), "loglik": bw, "cv_best_km": cv_best,
                  "bandwidth_km": best_h, "alpha": ALPHA,
                  "same_lead_half": float((dom_at[best_h / 2] == dom_at[best_h]).mean()), "same_lead_double": float((dom_at[best_h * 2] == dom_at[best_h]).mean())}
# Adaptive width: the cross-validated width where answers are dense, widened in steps where they
# are sparse until at least MIN_N kernel-weighted answers are nearby (each answer counts 1 at its
# own spot and exp(-d^2 / 2h^2) at distance d).
STEPS = [best_h] + [h for h in (12, 16, 24, 32) if h > best_h]
K = np.zeros((len(WORDS), ny, nx))
used_h = np.full((ny, nx), np.nan)
eff_n = np.zeros((ny, nx))
for h in STEPS:
    Kh, _ = smooth(h)
    th = Kh.sum(0)
    take = np.isnan(used_h) & (th >= MIN_N)
    K[:, take] = Kh[:, take]
    eff_n[take] = th[take]
    used_h[take] = h
tot = K.sum(0)
P = (K + ALPHA * prior[:, None, None]) / (tot + ALPHA)[None]
R["smoothing"]["steps_km"] = STEPS
# land mask from the county outlines
land = unary_union(cgeoms).buffer(0.01)
from shapely import contains_xy  # noqa: E402
gx = x0 + (np.arange(nx) + 0.5) * CELL
gy = y0 + (np.arange(ny) + 0.5) * CELL
GX, GY = np.meshgrid(gx, gy)
GLON, GLAT = TO_LL.transform(GX, GY)
on_land = contains_xy(land, GLON, GLAT)
mask = on_land & (eff_n >= MIN_N)
R["smoothing"]["share_masked_land_by_width"] = {str(h): float((mask & (used_h == h)).sum() / max(1, mask.sum())) for h in STEPS}
order = np.argsort(-P, axis=0)
top1, top2 = order[0], order[1]
R["smoothing"]["masked_share_of_land"] = float(mask.sum() / on_land.sum())
dom_area = {w: float(((top1 == i) & mask).sum() * (CELL / 1000) ** 2) for i, w in enumerate(WORDS)}
R["smoothing"]["dominant_area_km2"] = dom_area
R["smoothing"]["covered_area_km2"] = float(mask.sum() * (CELL / 1000) ** 2)


def grid_to_ll(cs):
    xs = x0 + (cs[:, 1] + 0.5) * CELL
    ys = y0 + (cs[:, 0] + 0.5) * CELL
    return TO_LL.transform(xs, ys), xs, ys


line_feats = []
lens = {}


def add_lines(field, level, keep, kind, a, b):
    total = 0.0
    for c in measure.find_contours(field, level):
        ri = np.clip(np.round(c[:, 0]).astype(int), 0, ny - 1)
        ci = np.clip(np.round(c[:, 1]).astype(int), 0, nx - 1)
        ok = keep[ri, ci]
        # split into runs where ok
        run = []
        for j in range(len(c) + 1):
            if j < len(c) and ok[j]:
                run.append(c[j])
            else:
                if len(run) >= 4:
                    arr = np.array(run)
                    (lon, lat), xs, ys = grid_to_ll(arr)
                    ls = LineString(list(zip(xs, ys))).simplify(1500)
                    if ls.length >= 15000:
                        X, Y = zip(*ls.coords)
                        lo, la = TO_LL.transform(X, Y)
                        total += ls.length
                        line_feats.append({"type": "Feature", "properties": {"kind": kind, "a": a, "b": b, "km": round(ls.length / 1000, 1)},
                                           "geometry": {"type": "LineString", "coordinates": [[round(p, 4), round(q, 4)] for p, q in zip(lo, la)]}})
                run = []
    return total / 1000


# 1. word boundaries: where the leading word changes
for i in range(len(WORDS)):
    for j in range(i + 1, len(WORDS)):
        keep = mask & (((top1 == i) & (top2 == j)) | ((top1 == j) & (top2 == i)))
        if keep.sum() < 5:
            continue
        L = add_lines(P[i] - P[j], 0.0, keep, "boundary", WORDS[i], WORDS[j])
        if L > 0:
            lens[f"{WORDS[i]}|{WORDS[j]}"] = round(L, 1)
# 2. the roll line: where roll falls below half of all answers
roll_i = WORDS.index("roll")
lens["roll_half"] = round(add_lines(P[roll_i], 0.5, mask, "roll_half", "roll", "rest"), 1)
R["lines"] = {"length_km": lens}
json.dump({"type": "FeatureCollection", "features": line_feats}, open(os.path.join(ROOT, "data", "roll_lines.geojson"), "w"), separators=(",", ":"))

# roll majority share of people? Use the answers themselves: share of answers in cells where roll > 50%
pr_at = P[roll_i][iy, ix]
R["lines"]["share_answers_roll_majority"] = float((pr_at >= 0.5).mean())
R["lines"]["share_answers_roll_majority_by_nation"] = {nat: float((pr_at[(S.county.map(cnation) == nat).values] >= 0.5).mean())
                                                       for nat in ["England", "Scotland", "Wales", "Northern Ireland"]}
# latitude profile of the roll share in England: mean P(roll) by 50 km band of northing, on masked land
eng = contains_xy(unary_union([g for n, nat, g in units if nat == "England"]).buffer(0.01), GLON, GLAT)
prof = []
for yb in range(0, 700000, 50000):
    sel = mask & eng & (GY >= yb) & (GY < yb + 50000)
    if sel.sum() > 20:
        prof.append({"northing_km": yb / 1000 + 25, "lat": float(np.median(GLAT[sel])), "roll": float(P[roll_i][sel].mean()),
                     **{w: float(P[k][sel].mean()) for k, w in enumerate(WORDS) if w != "roll"}})
R["lines"]["england_profile"] = prof

# full-resolution fields for the page overlays and figures (kept in work/, not published as data)
np.savez_compressed(os.path.join(ROOT, "work", "fields.npz"), P=P.astype(np.float16), mask=mask, top1=top1, x0=x0, y0=y0,
                    cell=CELL, words=np.array(WORDS))

# ------------------------------------------------------------------ the two surveys against each other
both = CT[(CT.n_od >= 30) & (CT.n_dh >= 30)].copy()
# harmonise: Our Dialects teacake and muffin are not options in the Dialect and Heritage question
for src in ("od", "dh"):
    pass
comp = {}
for w in ["roll", "bun", "bap", "barm", "cob", "breadcake", "batch"]:
    a, b = both[f"od_{w}"].astype(float), both[f"dh_{w}"].astype(float)
    r, p = pearsonr(a, b)
    comp[w] = {"r": float(r), "p": float(p), "mean_abs_diff": float((a - b).abs().mean())}


def top_h(row, src):
    sh = {w: row[f"{src}_{w}"] for w in ["roll", "bun", "bap", "barm", "cob", "breadcake", "batch"]}
    if src == "od":
        sh["other"] = (row["od_teacake"] or 0) + (row["od_muffin"] or 0)
    else:
        sh["other"] = row["dh_other"]
    return max(sh, key=sh.get)


both["top_od_h"] = [top_h(r, "od") for _, r in both.iterrows()]
both["top_dh_h"] = [top_h(r, "dh") for _, r in both.iterrows()]
agree = (both.top_od_h == both.top_dh_h)
R["agreement"] = {"n_counties": int(len(both)), "min_n": 30, "by_word": comp,
                  "top_agree": int(agree.sum()), "top_agree_share": float(agree.mean()),
                  "disagree": [{"county": r.county, "od": r.top_od_h, "dh": r.top_dh_h, "n_od": int(r.n_od), "n_dh": int(r.n_dh)}
                               for _, r in both[~agree].iterrows()],
                  "scatter": [{"county": r.county, **{f"od_{w}": r[f"od_{w}"] for w in ["roll", "bun", "bap", "barm", "cob", "breadcake"]},
                               **{f"dh_{w}": r[f"dh_{w}"] for w in ["roll", "bun", "bap", "barm", "cob", "breadcake"]}, "n_od": int(r.n_od), "n_dh": int(r.n_dh)}
                              for _, r in both.iterrows()]}
# national: Dialect and Heritage splits "bread roll" and "roll"
R["survey"]["dh_bread_roll"] = int(R["survey"]["dh_raw"].get("bread roll", 0))
R["survey"]["dh_roll_only"] = int(R["survey"]["dh_raw"].get("roll", 0))

# ------------------------------------------------------------------ YouGov county statements
YG = [  # word, county, low, high (percent), YouGov statement
    ("cob", "Leicestershire", 50, 100, "majority"), ("cob", "Nottinghamshire", 50, 100, "majority"), ("cob", "Derbyshire", 50, 100, "majority"),
    ("cob", "West Midlands", 20, 29, "20 to 29%"), ("cob", "Staffordshire", 10, 19, "10 to 19%"), ("cob", "Worcestershire", 10, 19, "10 to 19%"),
    ("bun", "Durham", 50, 100, "majority"), ("bun", "Tyne and Wear", 50, 100, "majority"), ("bun", "Northumberland", 50, 100, "majority"),
    ("bun", "North Yorkshire", 30, 39, "30 to 39%"), ("bun", "Cumbria", 20, 29, "20 to 29%"), ("bun", "Lincolnshire", 10, 19, "10 to 19%"),
    ("bun", "Merseyside", 10, 19, "10 to 19%"), ("bun", "East Riding of Yorkshire", 10, 19, "10 to 19%"),
    ("barm", "Greater Manchester", 30, 39, "30 to 39%, most common"), ("barm", "Lancashire", 30, 39, "30 to 39%"),
    ("barm", "Merseyside", 20, 29, "20 to 29%, joint first"), ("barm", "Cheshire", 20, 29, "20 to 29%"),
    ("bap", "Staffordshire", 20, 29, "20 to 29%"), ("bap", "Cheshire", 20, 29, "20 to 29%"), ("bap", "Shropshire", 20, 29, "20 to 29%"),
    ("bap", "Cornwall", 10, 19, "10 to 19%"), ("bap", "Devon", 10, 19, "10 to 19%"), ("bap", "West Midlands", 10, 19, "10 to 19%"),
    ("muffin", "Greater Manchester", 20, 29, "20 to 29%"),
    ("teacake", "West Yorkshire", 30, 39, "30 to 39%, second"), ("teacake", "Lancashire", 10, 19, "10 to 19%"), ("teacake", "Cumbria", 10, 19, "10 to 19%"),
    ("batch", "Warwickshire", 20, 29, "20 to 29%, second"), ("batch", "Merseyside", 10, 19, "10 to 19%"),
    ("breadcake", "East Riding of Yorkshire", 20, 29, "something else 20 to 29%"), ("breadcake", "South Yorkshire", 20, 29, "something else 20 to 29%"),
]
yg = []
CTi = CT.set_index("county")
for w, c, lo, hi, txt in YG:
    row = CTi.loc[c]
    vals = {}
    for src in ("od", "dh"):
        v = row[f"{src}_{w}"] if f"{src}_{w}" in row else None
        if src == "dh" and w in ("teacake", "muffin"):
            v = None   # not an option in the Dialect and Heritage question
        vals[src] = None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)

    def verdict(v):
        if v is None:
            return "n/a"
        p = v * 100
        if lo - 0.5 <= p <= hi + 0.5:
            return "within"
        gap = lo - p if p < lo else p - hi
        return "close" if gap <= 10 else ("higher" if p > hi else "lower")
    yg.append({"word": w, "county": c, "yougov": txt, "lo": lo, "hi": hi, "od": vals["od"], "dh": vals["dh"],
               "n_od": int(row.n_od), "n_dh": int(row.n_dh), "v_od": verdict(vals["od"]), "v_dh": verdict(vals["dh"])})
R["yougov"] = {"rows": yg, "n_statements": len(yg)}
for src in ("od", "dh"):
    v = Counter(r[f"v_{src}"] for r in yg)
    R["yougov"][f"verdicts_{src}"] = dict(v)
R["foodhub"] = {"chip_butty": 58, "chip_roll": 11, "chip_sandwich": 6, "chip_bap": 5.75, "chip_barm": 4.85, "chip_cob": 4,
                "note": "Foodhub app survey reported by the Yorkshire Post, 11 Sep 2020; sample size not published"}
R["yougov"]["england"] = {"roll": 52, "bun": 10, "cob": 8, "barm": 6, "bap": 6, "teacake": 4, "muffin": 3, "batch": 2, "other": 3}

# ------------------------------------------------------------------ age (Dialect and Heritage only)
AGEORD = ["under 11", "12-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75-84", "85 and over"]
AGEGRP = {"under 11": "Under 25", "12-17": "Under 25", "18-24": "Under 25", "25-34": "25 to 44", "35-44": "25 to 44",
          "45-54": "45 to 64", "55-64": "45 to 64", "65-74": "65 and over", "75-84": "65 and over", "85 and over": "65 and over"}
MID = {"under 11": 8, "12-17": 15, "18-24": 21, "25-34": 30, "35-44": 40, "45-54": 50, "55-64": 60, "65-74": 70, "75-84": 80, "85 and over": 88}
D = S[(S.src == "DH") & S.age.isin(AGEORD)].copy()
D["grp"] = D.age.map(AGEGRP)
D["mid"] = D.age.map(MID)
R["age"] = {"n_with_age": int(len(D)), "n_dh_inside": int((S.src == "DH").sum())}
od_c = CT[CT.n_od >= 30]
cob_zone = od_c[od_c.top_od == "cob"].county.tolist()
batch_zone = od_c[(od_c.od_batch.astype(float) >= 0.04)].county.tolist()
barm_zone = od_c[od_c.top_od == "barm"].county.tolist()
bun_zone = od_c[od_c.top_od == "bun"].county.tolist()
bap_zone = od_c[od_c.top_od == "bap"].county.tolist()
zones = {"cob": cob_zone, "batch": batch_zone, "barm": barm_zone, "bun": bun_zone, "bap": bap_zone, "roll": None}
GRPS = ["Under 25", "25 to 44", "45 to 64", "65 and over"]
for w, z in zones.items():
    sub_d = D if z is None else D[D.county.isin(z)]
    out = {"zone": z, "n": int(len(sub_d)), "groups": []}
    for g in GRPS:
        s = sub_d[sub_d.grp == g]
        k = int((s.word == w).sum())
        n = int(len(s))
        lo, hi = (binomtest(k, n).proportion_ci(0.95) if n else (0, 0))
        out["groups"].append({"group": g, "n": n, "k": k, "share": k / n if n else None, "lo": float(lo), "hi": float(hi)})
    y = (sub_d.word == w).astype(int).values
    X = sm.add_constant((sub_d.mid.values - 45) / 10.0)
    try:
        m = sm.Logit(y, X).fit(disp=0)
        out["or_per_decade"] = float(np.exp(m.params[1]))
        ci = np.exp(m.conf_int()[1])
        out["or_lo"], out["or_hi"] = float(ci[0]), float(ci[1])
        out["p"] = float(m.pvalues[1])
    except Exception as e:  # noqa: BLE001
        out["or_per_decade"] = None
    R["age"][w] = out

# ------------------------------------------------------------------ Wikipedia statements
WIKI = [
    ("barm", "Barm cake / List of bread rolls", "North West England: Liverpool, Manchester, South and West Lancashire",
     ["Merseyside", "Greater Manchester", "Lancashire"]),
    ("batch", "List of bread rolls", "Warwickshire and Cheshire, especially Coventry and the Wirral",
     ["Warwickshire", "West Midlands", "Cheshire", "Merseyside"]),
    ("breadcake", "List of bread rolls", "Yorkshire, and Annesley in north Nottinghamshire",
     ["West Yorkshire", "South Yorkshire", "North Yorkshire", "East Riding of Yorkshire", "Nottinghamshire"]),
    ("cob", "List of bread rolls", "the English Midlands",
     ["Derbyshire", "Nottinghamshire", "Leicestershire", "Rutland", "Lincolnshire", "Northamptonshire", "West Midlands", "Staffordshire",
      "Warwickshire", "Worcestershire", "Shropshire", "Herefordshire"]),
    ("teacake", "Teacake", "a plain roll in East Lancashire, the West Riding of Yorkshire and Cumbria",
     ["Lancashire", "West Yorkshire", "Cumbria"]),
    ("bun", "List of bread rolls", "a bread roll primarily in Northern England",
     ["Northumberland", "Tyne and Wear", "Durham", "North Yorkshire", "Cumbria", "Lancashire", "Greater Manchester", "Merseyside",
      "West Yorkshire", "South Yorkshire", "East Riding of Yorkshire"]),
    ("bun", "Bun", "savoury (a roll) in Northern Ireland", ["Northern Ireland"]),
    ("bap", "List of bread rolls", "the Belfast bap (Northern Ireland)", ["Northern Ireland"]),
    ("roll", "Morning roll", "the morning roll, Scotland", [c for c in cnames if cnation[c] == "Scotland"]),
]
wk = []
for w, art, claim, cs in WIKI:
    inside = S.county.isin(cs)
    k_in = int(((S.word == w) & inside).sum())
    k = int((S.word == w).sum())
    n_in = int(inside.sum())
    sh_in = k_in / n_in if n_in else None
    sh_out = int(((S.word == w) & ~inside).sum()) / int((~inside).sum())
    wk.append({"word": w, "article": art, "claim": claim, "counties": cs, "n_in": n_in, "k_in": k_in, "k": k,
               "share_of_word_in_region": k_in / k if k else None, "share_of_answers_in_region": n_in / len(S),
               "share_in": sh_in, "share_out": sh_out, "ratio": (sh_in / sh_out) if sh_out else None})
R["wikipedia"] = wk

# ------------------------------------------------------------------ business names
M = pd.read_csv(os.path.join(ROOT, "data", "roll_word_matches.csv"), keep_default_na=False)
tot = json.load(open(os.path.join(ROOT, "work", "fsa_county_totals.json")))
K_ = M[M.kept == 1].copy()
K_["key"] = K_.name.str.lower().str.replace(r"[^a-z0-9]", "", regex=True) + "|" + K_.county
# unique business name per county across both sources (OSM and FSA list many of the same shops)
U = K_.drop_duplicates(["word", "key"])
fsa_k = K_[K_.source == "FSA"]
B = {"fsa_total": tot["fsa_n"], "osm_total": tot["osm_n"], "fsa_placement": tot["fsa_placement"],
     "fsa_kept": {w: int((fsa_k.word == w).sum()) for w in words.WORDS},
     "osm_kept": {w: int(((K_.source == "OSM") & (K_.word == w)).sum()) for w in words.WORDS},
     "unique_kept": {w: int((U.word == w).sum()) for w in words.WORDS},
     "raw_matches_fsa": {w: int(((M.source == "FSA") & (M.word == w)).sum()) for w in words.WORDS},
     "dropped_fsa": {w: int(((M.source == "FSA") & (M.word == w) & (M.kept == 0)).sum()) for w in words.WORDS}}
B["fsa_any_roll_word"] = int(fsa_k[fsa_k.word.isin(words.ROLL_WORDS)].id.nunique())
B["fsa_any_sandwich_word"] = int(fsa_k[fsa_k.word.isin(words.SANDWICH_WORDS)].id.nunique())
B["fsa_any_kept"] = int(fsa_k.id.nunique())
B["rate_any_roll_per_10k"] = B["fsa_any_roll_word"] / tot["fsa_n"] * 1e4
reasons = M[(M.kept == 0)].groupby(["word", "reason"]).size().reset_index(name="n")
B["drop_reasons"] = [dict(word=r.word, reason=r.reason, n=int(r.n)) for _, r in reasons.sort_values("n", ascending=False).iterrows()]
B["fsa_btype_kept"] = {w: dict(Counter(fsa_k[fsa_k.word == w].btype.astype(str))) for w in ["roll", "bap", "cob", "butty", "sandwich"]}
# county table of business names
fsa_cty = tot["fsa_by_county"]
brow = []
for c in cnames:
    u = U[U.county == c]
    d = {"county": c, "nation": cnation[c], "fsa_businesses": int(fsa_cty.get(c, 0))}
    for w in ["roll", "bap", "cob", "batch", "barm", "stottie", "breadcake", "scuffler", "ovenbottom", "bun", "butty", "sarnie", "sandwich", "piece", "crusty"]:
        d[w] = int((u.word == w).sum())
    sw = d["butty"] + d["sarnie"] + d["sandwich"] + d["piece"]
    d["butty_share"] = round(d["butty"] / sw, 4) if sw >= MIN_N else None
    rw = d["roll"] + d["bap"] + d["cob"] + d["batch"] + d["barm"] + d["stottie"] + d["breadcake"] + d["scuffler"] + d["ovenbottom"]
    d["roll_words"] = rw
    d["sandwich_words"] = sw
    brow.append(d)
BC = pd.DataFrame(brow)
BC.to_csv(os.path.join(ROOT, "data", "business_counties.csv"), index=False)
# where do the business words sit, against the surveys' map of the same words?
J = BC.merge(CT[["county", "n", "top"] + [f"all_{w}" for w in WORDS]], on="county", how="left")
cmpb = {}
for w in ["roll", "bap", "cob", "barm", "batch", "breadcake", "bun"]:
    k = int(J[w].sum())
    zone = J[J.top == w]
    k_zone = int(zone[w].sum())
    biz_zone = int(zone.fsa_businesses.sum())
    jj = J[(J.n >= 30) & (J.fsa_businesses > 0)]
    rate = jj[w] / jj.fsa_businesses * 1e4
    rho, p = spearmanr(jj[f"all_{w}"].astype(float), rate)
    cmpb[w] = {"names": k, "names_in_top_counties": k_zone, "share_names_in_top_counties": (k_zone / k) if k else None,
               "share_businesses_in_top_counties": biz_zone / tot["fsa_n"], "top_counties": zone.county.tolist(),
               "spearman_rho": float(rho), "spearman_p": float(p), "n_counties": int(len(jj))}
B["vs_survey"] = cmpb
bz = R["age"]["batch"]["zone"]
B["batch_zone"] = {"counties": bz, "names_in_zone": int(BC[BC.county.isin(bz)].batch.sum()),
                   "names_in_zone_or_leics": int(BC[BC.county.isin(bz + ["Leicestershire"])].batch.sum()),
                   "share_businesses_in_zone": float(sum(fsa_cty.get(c, 0) for c in bz) / tot["fsa_n"])}
# butty
bt = BC[BC.butty_share.notna()].sort_values("butty_share", ascending=False)
B["butty_top"] = bt.head(8)[["county", "butty", "sandwich_words", "butty_share"]].to_dict("records")
B["butty_bottom"] = bt.tail(5)[["county", "butty", "sandwich_words", "butty_share"]].to_dict("records")
B["butty_national_share"] = float(U[U.word == "butty"].shape[0] / U[U.word.isin(words.SANDWICH_WORDS)].shape[0])
nw = ["Greater Manchester", "Lancashire", "Merseyside", "Cheshire", "Cumbria"]
x = BC[BC.county.isin(nw)]
B["butty_nw_share"] = float(x.butty.sum() / x.sandwich_words.sum())
B["butty_nw_share_of_butties"] = float(x.butty.sum() / BC.butty.sum())
B["nw_share_of_fsa"] = float(sum(fsa_cty.get(c, 0) for c in nw) / tot["fsa_n"])
ld = BC[BC.county == "Greater London"].iloc[0]
B["london_butty"] = int(ld.butty)
B["london_sandwich_words"] = int(ld.sandwich_words)
B["london_share_fsa"] = float(ld.fsa_businesses / tot["fsa_n"])
# barm in names
B["barm_names"] = M[(M.word == "barm") & (M.kept == 1)][["source", "name", "county"]].to_dict("records")
B["scuffler_names"] = M[(M.word == "scuffler") & (M.kept == 1)][["source", "name", "county"]].to_dict("records")
B["stottie_names"] = M[(M.word == "stottie") & (M.kept == 1)][["source", "name", "county"]].to_dict("records")
B["breadcake_names"] = M[(M.word == "breadcake") & (M.kept == 1)][["source", "name", "county"]].to_dict("records")
B["batch_names"] = M[(M.word == "batch") & (M.kept == 1)][["source", "name", "county"]].to_dict("records")
B["buttery_aberdeen"] = int(((M.word == "buttery") & (M.kept == 1) & M.county.isin(["Aberdeen City", "Aberdeenshire"])).sum())
B["cob_east_mid"] = int(U[(U.word == "cob") & U.county.isin(["Nottinghamshire", "Leicestershire", "Derbyshire"])].shape[0])
B["cob_unique"] = int((U.word == "cob").sum())
R["business"] = B

# crusty: which noun follows?
cr = M[(M.word == "crusty") & (M.kept == 1)]
nxt = Counter()
for n in cr.name:
    m_ = re.search(r"crusty['’]?s?\s+([a-z]+)", n.lower())
    nxt[m_.group(1) if m_ else "(none)"] += 1
R["business"]["crusty_next"] = dict(nxt.most_common(8))

# ------------------------------------------------------------------ write
R["meta"] = {"min_n": MIN_N, "doi": "10.5281/zenodo.23691943", "slug": "bread-rolls",
             "title": "Barm, bap, cob or roll? Mapping Britain's bread roll lines from 20,000 survey answers"}


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if math.isnan(o) else float(o)
    return o


json.dump(clean(R), open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1)
print(json.dumps({k: R[k] for k in ["survey", "hex", "smoothing", "lines", "agreement"]}, default=str)[:4000])
