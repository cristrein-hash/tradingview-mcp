"""Audit: confirm sell_skew_mig bubble source is causal.
kb() uses (known_at or t) <= tc. Report known_at coverage and whether any
known_at < t (which would be the only anti-causal case)."""
import json, glob
from pathlib import Path
HERE=Path('.')
files=sorted(glob.glob('bubbles/*.bubbles.jsonl'))
tot=0; have_ka=0; ka_before_t=0
for fp in files:
    for l in open(fp):
        l=l.strip()
        if not l: continue
        x=json.loads(l); tot+=1
        if x.get('known_at') is not None:
            have_ka+=1
            if x['known_at']<x['t']: ka_before_t+=1
print(f"bubble files={len(files)} total_bubbles={tot}")
print(f"have known_at={have_ka} ({100*have_ka/tot:.1f}%)")
print(f"known_at < t (anti-causal)={ka_before_t}")
print("kb() filter = (known_at or t) <= tc  => causal regardless of coverage")
