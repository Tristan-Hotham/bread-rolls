"""Step 6. Static figures with matplotlib, drawn from data/ and work/fields.npz.

  map/words_grid.png            small multiples for the page
  release/paper/f_*.png         paper figures
  release/blog/b_*.png          blog figures, 1520 px wide, no titles inside the image

Fonts: Source Serif 4 and IBM Plex Mono from FONT_DIR (Google Fonts files) if present.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402
from pyproj import Transformer  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from style import WORDS, LABEL, COLOR, BG, FG, MUTED, RULE, LAND, ROLL_INK, FONT_DIR  # noqa: E402

FD = os.environ.get("FONT_DIR", FONT_DIR)
for f in ["IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    if os.path.exists(os.path.join(FD, f)):
        fm.fontManager.addfont(os.path.join(FD, f))
SER, MONO = "Source Serif 4", "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 11, "axes.edgecolor": MUTED, "axes.labelcolor": FG, "xtick.color": MUTED,
                     "ytick.color": MUTED, "text.color": FG, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG})
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
F = np.load(os.path.join(ROOT, "work", "fields.npz"))
P = F["P"].astype(np.float32)
mask, top1 = F["mask"], F["top1"]
x0, y0, cell = float(F["x0"]), float(F["y0"]), float(F["cell"])
ny, nx = mask.shape
EXT = [x0, x0 + nx * cell, y0, y0 + ny * cell]
TR = Transformer.from_crs(4326, 27700, always_xy=True)
C = json.load(open(os.path.join(ROOT, "data", "counties.geojson")))
LINES = json.load(open(os.path.join(ROOT, "data", "roll_lines.geojson")))
for d in ["map", "release/paper", "release/blog"]:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)


def polys():
    out = []
    for f in C["features"]:
        g = f["geometry"]
        rings = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in rings:
            r = np.array(poly[0])
            X, Y = TR.transform(r[:, 0], r[:, 1])
            out.append((X, Y))
    return out


POLYS = polys()


def base(ax, xlim=(-10000, 670000), ylim=(0, 1000000), fill=True, lw=.35):
    for X, Y in POLYS:
        if fill:
            ax.fill(X, Y, color=LAND, lw=0, zorder=0)
        ax.plot(X, Y, color="#BFAE90", lw=lw, zorder=3)
    ax.set_aspect("equal")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")


def lead_rgba(alpha_min=.55):
    img = np.zeros((ny, nx, 4))
    ts = np.take_along_axis(P, top1[None], 0)[0]
    for k, w in enumerate(WORDS):
        sel = mask & (top1 == k)
        img[sel, :3] = to_rgb(COLOR[w])
        img[sel, 3] = alpha_min + (1 - alpha_min) * np.clip((ts[sel] - .3) / .4, 0, 1)
    return img


def share_rgba(w):
    k = WORDS.index(w)
    img = np.zeros((ny, nx, 4))
    img[mask, :3] = to_rgb(COLOR[w])
    img[mask, 3] = np.clip(P[k][mask] / .6, 0, 1) ** .8
    return img


def draw_lines(ax, lw=1.6, roll=True):
    for f in LINES["features"]:
        c = np.array(f["geometry"]["coordinates"])
        X, Y = TR.transform(c[:, 0], c[:, 1])
        if f["properties"]["kind"] == "roll_half":
            if roll:
                ax.plot(X, Y, color=BG, lw=lw * 2.6, zorder=5, solid_capstyle="round")
                ax.plot(X, Y, color="#D7263D", lw=lw * 1.2, ls=(0, (4, 2.5)), zorder=6)
        else:
            ax.plot(X, Y, color=BG, lw=lw * 2.4, zorder=5, solid_capstyle="round")
            ax.plot(X, Y, color=FG, lw=lw, zorder=6, solid_capstyle="round")


def save(fig, name, blog_w=1520):
    fig.savefig(os.path.join(ROOT, "release", "paper", f"f_{name}.png"), dpi=200)
    w_in = fig.get_size_inches()[0]
    fig.savefig(os.path.join(ROOT, "release", "blog", f"b_{name}.png"), dpi=blog_w / w_in)
    plt.close(fig)


# ---------------------------------------------------------------- 1. leading word map
def fig_map():
    fig = plt.figure(figsize=(9, 11.5))
    ax = fig.add_axes([0.0, 0.0, 0.72, 1.0])
    base(ax, xlim=(-20000, 660000), ylim=(0, 980000))
    ax.imshow(lead_rgba(), origin="lower", extent=EXT, zorder=2, interpolation="bilinear")
    draw_lines(ax)
    lab = {"barm": (330000, 420000, "barm"), "cob": (470000, 330000, "cob"), "bun": (470000, 560000, "bun"),
           "bap": (230000, 350000, "bap"), "breadcake": (530000, 445000, "breadcake"), "muffin": (420000, 425000, "muffin"),
           "batch": (440000, 255000, "batch"), "teacake": (300000, 495000, "teacake"), "roll": (520000, 180000, "roll"),
           "bapni": (60000, 520000, "bap")}
    for k, (x, y, t) in lab.items():
        w = "bap" if k == "bapni" else k
        ax.text(x, y, t, fontsize=12.5, color=FG if w in ("roll", "breadcake") else "white", ha="center", va="center", zorder=8, weight="medium",
                bbox=dict(boxstyle="round,pad=0.25", fc=COLOR[w] if w != "roll" else BG, ec="none", alpha=.95))
    ax.text(270000, 720000, "roll", fontsize=12.5, color=FG, ha="center", va="center", zorder=8, weight="medium",
            bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=.95))
    lg = fig.add_axes([0.70, 0.40, 0.29, 0.5]); lg.axis("off")
    yy = 1.0
    for w in WORDS[:9]:
        lg.add_patch(plt.Rectangle((0, yy - .035), .1, .05, color=COLOR[w], transform=lg.transAxes))
        lg.text(.15, yy - .01, f"{LABEL[w]}", fontsize=12, va="center", transform=lg.transAxes)
        lg.text(.98, yy - .01, f"{R['survey']['count_ALL'][w]:,}", fontsize=11, va="center", ha="right", color=MUTED, transform=lg.transAxes)
        yy -= .075
    yy -= .03
    lg.plot([0, .1], [yy, yy], color=FG, lw=1.8, transform=lg.transAxes)
    lg.text(.15, yy, "leading word\nchanges", fontsize=10.5, va="center", transform=lg.transAxes)
    yy -= .1
    lg.plot([0, .1], [yy, yy], color="#D7263D", lw=2, ls=(0, (4, 2.5)), transform=lg.transAxes)
    lg.text(.15, yy, "roll falls\nbelow half", fontsize=10.5, va="center", transform=lg.transAxes)
    yy -= .1
    lg.add_patch(plt.Rectangle((0, yy - .025), .1, .05, color=LAND, transform=lg.transAxes))
    lg.text(.15, yy, "too few answers\nnearby", fontsize=10.5, va="center", transform=lg.transAxes)
    lg.set_visible(False)
    fig.savefig(os.path.join(ROOT, "work", "header_map.png"), dpi=110)
    lg.set_visible(True)
    save(fig, "map")


# ---------------------------------------------------------------- 2. small multiples
def fig_words():
    ws = WORDS[:9]
    fig, axs = plt.subplots(3, 3, figsize=(10, 12.6))
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.97, 0.02, 0.08)
    for ax, w in zip(axs.flat, ws):
        base(ax, xlim=(-20000, 660000), ylim=(0, 980000), lw=.25)
        ax.imshow(share_rgba(w), origin="lower", extent=EXT, zorder=2, interpolation="bilinear")
        ax.set_title(f"{LABEL[w]}   {R['survey']['count_ALL'][w]:,}", fontsize=14, color=FG, pad=2, loc="left",
                     fontweight="medium")
    fig.savefig(os.path.join(ROOT, "map", "words_grid.png"), dpi=110)
    save(fig, "words")


# ---------------------------------------------------------------- 3. north-south profile
def fig_profile():
    d = pd.DataFrame(R["lines"]["england_profile"])
    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.subplots_adjust(0.09, 0.14, 0.86, 0.97)
    sty = {"roll": "-", "bun": "--", "bap": "-.", "barm": ":", "cob": "-", "breadcake": (0, (5, 1, 1, 1))}
    ends = []
    for w in ["roll", "bun", "bap", "barm", "cob", "breadcake"]:
        c = ROLL_INK if w == "roll" else COLOR[w]
        ax.plot(d.northing_km, d[w] * 100, color=c, lw=3 if w == "roll" else 2.2, ls=sty[w], marker="o", ms=4)
        ends.append([w, d[w].iloc[-1] * 100])
    ends.sort(key=lambda e: e[1])
    for i in range(1, len(ends)):
        if ends[i][1] - ends[i - 1][1] < 4:
            ends[i][1] = ends[i - 1][1] + 4
    for w, y in ends:
        ax.text(d.northing_km.iloc[-1] + 12, y, LABEL[w], va="center", fontsize=12, color=ROLL_INK if w == "roll" else COLOR[w], fontweight="medium")
    ax.set_xlabel("Distance north, km (British National Grid northing; south coast left, Scottish border right)", fontsize=11)
    ax.set_ylabel("Share of answers, %", fontsize=11)
    ax.set_ylim(0, 80)
    ax.grid(axis="y", color=RULE)
    save(fig, "profile")


# ---------------------------------------------------------------- 4. two surveys
def fig_agree():
    pts = pd.DataFrame(R["agreement"]["scatter"])
    ws = ["roll", "bun", "bap", "barm", "cob", "breadcake"]
    fig, axs = plt.subplots(2, 3, figsize=(10, 7))
    fig.subplots_adjust(0.08, 0.1, 0.98, 0.95, 0.3, 0.38)
    for ax, w in zip(axs.flat, ws):
        mx = max(pts[f"od_{w}"].max(), pts[f"dh_{w}"].max()) * 1.08
        ax.plot([0, mx], [0, mx], color=MUTED, lw=1, ls="--")
        ax.scatter(pts[f"od_{w}"] * 100, pts[f"dh_{w}"] * 100, s=12 + np.sqrt(pts.n_od + pts.n_dh) * 1.2, color=ROLL_INK if w == "roll" else COLOR[w],
                   alpha=.75, edgecolor="white", lw=.6)
        ax.set_xlim(0, mx * 100); ax.set_ylim(0, mx * 100)
        ax.set_title(f"{LABEL[w]}   r = {R['agreement']['by_word'][w]['r']:.2f}", fontsize=12.5, loc="left", fontweight="medium")
        ax.grid(color=RULE, lw=.6)
        ax.tick_params(labelsize=9.5)
    fig.text(0.53, 0.02, "Our Dialects, % of a county's answers", ha="center", fontsize=11)
    fig.text(0.015, 0.52, "Dialect and Heritage, %", rotation=90, va="center", fontsize=11)
    save(fig, "agree")


# ---------------------------------------------------------------- 5. age
def fig_age():
    ws = ["cob", "batch", "barm", "bun"]
    fig, axs = plt.subplots(1, 4, figsize=(11, 4))
    fig.subplots_adjust(0.06, 0.2, 0.99, 0.86, 0.35)
    for ax, w in zip(axs, ws):
        a = R["age"][w]
        g = pd.DataFrame(a["groups"])
        x = np.arange(len(g))
        ax.errorbar(x, g.share * 100, yerr=[(g.share - g.lo) * 100, (g.hi - g.share) * 100], fmt="o", color=COLOR[w], ms=8, capsize=3, lw=2)
        ax.set_xticks(x, ["<25", "25-44", "45-64", "65+"], fontsize=10)
        ax.set_ylim(0, max(g.hi) * 100 * 1.15)
        ax.set_title(f"{LABEL[w]}\nn = {a['n']:,}", fontsize=12, loc="left", fontweight="medium")
        ax.grid(axis="y", color=RULE)
    axs[0].set_ylabel("% giving the word", fontsize=11)
    fig.text(0.5, 0.03, "Age group (Dialect and Heritage answers in each word's heartland counties)", ha="center", fontsize=10.5, color=MUTED)
    save(fig, "age")


# ---------------------------------------------------------------- 6. high street
def fig_highstreet():
    M = pd.read_csv(os.path.join(ROOT, "data", "roll_word_matches.csv"), keep_default_na=False)
    K = M[(M.kept == 1) & (M.lat != "")].copy()
    K["key"] = K.name.str.lower().str.replace(r"[^a-z0-9]", "", regex=True) + "|" + K.county + "|" + K.word
    K = K.sort_values("source").drop_duplicates("key")
    K["X"], K["Y"] = TR.transform(K.lon.astype(float).values, K.lat.astype(float).values)
    fig, axs = plt.subplots(1, 2, figsize=(10, 7.4))
    fig.subplots_adjust(0, 0.0, 1, 0.94, 0.02)
    groups = [("cob", COLOR["cob"]), ("batch", COLOR["batch"]), ("barm", COLOR["barm"]), ("stottie", COLOR["bun"]),
              ("breadcake", COLOR["breadcake"]), ("scuffler", COLOR["breadcake"]), ("ovenbottom", COLOR["barm"])]
    ax = axs[0]
    base(ax, xlim=(-20000, 660000), ylim=(0, 980000), lw=.25)
    q = K[K.word == "bap"]
    ax.scatter(q.X, q.Y, s=10, color=COLOR["bap"], alpha=.55, lw=0, zorder=4, label=f"bap  {R['business']['unique_kept']['bap']}")
    for w, c in groups:
        q = K[K.word == w]
        if len(q):
            ax.scatter(q.X, q.Y, s=26, color=c, edgecolor="white", lw=.6, zorder=5,
                       label=f"{'oven bottom' if w == 'ovenbottom' else w}  {R['business']['unique_kept'][w]}")
    ax.legend(loc="upper left", frameon=False, fontsize=10.5, handletextpad=.2, bbox_to_anchor=(0.0, 0.93))
    ax.set_title("Roll words in business names", fontsize=12.5, loc="left", fontweight="medium")
    ax = axs[1]
    base(ax, xlim=(-20000, 660000), ylim=(0, 980000), lw=.25)
    q = K[K.word == "sandwich"]
    for w, c, s in [("sarnie", "#8A6F4E", 14), ("butty", FG, 14), ("piece", "#2F6DB5", 18)]:
        q = K[K.word == w]
        ax.scatter(q.X, q.Y, s=s, color=c, alpha=.85, lw=0, zorder=5, label=f"{w}  {R['business']['unique_kept'][w]}")
    ax.legend(loc="upper left", frameon=False, fontsize=10.5, handletextpad=.2, bbox_to_anchor=(0.0, 0.93))
    ax.set_title("Sandwich words in business names", fontsize=12.5, loc="left", fontweight="medium")
    save(fig, "highstreet")


if __name__ == "__main__":
    fig_map(); fig_words(); fig_profile(); fig_agree(); fig_age(); fig_highstreet()
    print("figures written")
