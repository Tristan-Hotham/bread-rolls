"""Step 5. Build ../index.html and ../README.md from templates.

Every number in the text is a placeholder like {{survey.inside_n|int}} filled from
data/results.json, or a derived value computed below from the same file. The compact page data
(work/site.json) is embedded as `const D = ...`.
Formats: int, pct0, pct1, f0, f1, f2, raw.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
site = open(os.path.join(ROOT, "work", "site.json")).read().replace("–", "-").replace("—", "-")


def pct(v, d=0):
    return f"{v * 100:.{d}f}%"


yg = {(r["word"], r["county"]): r for r in R["yougov"]["rows"]}
wk = R["wikipedia"]
B = R["business"]
X = {
    "pct60": "60%",
    "yg_cob_leics": pct(yg[("cob", "Leicestershire")]["od"]),
    "yg_cob_notts": pct(yg[("cob", "Nottinghamshire")]["od"]),
    "age_cob_young": pct(R["age"]["cob"]["groups"][0]["share"]),
    "age_cob_mid": pct(R["age"]["cob"]["groups"][2]["share"]),
    "age_batch_young": pct(R["age"]["batch"]["groups"][0]["share"], 1),
    "age_batch_mid": pct(R["age"]["batch"]["groups"][2]["share"], 1),
    "age_batch_n": str(R["age"]["batch"]["groups"][0]["n"]),
    "wk_barm": pct(wk[0]["share_of_word_in_region"]),
    "wk_barm_base": pct(wk[0]["share_of_answers_in_region"]),
    "wk_bc_ratio": f"{wk[2]['ratio']:.0f}",
    "wk_batch_ratio": f"{wk[1]['ratio']:.0f}",
    "wk_bun_ni": pct(wk[6]["share_in"], 1),
    "rate_roll_10k": f"{B['rate_any_roll_per_10k']:.1f}",
    "cob_share": pct(B["cob_east_mid"] / B["cob_unique"]),
    "cob_base": pct(B["vs_survey"]["cob"]["share_businesses_in_top_counties"], 1),
    "butty_nw": pct(B["butty_nw_share_of_butties"]),
    "nw_base": pct(B["nw_share_of_fsa"]),
    "london_base": pct(B["london_share_fsa"]),
}
R["_x"] = X


def get(path):
    if path in X:
        return X[path]
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if isinstance(v, str) and f in ("", "raw"):
        return v
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f0": return f"{v:.0f}"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip())


def fill(t):
    return re.sub(r"\{\{(.+?)\}\}", sub, t)


if __name__ == "__main__":
    t = fill(open(os.path.join(HERE, "page_template.html")).read())
    t = t.replace("/*DATA*/", "const D = " + site + ";")
    open(os.path.join(ROOT, "index.html"), "w").write(t)
    print("index.html", len(t.encode()) // 1024, "KB")
    md = fill(open(os.path.join(HERE, "README_template.md")).read())
    open(os.path.join(ROOT, "README.md"), "w").write(md)
    print("README.md written")
