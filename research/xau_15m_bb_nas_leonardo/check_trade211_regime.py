#!/usr/bin/env python3
"""Por que #211 nao esta nos removidos? Mostra regime as-of de #211 (e ultimos trades) + a barra 4H que o classificou.
Confirma numeracao vs strategy_5atr_a2_h1eff_trades.csv (CSV plotado). RAW-causal."""
import json, bisect, csv, datetime as dt
from pathlib import Path
from filter_harness import ROWS, dedup
HERE=Path(__file__).parent
MR=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MR.sort(key=lambda x:x["t_end"])
MEND=[b["t_end"] for b in MR]
def asof(t):
    k=bisect.bisect_right(MEND,t)-1; return MR[k] if k>=0 else None
def d(t): return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")

base=dedup([r for r in ROWS if r['h1_eff'] is not None and r['h1_eff']>=0.15]); base.sort(key=lambda x:x["t"])
for n,c in enumerate(base,1): c["num"]=n
# confere numeracao vs CSV plotado
csvrows=list(csv.DictReader(open(HERE/"strategy_5atr_a2_h1eff_trades.csv")))
print("CSV plotado: N=",len(csvrows),"| #211 entry_t=",csvrows[210]["entry_t"],"entry=",csvrows[210]["entry"])
print("base211 #211: entry_t=",base[210]["t"],"entry=",base[210]["entry"],"-> bate?" , str(base[210]["t"])==csvrows[210]["entry_t"])
print()
for n in (207,208,209,210,211):
    c=base[n-1]; a=asof(c["t"])
    flag="BEAR" if c["macro_bear"] else ("BULL" if c["macro_bull"] else "NEUTRAL")
    print(f"#{n} | {d(c['t'])} entry={c['entry']} R={c['R']:+.2f} | macro_bear={c['macro_bear']} macro_bull={c['macro_bull']} => {flag}")
    if a: print(f"      4H as-of [t_end {d(a['t_end'])}]: macro={a['macro']} close={a['c']} ema50={round(a['ema50'],1)} swing_dir={a['swing_dir']} ema_pos={a['ema_pos']}")
