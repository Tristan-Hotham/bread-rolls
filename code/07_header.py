"""Step 7. Render ../header.png (1200x630 social card) with Playwright Chromium.
Fonts: FONT_DIR with Fraunces, Source Serif 4 and IBM Plex Mono (Google Fonts files); otherwise system serif.
Run: python3 code/07_header.py
"""
import base64
import json
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from style import FONT_DIR  # noqa: E402
FD = os.environ.get("FONT_DIR", FONT_DIR)
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
img = base64.b64encode(open(os.path.join(ROOT, "work", "header_map.png"), "rb").read()).decode()
ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
    ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
    ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
n = R["survey"]["inside_n"]
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:#F6EFE1;color:#2A2118;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:64px;top:70px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#76695A;display:flex;gap:12px;align-items:center}}
.k b{{background:#D7263D;color:#fff;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:60px;top:112px;margin:0;font:900 104px/.9 Fraunces,Georgia,serif;letter-spacing:-.02em;font-variation-settings:"SOFT" 60;width:640px}}
h1 em{{font-style:normal;color:#D7263D}}
p{{position:absolute;left:64px;top:400px;width:540px;margin:0;font-size:25px;line-height:1.36}}
.f{{position:absolute;left:64px;bottom:40px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#76695A}}
.m{{position:absolute;left:640px;top:-30px;height:700px;z-index:0}} h1,p,.k,.f{{z-index:1}}
</style></head><body>
<div class="k"><b>Data study</b><span>Dialect × food</span></div>
<h1>Barm, bap, cob or <em>roll?</em></h1>
<p>{n:,} survey answers, smoothed into the lines where one bread roll word gives way to another.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<img class="m" src="data:image/png;base64,{img}">
</body></html>"""
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
print("header.png written")
