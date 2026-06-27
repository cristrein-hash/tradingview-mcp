#!/usr/bin/env python3
"""Sweep de VARIACOES de feature de regime macro (Cris 2026-06-27) sobre base aprovada A2+h1_eff>=0.15.
Qual mapa de regime melhora mais LUCRO/STREAK/DD/WINRATE ao cortar regime desfavoravel.
Mapas testados (todos CAUSAIS as-of): macro 4H (ema50+swing), swing_dir 4H, ema_pos 4H, h1/h4/hd_trend, h4/hd_pos.
Enriquece linhas do filter_dataset (sem reescreve-lo) + dedup/stats do harness. RAW-causal."""
import json, bisect
from pathlib import Path
from filter_harness import ROWS, dedup, stats
HERE=Path(__file__).parent
# join hd/h4/h1 trend+pos do dataset_5atr
F={}
for l in (HERE/"dataset_5atr.jsonl").read_text().splitlines():
    r=json.loads(l); F[(r["block"],r["low_t"])]=r
# regime 4H as-of: swing_dir, ema_pos
MR=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MR.sort(key=lambda x:x["t_end"])
MEND=[b["t_end"] for b in MR]
def asof(t):
    k=bisect.bisect_right(MEND,t)-1; return MR[k] if k>=0 else {}
for r in ROWS:
    src=F.get((r["block"],r["low_t"]),{})
    for f in ("hd_trend","hd_pos","hd_eff","h4_trend","h1_trend","h4_pos"): r[f]=src.get(f)
    a=asof(r["t"]); r["swing_dir"]=a.get("swing_dir"); r["ema_pos"]=a.get("ema_pos")

base211=dedup([r for r in ROWS if (r['h1_eff'] is not None and r['h1_eff']>=0.15)])
B=stats(base211)

VARIANTS={
 "BASE A2+h1_eff (sem regime)": "True",
 "macro != BEAR (BULL+NEUTRAL)": "r['macro_bear']==0",
 "macro == BULL so": "r['macro_bull']==1",
 "swing_dir>=0 (4H)": "(r.get('swing_dir') or 0)>=0",
 "ema_pos>=0 (4H vs EMA50)": "(r.get('ema_pos') or 0)>=0",
 "h4_trend>=0 (None=keep)": "(r.get('h4_trend') is None) or r['h4_trend']>=0",
 "hd_trend>=0 daily (None=keep)": "(r.get('hd_trend') is None) or r['hd_trend']>=0",
 "hd_trend==1 daily-up (None=keep)": "(r.get('hd_trend') is None) or r['hd_trend']==1",
 "macro!=BEAR & swing_dir>=0": "r['macro_bear']==0 and (r.get('swing_dir') or 0)>=0",
 "macro!=BEAR & ema_pos>=0": "r['macro_bear']==0 and (r.get('ema_pos') or 0)>=0",
 "macro!=BEAR & hd_trend>=0": "r['macro_bear']==0 and ((r.get('hd_trend') is None) or r['hd_trend']>=0)",
 "macro!=BEAR & h4_trend>=0": "r['macro_bear']==0 and ((r.get('h4_trend') is None) or r['h4_trend']>=0)",
 "ema_pos>=0 & swing_dir>=0": "(r.get('ema_pos') or 0)>=0 and (r.get('swing_dir') or 0)>=0",
}

def yrstr(taken):
    yr={}
    for c in taken: yr.setdefault(c["yr"],[0,0]); yr[c["yr"]][0]+=1; yr[c["yr"]][1]+=c["win"]
    return "/".join(f"{100*yr[y][1]/yr[y][0]:.0f}" if y in yr else "-" for y in (2024,2025,2026))

print(f"BASE211 (h1_eff): N={B['n']} WR={B['wr']} sumR={B['sumr']} DD={B['dd']} streak={B['streak']} maxR={B['maxR']}")
print(f"\n{'variacao de regime (+ h1_eff>=0.15)':<38} {'N':>4} {'WR':>5} {'sumR':>6} {'DD':>5} {'stk':>3} {'maxR':>4} | {'dWR':>5} {'dSumR':>6} {'dDD':>5} | yr24/25/26")
res=[]
for name,cond in VARIANTS.items():
    fn=eval("lambda r:(r['h1_eff'] is not None and r['h1_eff']>=0.15) and ("+cond+")")
    taken=dedup([r for r in ROWS if fn(r)]); s=stats(taken)
    dWR=round(s['wr']-B['wr'],1); dSumR=round(s['sumr']-B['sumr'],1); dDD=round(s['dd']-B['dd'],1)
    print(f"{name:<38} {s['n']:>4} {s['wr']:>5} {s['sumr']:>6} {s['dd']:>5} {s['streak']:>3} {s['maxR']:>4} | {dWR:>+5} {dSumR:>+6} {dDD:>+5} | {yrstr(taken)}")
    res.append((name,s,dWR,dSumR,dDD))
