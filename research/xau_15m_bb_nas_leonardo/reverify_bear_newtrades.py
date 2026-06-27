#!/usr/bin/env python3
"""Esclarece o que sao os '17 trades novos' ao bloquear BEAR (Cris perguntou: nao pedi reentradas).
Compara taken da base h1_eff (211) vs h1_eff & macro!=BEAR (181). Mostra:
 - removidos (os BEAR bloqueados) com regime/R
 - novos (taken no 181 que nao estavam no 211) com regime/R/quando -> sao reentradas BEAR ou longs BULL/NEUTRAL liberados?
Tudo uma-posicao (dedup). RAW-causal."""
import json, bisect
from pathlib import Path
from filter_harness import ROWS, dedup, stats
HERE=Path(__file__).parent
MR=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MR.sort(key=lambda x:x["t_end"])
MEND=[b["t_end"] for b in MR]
def reg(t):
    k=bisect.bisect_right(MEND,t)-1; return MR[k]["macro"] if k>=0 else "WARMUP"
import datetime as dt
def d(t): return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")

base=dedup([r for r in ROWS if r['h1_eff'] is not None and r['h1_eff']>=0.15])
filt=dedup([r for r in ROWS if r['h1_eff'] is not None and r['h1_eff']>=0.15 and r['macro_bear']==0])
bid={(c['block'],c['low_t']):c for c in base}
fid={(c['block'],c['low_t']):c for c in filt}
removed=[bid[k] for k in bid if k not in fid]
newt=[fid[k] for k in fid if k not in bid]
print(f"BASE211: N={len(base)} | FILT181 (macro!=BEAR): N={len(filt)}")
print(f"\nREMOVIDOS (estavam no 211, sumiram no 181): {len(removed)}")
import collections
rc=collections.Counter(reg(c['t']) for c in removed)
print(f"  regime dos removidos: {dict(rc)}  | R soma removidos: {sum(c['R'] for c in removed):+.1f}")
print(f"\nTRADES NOVOS (no 181, nao estavam no 211): {len(newt)}")
nc=collections.Counter(reg(c['t']) for c in newt)
print(f"  regime dos novos: {dict(nc)}  | R soma novos: {sum(c['R'] for c in newt):+.1f}")
print(f"  -> ALGUM novo e BEAR? {'SIM (PROBLEMA)' if any(reg(c['t'])=='BEAR' for c in newt) else 'NAO — todos BULL/NEUTRAL (longs liberados pela vaga, nao reentrada BEAR)'}")
print("\n  detalhe dos novos (entrada | regime | R):")
for c in sorted(newt,key=lambda x:x['t']):
    print(f"    {d(c['t'])} | {reg(c['t']):<7} | R={c['R']:+.2f}")
# net honesto
print(f"\nNET: removeu {len(removed)} BEAR ({sum(c['R'] for c in removed):+.1f}R) + ganhou {len(newt)} longs BULL/NEUTRAL ({sum(c['R'] for c in newt):+.1f}R)")
print(f"     = mesma estrategia, uma-posicao, simplesmente NAO presa num long BEAR quando vem setup melhor.")
