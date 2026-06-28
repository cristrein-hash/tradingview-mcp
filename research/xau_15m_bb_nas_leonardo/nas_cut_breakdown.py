#!/usr/bin/env python3
"""SANITY_PROBE — breakdown exato do conjunto cortado por NAS-long (nas_long_16>=1) sobre substrato #4 (descritivo)."""
import json
from pathlib import Path
R=[json.loads(l) for l in (Path(__file__).parent/"substrate4_flow.jsonl").read_text().splitlines()]
cut=[r for r in R if (r["flow"].get("nas_long_16") or 0)>=1]
L=[r for r in cut if r["R"]<=0]; W=[r for r in cut if r["R"]>0]; run=[r for r in cut if r["R"]>=3]
print(f"SUBSTRATO#4 N={len(R)} | CORTE NAS-long (nas_long_16>=1): total={len(cut)}  losers={len(L)}  winners={len(W)}  runners(R>=3)={len(run)}")
print(f"sumR do conjunto cortado = {sum(r['R'] for r in cut):.1f}  (losers {sum(r['R'] for r in L):.1f} / winners {sum(r['R'] for r in W):.1f})")
