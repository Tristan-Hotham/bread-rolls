"""r/dataisbeautiful collage: Barm, bap, cob or roll? 2400 x 3000 px, light flour background.
Run from the project root or anywhere: python3 reddit/collage.py
"""
import importlib.util
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("figs", os.path.join(ROOT, "code", "06_figures.py"))
F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)
R, COLOR, LABEL, BG, FG, MUTED = F.R, F.COLOR, F.LABEL, F.BG, F.FG, F.MUTED
FD = F.FD
fm.fontManager.addfont(os.path.join(FD, "FrauncesVar.ttf"))
DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
ACC = "#D7263D"
S, B, A = R["survey"], R["business"], R["agreement"]

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
t1 = fig.text(0.045, 0.968, "Barm, bap, cob or ", fontproperties=DISP, fontsize=50, color=FG, va="top")
bb = t1.get_window_extent(renderer=fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
fig.text(bb.x1, 0.968, "roll?", fontproperties=DISP, fontsize=50, color=ACC, va="top")
fig.text(0.045, 0.912, f"What Britain calls a bread roll. {S['inside_n']:,} answers from two dialect surveys, smoothed into the\n"
         "lines where one word gives way to another, and checked against 614,437 food business names.",
         family=SER, fontsize=15, color=FG, va="top", linespacing=1.4)

# hero map
ax = fig.add_axes([0.0, 0.285, 0.6, 0.575])
F.base(ax, xlim=(-20000, 660000), ylim=(0, 980000), lw=.3)
ax.imshow(F.lead_rgba(), origin="lower", extent=F.EXT, zorder=2, interpolation="bilinear")
F.draw_lines(ax, lw=1.5)
lab = [(330000, 418000, "barm"), (470000, 330000, "cob"), (470000, 560000, "bun"), (232000, 350000, "bap"), (536000, 446000, "breadcake"),
       (420000, 423000, "muffin"), (440000, 252000, "batch"), (296000, 497000, "teacake"), (520000, 170000, "roll"), (60000, 520000, "bap"),
       (270000, 720000, "roll")]
for x, y, w in lab:
    ax.text(x, y, w, fontsize=12.5, family=MONO, color=FG if w in ("roll", "breadcake") else "white", ha="center", va="center", zorder=8,
            weight="medium", bbox=dict(boxstyle="round,pad=0.25", fc=COLOR[w] if w != "roll" else BG, ec="none", alpha=.95))
ax.annotate("roll falls below half\nof all answers", xy=(318000, 292000), xytext=(110000, 190000), family=MONO, fontsize=10.5, color=ACC,
            arrowprops=dict(arrowstyle="-", color=ACC, lw=.9), zorder=9)

# legend with counts
lg = fig.add_axes([0.6, 0.66, 0.36, 0.17]); lg.axis("off")
for i, w in enumerate(F.WORDS[:9]):
    col, row = i // 5, i % 5
    x, y = col * 0.52, 1 - row * 0.2
    lg.scatter([x + .03], [y - .05], s=120, color=COLOR[w], transform=lg.transAxes, clip_on=False)
    lg.text(x + .08, y - .05, f"{LABEL[w]}  {S['count_ALL'][w]:,}", family=MONO, fontsize=11.5, va="center", color=FG, transform=lg.transAxes)

# big numbers
tx = fig.add_axes([0.6, 0.29, 0.37, 0.36]); tx.axis("off")
notes = [(f"{S['share_ALL']['roll'] * 100:.0f}%", "say roll. Only " + f"{R['lines']['share_answers_roll_majority_by_nation']['England'] * 100:.0f}%" +
          " of English answers come\nfrom places where roll has a majority."),
         (f"{S['by_nation']['Northern Ireland']['share']['bap'] * 100:.0f}%", f"of answers in Northern Ireland say bap.\nWikipedia's Northern Irish bun: {R['wikipedia'][6]['share_in'] * 100:.0f}%."),
         (f"{A['by_word']['barm']['r']:.2f}", f"county correlation for barm between the two\nsurveys. Cob {A['by_word']['cob']['r']:.2f}, bun {A['by_word']['bun']['r']:.2f}: they agree on where."),
         (f"{B['fsa_kept']['barm']}", f"of 614,437 food businesses use barm in their\nname. But {B['cob_east_mid']} of {B['cob_unique']} cob names are in Derbys,\nLeics and Notts, with {B['vs_survey']['cob']['share_businesses_in_top_counties'] * 100:.0f}% of the UK's food businesses.")]
for (big, small), y in zip(notes, [1.0, 0.75, 0.5, 0.25]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=30, color=ACC, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.085, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# small multiples
fig.text(0.045, 0.272, "EACH WORD'S OWN SHARE OF ANSWERS (darkest: 60% or more)", family=MONO, fontsize=11, color=MUTED)
for i, w in enumerate(["bun", "bap", "barm", "cob", "breadcake", "batch"]):
    a = fig.add_axes([0.01 + i * 0.163, 0.058, 0.163, 0.17])
    F.base(a, xlim=(-20000, 660000), ylim=(0, 980000), lw=.15)
    a.imshow(F.share_rgba(w), origin="lower", extent=F.EXT, zorder=2, interpolation="bilinear")
    a.set_title(f"{LABEL[w]}\n{S['count_ALL'][w]:,}", family=MONO, fontsize=11.5, color=FG, pad=2)

fig.text(0.045, 0.012,
         "Data: Our Dialects bread map (ourdialects.uk) and Dialect and Heritage Project, University of Leeds, \"Roll with it\": answers used\n"
         "with credit, aggregated only. Food Standards Agency hygiene ratings (OGL v3); OpenStreetMap (ODbL); ONS boundaries (OGL v3).\n"
         f"Analysis and chart: Tristan Hotham, with Python and matplotlib. Lines: kernel smoothing, {R['smoothing']['bandwidth_km']} km where answers are dense.",
         family=MONO, fontsize=9, color=MUTED, linespacing=1.45)
fig.savefig(os.path.join(HERE, "bread_roll_lines.png"), facecolor=BG, dpi=200)
print("ok")
