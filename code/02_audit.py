"""Step 2 (checking aid). Print every match for each word, kept and dropped, so the exclusion rules
in words.py can be read against the names by eye. Usage: python3 code/02_audit.py [word ...]"""
import os, sys
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m = pd.read_csv(os.path.join(ROOT, "data", "roll_word_matches.csv"), keep_default_na=False)
ws = sys.argv[1:] or sorted(m.word.unique())
for w in ws:
    s = m[m.word == w]
    print(f"===== {w}: {len(s)} matches, {s.kept.sum()} kept ({(s.source=='FSA').sum()} FSA)")
    for k in (1, 0):
        print("  -- kept" if k else "  -- dropped")
        for _, r in s[s.kept == k].sort_values("name").iterrows():
            print(f"     {r.source} | {r['name'][:70]} | {r.pc_area or r.county} | {r.reason}")
