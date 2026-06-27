#!/usr/bin/env python3
"""DA final: bracket sumR concentration, csv_exit==entry baseline check, F mechanism, fill-at-low impact on bracket."""
import json, csv, statistics as st
from pathlib import Path
HERE=Path(__file__).parent; HMAX=480
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIM={k[:10]:v for k,v in PRIM.items()}
FD={r["t"]:r for r in (json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines())}
GT={int(r["num"]):r for r in csv.DictReader(open(HERE/"cris_ground_truth.csv"))}
T170={int(r["num"]):r for r in csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv"))}
SL=list(csv.DictReader(open(HERE/"lab_sl_exit.csv")))
ENG={int(r["num"]):r for r in csv.DictReader(open(HERE/"lab_entry_engine.csv"))}
def f(x):
    try: return float(x)
    except: return None

print("="*70); print("A — bracket sumR concentration (top contributors)"); print("="*70)
br=sorted([(int(r["num"]),f(r["br_R"]),r["br_out"],r["tp_reached"]) for r in SL],key=lambda x:-x[1])
tot=sum(x[1] for x in br)
top10=br[:10]
print(f"bracket total {tot:+.1f}R | top-10 trades = {sum(x[1] for x in top10):+.1f}R ({100*sum(x[1] for x in top10)/tot:.0f}% of total)")
for n,r,o,tp in top10:
    g=GT[n]; rp=f(g["cris_Rpot"])
    print(f"  #{n}: br_R {r:+.2f} ({o}) cris_Rpot={rp} cris_exit={g['cris_exit']} csv_exit={g['csv_exit']} | letrun_R={T170[n]['R']}")
# how many trades have csv_exit == entry (i.e. csv 'exit' col is just the SL for losers -> baseline csv_exit meaningless)
nbad=sum(1 for g in GT.values() if abs(f(g["csv_exit"])-f(g["csv_sl"]))<0.05)
print(f"trades where csv_exit==csv_sl (csv 'exit' is just stop, so 'higher than csv' is trivially true for any winner target): {nbad}/170")

print("\n"+"="*70); print("BRACKET with fill-at-candle-low SL (realistic) vs exact-SL"); print("="*70)
# Re-sim bracket but on SL hit, charge actual candle low (worse than -1R), TP exact.
real=[]
for r in SL:
    num=int(r["num"]); g=GT[num]; t=int(g["entry_t"]); fd=FD.get(t)
    pr=PRIM[fd["block"]]; s=pr["series"]; cj=int(fd["cj"])
    entry=f(g["entry"]); cris_sl=f(g["cris_sl"]); cris_exit=f(g["cris_exit"]); risk=entry-cris_sl
    end=min(cj+HMAX,len(s)-1); out=None
    for k in range(cj+1,end+1):
        lo,hi=s[k]["l"],s[k]["h"]
        hit_sl=lo<=cris_sl; hit_tp=hi>=cris_exit
        if hit_sl and hit_tp:  # ambos: conservative SL but at candle low
            out=("SL",max(-1.0-(cris_sl-lo)/risk if risk>0 else -1.0, -5.0)); break  # cap catastrophe -5R
        if hit_sl:
            slipR=(cris_sl-lo)/risk if risk>0 else 0
            out=("SL",max(-1.0-slipR,-5.0)); break
        if hit_tp: out=("TP",(cris_exit-entry)/risk if risk>0 else 0); break
    if out is None: out=("timeout",(s[end]["c"]-entry)/risk if risk>0 else 0)
    real.append(out[1])
print(f"bracket exact-SL sumR = +148.9 (reported) | bracket fill-at-low SL (cap -5R) sumR = {sum(real):+.1f}")

print("\n"+"="*70); print("F mechanism — why better entry worsens DD"); print("="*70)
# trades flipped W->L by engine (winners that became losers) -> these add consecutive losses
flip_wl=[(n,f(ENG[n]['R0']),f(ENG[n]['R'])) for n in ENG if f(ENG[n]['R0'])>0 and f(ENG[n]['R'])<=0]
print(f"winners turned into losers by engine (limit filled then stopped, or letrun from worse spot): {len(flip_wl)} -> {flip_wl}")
print("  MECHANISM: limit fill = enter lower -> SL unchanged (flush) -> smaller risk -> faster 1R lock,")
print("  BUT for trades that pulled to demand then died, the limit got filled and then stopped =")
print("  converts a no-fill-skip(...actually a small win in base) into a -1R. These cluster -> deeper DD.")
