#!/usr/bin/env python3
"""Lista os 47 trades RETIRADOS ao aplicar macro!=BEAR, com o #N do plot dos 211 (mesma numeracao do chart).
base211 = dedup(h1_eff>=0.15) ordenado por t, num=1..211 (= strategy_5atr_a2_h1eff_trades.csv).
removidos = nos 211 mas nao nos 181. Separa BEAR-bloqueado-direto vs deslocado-por-resequencia. RAW-causal."""
import json, bisect, datetime as dt
from pathlib import Path
from filter_harness import ROWS, dedup
HERE=Path(__file__).parent
MR=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MR.sort(key=lambda x:x["t_end"])
MEND=[b["t_end"] for b in MR]
def reg(t):
    k=bisect.bisect_right(MEND,t)-1; return MR[k]["macro"] if k>=0 else "WARMUP"
def d(t): return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")

base=dedup([r for r in ROWS if r['h1_eff'] is not None and r['h1_eff']>=0.15])
base.sort(key=lambda x:x["t"])
for n,c in enumerate(base,1): c["num"]=n
filt=set((c['block'],c['low_t']) for c in dedup([r for r in ROWS if r['h1_eff'] is not None and r['h1_eff']>=0.15 and r['macro_bear']==0]))
removed=[c for c in base if (c['block'],c['low_t']) not in filt]
bear=[c for c in removed if c['macro_bear']==1]
displaced=[c for c in removed if c['macro_bear']!=1]
print(f"RETIRADOS: {len(removed)} = {len(bear)} BEAR bloqueado direto + {len(displaced)} deslocado (re-sequencia uma-posicao)")
print(f"\n--- {len(bear)} BEAR BLOQUEADOS (#N | data | R | win) ---")
print("  #N: "+", ".join(f"#{c['num']}" for c in bear))
for c in bear: print(f"  #{c['num']:<3} {d(c['t'])} R={c['R']:+.2f} {'W' if c['win'] else 'L'}")
print(f"  soma R BEAR removidos: {sum(c['R'] for c in bear):+.1f}  (W {sum(c['win'] for c in bear)}/L {sum(1-c['win'] for c in bear)})")
print(f"\n--- {len(displaced)} DESLOCADOS (nao-BEAR, sairam pela re-sequencia da vaga) (#N | regime | data | R) ---")
print("  #N: "+", ".join(f"#{c['num']}" for c in displaced))
for c in displaced: print(f"  #{c['num']:<3} {reg(c['t']):<7} {d(c['t'])} R={c['R']:+.2f} {'W' if c['win'] else 'L'}")
print(f"  soma R deslocados: {sum(c['R'] for c in displaced):+.1f}")
