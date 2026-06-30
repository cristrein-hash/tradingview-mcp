#!/usr/bin/env python3
"""AUDITORIA DURA dos extracts RAW antes da Fase 3a (Cris: já tivemos extracts errôneos; não validar sob dado distorcido).
(1) integridade OHLC 4H/1H (count, espaçamento modal, duplicatas, gaps anômalos vs fim-de-semana, sanidade h>=l>0, monotonia)
(2) schema RAW do 15M primitives (chaves, barra-exemplo, streams nas/smc/zones) p/ ler features de indicador corretamente.
Determinístico, só leitura."""
import json,datetime as dt
from collections import Counter
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
REV=ROOT/"my-strategy/research/revalidation"
def D(ts): return dt.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
def audit_ohlc(path,tf_sec,label):
    bars=[json.loads(l) for l in path.read_text().splitlines()]
    ts=[b["t"] for b in bars]
    print(f"\n=== {label} ({path.name}) ===")
    print(f"  N={len(bars)} | {D(ts[0])} -> {D(ts[-1])}")
    print(f"  monotônico crescente: {all(ts[i]<ts[i+1] for i in range(len(ts)-1))}")
    dups=[t for t,c in Counter(ts).items() if c>1]; print(f"  timestamps duplicados: {len(dups)}")
    deltas=Counter(ts[i+1]-ts[i] for i in range(len(ts)-1))
    print(f"  espaçamento esperado={tf_sec}s | top intervalos: {deltas.most_common(5)}")
    modal=deltas.most_common(1)[0][0]
    print(f"  intervalo modal={modal}s ({'OK' if modal==tf_sec else 'DIVERGE!'})")
    # gaps anômalos = não múltiplos do tf e não fim-de-semana (~2-3 dias)
    weekend=2*86400
    anom=[(D(ts[i]),(ts[i+1]-ts[i])//tf_sec) for i in range(len(ts)-1) if (ts[i+1]-ts[i])%tf_sec!=0 and (ts[i+1]-ts[i])<weekend]
    print(f"  gaps não-múltiplos-do-TF (intra-semana): {len(anom)}{' -> '+str(anom[:3]) if anom else ''}")
    bad=[b for b in bars if not(b['h']>=b['l'] and b['h']>=b['o'] and b['h']>=b['c'] and b['l']<=b['o'] and b['l']<=b['c'] and b['l']>0)]
    print(f"  barras OHLC inválidas (h>=l>=0, h>=o,c>=l): {len(bad)}{' -> '+str(bad[:2]) if bad else ''}")
    # densidade diária (barras/dia útil) sanity
    days=len(set(dt.datetime.utcfromtimestamp(t).date() for t in ts))
    print(f"  ~barras/dia: {len(bars)/days:.1f} (esperado ~{round(23*3600/tf_sec)} num dia cheio)")
audit_ohlc(REV/"raw_4h_ohlc.jsonl",14400,"OHLC 4H")
audit_ohlc(REV/"raw_1h_ohlc.jsonl",3600,"OHLC 1H")
# ---- schema 15M primitives ----
print("\n=== SCHEMA 15M primitives (1 arquivo) ===")
pf=sorted((ROOT/"research/xau_15m_bb_nas_leonardo/primitives").glob("*.primitives.json"))[0]
d=json.loads(pf.read_text())
print(f"  arquivo: {pf.name} | tipo raiz: {type(d).__name__}")
if isinstance(d,dict):
    print(f"  chaves raiz: {list(d.keys())}")
    for k,v in d.items():
        if isinstance(v,list): print(f"    {k}: list[{len(v)}] ex0={json.dumps(v[0])[:160] if v else '—'}")
        else: print(f"    {k}: {type(v).__name__} = {str(v)[:80]}")
elif isinstance(d,list):
    print(f"  list[{len(d)}] | ex0 chaves: {list(d[0].keys()) if d and isinstance(d[0],dict) else d[0]}")
    print(f"  ex0: {json.dumps(d[0])[:300]}")
